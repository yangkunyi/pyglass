import pickle

import numpy as np
import polarTransform
from abtem.parametrizations import KirklandParametrization
from scipy.optimize import leastsq


def getPath(filename):
    import sys
    from os import chdir, environ
    from os.path import dirname, join

    if hasattr(sys, "_MEIPASS"):
        # PyInstaller >= 1.6
        chdir(sys._MEIPASS)
        filename = join(sys._MEIPASS, filename)
    elif "_MEIPASS2" in environ:
        # PyInstaller < 1.6 (tested on 1.5 only)
        chdir(environ["_MEIPASS2"])
        filename = join(environ["_MEIPASS2"], filename)
    else:
        chdir(dirname(sys.argv[0]))
        filename = join(dirname(sys.argv[0]), filename)

    return filename


def numba_get_center(img, thres=0.7):
    """
    根据阈值计算图像的质心作为中心点。

    参数：
        data (numpy.ndarray): 输入图像数据。
        thres (float, optional): 阈值比例，用于确定哪些像素点参与质心计算。默认为 0.5。
    """
    data_max = np.max(img)
    data_min = np.min(img)
    data_thres = (data_max - data_min) * thres + data_min
    data_binary = (img >= data_thres).astype(np.float32)  # 二值化图像
    mass = np.sum(data_binary)
    center_x = np.sum(data_binary * np.arange(img.shape[1])) / mass
    center_y = np.sum(data_binary.T * np.arange(img.shape[0])) / mass
    return center_x, center_y


def adjust_image(img, brightness_percent, contrast_percent):
    brightness_value = brightness_percent / 100.0 * (np.max(img) - np.min(img))
    contrast_factor = 1 + contrast_percent / 100.0
    adjusted_image = contrast_factor * img + brightness_value
    adjusted_image = np.clip(adjusted_image, np.min(img), np.max(img))
    return adjusted_image


def calculate_radial_mean(polar_image):
    return np.mean(polar_image, axis=0)


def fit_leastsq(intensity, scattering_factor_sq, threshold):
    data_length = len(intensity)
    start_index = int(data_length * threshold)
    intensity_last_20 = intensity[start_index:]
    scattering_factor_last_20 = scattering_factor_sq[start_index:]
    initial_guess = intensity.sum() / scattering_factor_sq.sum()

    def error_function(N, i, a):
        return i - N * a

    result, _ = leastsq(
        error_function,
        initial_guess,
        args=(intensity_last_20, scattering_factor_last_20),
    )
    return result[0]


def calculate_phi(s, radial_mean, N_fit, scattering_factor, scattering_factor_sq):
    return (
        (radial_mean - N_fit * scattering_factor_sq)
        / (N_fit * scattering_factor**2)
        * s
    )


def fit_polynomial(s, phi):
    coefficients = np.polyfit(s, phi, 4)
    polynomial = np.poly1d(coefficients)
    y_fit = polynomial(s)
    return y_fit


def cut_at_zero(y_fit):
    # 找到最后一个最接近0的值的索引
    last_zero_closest_index = np.abs(y_fit[::-1] - 0).argmin()
    last_zero_closest_index = len(y_fit) - 1 - last_zero_closest_index

    # 生成indices数组，包含从开始到最后一个最接近0的值的索引
    indices = np.arange(last_zero_closest_index + 1)

    return indices


def calculate_pdf(s, phi, r_ranges):
    return [np.sum(phi * np.sin(2 * np.pi * s * r)) for r in r_ranges]


def get_scattering_factor_function(element_data: list):
    with open("kirkland.pkl", "rb") as f:
        kirkland_dict = pickle.load(f)

    kirkland_param = KirklandParametrization(kirkland_dict)

    element_data_dict = {
        str(item["atomicNumber"]): item["percentage"] for item in element_data
    }
    functions = []
    for element, percentage in element_data_dict.items():
        functions.append((kirkland_param.scattering_factor(element), percentage / 100))

    def combined_function(x):
        return sum(f(x) * p for f, p in functions)

    def combined_function_sq(x):
        return sum(f(x) ** 2 * p for f, p in functions)

    return (combined_function, combined_function_sq)


def convert_to_polar(image, center):
    return polarTransform.convertToPolarImage(image, center=center)


def radial_profile(img):
    polar_image, _ = convert_to_polar(
        img, center=(img.shape[0] // 2, img.shape[1] // 2)
    )
    radial_mean = calculate_radial_mean(polar_image)

    return polar_image, radial_mean
