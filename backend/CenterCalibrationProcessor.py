import numpy as np
import cv2


def normalize(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def correct_center(img, center_x, center_y):
    height, width = img.shape[:2]  # 获取图像的高度和宽度
    dx = width // 2 - center_x  # 计算水平方向的平移量
    dy = height // 2 - center_y  # 计算垂直方向的平移量

    # 定义平移矩阵
    translation_matrix = np.float32([[1, 0, dx], [0, 1, dy]])

    # 使用 warpAffine 进行平移
    corrected_img = cv2.warpAffine(
        img,
        translation_matrix,
        (width, height),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=float(img.min()),
    )

    return corrected_img


def get_center(img, thres=0.7):
    data_max = np.max(img)
    data_min = np.min(img)
    data_thres = (data_max - data_min) * thres + data_min
    data_binary = (img >= data_thres).astype(np.float32)  # 二值化图像
    mass = np.sum(data_binary)
    center_x = np.sum(data_binary * np.arange(img.shape[1])) / mass
    center_y = np.sum(data_binary.T * np.arange(img.shape[0])) / mass
    return center_x, center_y


class CenCal:
    def __init__(self):
        pass

    def load_img(self, img):
        self.img = normalize(img)

    def calibrate_center(self, thres=0.7):
        center_x, center_y = get_center(self.img, thres)
        corrected_img = correct_center(self.img, center_x, center_y)
        return corrected_img


Cen_Cal_Processor = CenCal()
