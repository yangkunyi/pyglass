import base64

import cv2
from flask import Flask
from flask_socketio import SocketIO, emit, Namespace
import numpy as np
from engineio.async_drivers import gevent
from loguru import logger
from scipy.ndimage import zoom
from time import time
import json

from DM4Processor import DM4_Processor
from ImageProcessor import ImageProcessor
from RDFProcessor import RDFProcessor
from CenterCalibrationProcessor import CenCal
from engineio.async_drivers import gevent

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:9300")


def hex_to_bgr(hex_color):
    """
    将16进制颜色转换为BGR格式
    :param hex_color: 16进制颜色字符串（例如：'#FF0000'）
    :return: BGR格式的颜色元组
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)  # OpenCV使用BGR格式


def add_border_to_grayscale(grayscale_image, border_color_hex, border_width=1):
    """
    在灰度图像内部添加指定颜色的边框
    :param grayscale_image: 二维NumPy数组，范围0-1，表示灰度图
    :param border_color_hex: 16进制颜色字符串（例如：'#FF0000'）
    :param border_width: 边框宽度（默认为10）
    :return: 带有边框的灰度图像，范围0-1
    """
    # 确保输入图像范围在0-1之间
    if grayscale_image.min() < 0 or grayscale_image.max() > 1:
        raise ValueError("灰度图像的范围必须在0-1之间")

    # 获取图像的尺寸
    height, width = grayscale_image.shape

    # 将灰度图像转换为BGR格式
    grayscale_image_8bit = (grayscale_image * 255).astype(np.uint8)
    bgr_image = cv2.cvtColor(grayscale_image_8bit, cv2.COLOR_GRAY2BGR)

    # 将16进制颜色转换为BGR格式
    border_color_bgr = hex_to_bgr(border_color_hex)

    # 创建带有边框的区域
    bgr_image_with_border = bgr_image.copy()
    bgr_image_with_border[:border_width, :] = border_color_bgr  # 上边框
    bgr_image_with_border[-border_width:, :] = border_color_bgr  # 下边框
    bgr_image_with_border[:, :border_width] = border_color_bgr  # 左边框
    bgr_image_with_border[:, -border_width:] = border_color_bgr  # 右边框

    return bgr_image_with_border.astype(np.float32) / 255.0


def get_mask_from_selection(
    selection: dict, original_shape: tuple, scaled_shape: tuple
):
    x = int(selection["attrs"]["x"] / scaled_shape[1] * original_shape[1])
    y = int(selection["attrs"]["y"] / scaled_shape[0] * original_shape[0])
    if selection["className"] == "Rect":
        logger.info(selection["className"])
        width = int(selection["attrs"]["width"] / scaled_shape[1] * original_shape[1])
        height = int(selection["attrs"]["height"] / scaled_shape[0] * original_shape[0])
        mask = np.zeros(original_shape, dtype=np.bool_)
        mask[y : y + height, x : x + width] = 1
        return mask
    elif selection["className"] == "Circle":
        mask = np.zeros(original_shape, dtype=np.bool_)
        mask[y, x] = 1
        return mask


def resize_mask(large_mask, original_shape):
    """
    将放大后的二值mask缩回到原始尺寸。

    参数:
    large_mask (numpy.ndarray): 放大后的二值mask。
    original_shape (tuple): 原始mask的尺寸。

    返回:
    numpy.ndarray: 缩回到原始尺寸的二值mask。
    """
    # 计算缩放因子
    zoom_factor = tuple([o / l for o, l in zip(original_shape, large_mask.shape)])

    # 使用scipy.ndimage.zoom进行缩放
    small_mask = zoom(large_mask, zoom_factor, order=0)

    return small_mask


def calculate_average_intensity(gray_images, mask):
    """
    计算每张灰度图在选定像素上的平均强度，并形成一个128x128的强度数组。

    参数:
    gray_images (numpy.ndarray): 形状为 (128, 128, 256, 256) 的灰度图数组。
    mask (numpy.ndarray): 形状为 (256, 256) 的mask数组。

    返回:
    numpy.ndarray: 形状为 (128, 128) 的强度数组。
    """
    # 将mask扩展到与gray_images相同的维度
    mask_expanded = np.broadcast_to(mask, gray_images.shape)
    print(mask_expanded.shape)
    # 选择选定像素
    t1 = time()
    selected_pixels = gray_images[mask_expanded == 1]

    # 将选定像素重塑为 (128, 128, -1)
    selected_pixels_reshaped = selected_pixels.reshape(
        gray_images.shape[0], gray_images.shape[1], -1
    )

    # 计算每张灰度图的平均值
    intensity_array = np.mean(selected_pixels_reshaped, axis=2)
    t2 = time()
    print("Time taken to calculate average intensity:", t2 - t1)
    return intensity_array


def convert_to_base64(img: np.ndarray) -> str:
    img = (img * 255).astype(np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    image_base64 = base64.b64encode(buffer).decode("utf-8")
    return image_base64


def image_response(img: np.ndarray, id=None, id2=None, event_name: str = None):
    ### Convert float image in range 0-1 to uint8 and encode to base64
    img = (img * 255).astype(np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    image_base64 = base64.b64encode(buffer).decode("utf-8")
    if event_name is not None:
        emit(event_name, {"image_data": image_base64})
    if id is None:
        emit("image_response", {"image_data": image_base64})
    else:
        emit("image_response", {"image_data": image_base64, "id": id, "id2": id2})


class ViewerNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.right_processer = ImageProcessor()
        self.left_processer = ImageProcessor()

    def on_connect(self):
        print("Client connected: ViwerNamespace")

    def on_disconnect(self):
        print("Client disconnected: ViwerNamespace")

    def on_upload_dm4(self, file_path):
        print(file_path)
        DM4_Processor.load_file(file_path)
        shape = DM4_Processor.get_shape()
        self.bin_mask_shape = shape[:2]
        self.virtual_mask_shape = shape[2:]
        index_range = shape[0] * shape[1]
        emit(
            "file_name_response",
            {"success": True, "index_range": index_range},
        )

    def on_update_bin_mask(self, data):
        print("update bin mask")
        selections = [json.loads(s) for s in data["all_selections"]]

        img_series = []
        for s in selections:
            bin_mask = get_mask_from_selection(
                s, self.bin_mask_shape, (data["height"], data["width"])
            )
            bin_img = DM4_Processor.raw_data[bin_mask].mean(axis=0)
            self.right_processer.load_img(bin_img)
            img = self.right_processer.get_img()
            border_img = add_border_to_grayscale(
                img, border_color_hex=s["attrs"]["stroke"]
            )
            img_base64 = convert_to_base64(border_img)
            img_series.append(img_base64)
        if img_series == []:
            emit("image_series_response", {"image_series": []})
        emit("right_image_response", {"image_data": img_series[-1]})
        emit("image_series_response", {"image_series": img_series[::-1][1:]})

    def on_update_virtual_mask(self, data):
        print("update virtual mask")
        virtual_mask = resize_mask(
            np.array(data["mask"]), self.virtual_mask_shape
        ).astype(np.bool_)
        if virtual_mask.sum() == 0:
            virtual_mask = np.ones(self.virtual_mask_shape, dtype=np.bool_)
        print("virtual mask shape:", virtual_mask.shape)
        print("virtual mask:", virtual_mask.sum())
        virtual_img = calculate_average_intensity(DM4_Processor.raw_data, virtual_mask)
        self.left_processer.load_img(virtual_img)
        image_response(self.left_processer.get_img(), event_name="left_image_response")

    def on_set_index(self, data):
        # logger.info(f"set index: {data}")
        index = int(data["index"])
        img = DM4_Processor.get_img(index)
        self.right_processer.load_img(img)
        image_response(
            self.right_processer.get_img(), event_name="right_image_response"
        )

    def on_request_image(self, data):
        if data["side"] == "left":
            image_response(
                self.left_processer.get_img(), event_name="left_image_response"
            )
        elif data["side"] == "right":
            image_response(
                self.right_processer.get_img(), event_name="right_image_response"
            )

    def on_update_adjust_params(self, data):
        logger.info(f"on_update_adjust_params: {data}")
        gamma = data["gamma"]
        contrast = data["contrast"]
        brightness = data["brightness"]
        log_scale = data["log_scale"]
        side = data["side"]
        if side == "left":
            self.left_processer.updata_params(gamma, contrast, brightness, log_scale)
        elif side == "right":
            self.right_processer.updata_params(gamma, contrast, brightness, log_scale)


class RDFNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.image_processer = ImageProcessor()
        self.rdf_processor = RDFProcessor()

    def on_connect(self):
        print("Client connected: RDFNamespace")

    def on_disconnect(self):
        print("Client disconnected: RDFNamespace")

    def on_load_image_rdf(self, data):
        print("rdf namespace load image")
        self.rdf_processor.set_image(DM4_Processor.get_mean_img())

    def on_update_adjust_params(self, data):
        # print("update adjust params")
        gamma = data["gamma"]
        contrast = data["contrast"]
        brightness = data["brightness"]
        self.image_processer.updata_params(gamma, contrast, brightness)

    def on_select_elements(self, data):
        logger.debug("select elements")
        self.rdf_processor.set_element_data(data)
        self.rdf_processor.set_scattering_factor_function()
        emit("success", {"success": True})

    def on_update_rdf_params(self, data):
        self.rdf_processor.set_parameters(
            data["qPerPixel"],
            data["startIndex"],
            data["endIndex"],
            data["fitThreshold"],
            data["rMin"],
            data["rMax"],
        )
        result = self.rdf_processor.process()
        emit("rdf_result_response", result)

    def on_request_img_with_range(self, data):
        start_index = data["startIndex"]
        end_index = data["endIndex"]
        self.image_processer.load_img(self.rdf_processor.get_image())
        img = self.image_processer.get_img()

        # Convert image to color (if it's grayscale)
        img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # Get image center
        center = (img.shape[1] // 2, img.shape[0] // 2)

        # Draw circles
        cv2.circle(img_color, center, int(start_index / np.sqrt(2)), (0, 0, 1), 1)
        cv2.circle(img_color, center, int(end_index / np.sqrt(2)), (0, 0, 1), 1)

        image_response(img_color, "rdf_left")

    def on_request_polar_img_with_range(self, data):
        start_index = data["startIndex"]
        end_index = data["endIndex"]
        self.image_processer.load_img(self.rdf_processor.get_polar_image())
        img = self.image_processer.get_img()

        # Convert image to color (if it's grayscale)
        img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # Draw lines

        # Transpose the image to match the orientation in plot_utils.py
        img_color = cv2.transpose(img_color)
        img_color = cv2.flip(img_color, 0)

        cv2.line(
            img_color,
            (0, img_color.shape[0] - start_index),
            (img_color.shape[1] - 1, img_color.shape[0] - start_index),
            (0, 0, 1),
            2,
        )
        cv2.line(
            img_color,
            (0, img_color.shape[0] - end_index),
            (img_color.shape[1] - 1, img_color.shape[0] - end_index),
            (0, 0, 1),
            2,
        )

        image_response(img_color, "rdf_right")


class CenterCalibrationNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.image_processer = ImageProcessor()
        self.center_cal_processor = CenCal()

    def on_connect(self):
        print("Client connected: CenterCalibrationNamespace")

    def on_disconnect(self):
        print("Client disconnected: CenterCalibrationNamespace")

    def on_update_adjust_params(self, data):
        # print("update adjust params")
        gamma = data["gamma"]
        contrast = data["contrast"]
        brightness = data["brightness"]
        self.image_processer.updata_params(gamma, contrast, brightness)

    def on_request_image(self, index):
        index = int(index)
        img = DM4_Processor.get_img(index)

        self.image_processer.load_img(img)
        processed_img = self.image_processer.get_img()
        img_color = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
        center = (img.shape[1] // 2, img.shape[0] // 2)
        cv2.circle(img_color, center, 3, (0, 0, 1), -1)
        image_response(img_color, "center_calibration")

    def on_request_calibrated_image(self, data):
        index = int(data["index"])
        thres = float(data["threshold"])

        self.center_cal_processor.load_img(DM4_Processor.get_img(index))
        corrected_img = self.center_cal_processor.calibrate_center(thres)
        self.image_processer.load_img(corrected_img)
        processed_img = self.image_processer.get_img()
        img_color = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
        center = (processed_img.shape[1] // 2, processed_img.shape[0] // 2)
        cv2.circle(img_color, center, 3, (0, 0, 1), -1)
        image_response(img_color, "center_calibration", "after")

    def on_get_range(self):
        x_range, y_range = DM4_Processor.get_range()
        index_range = x_range * y_range
        print(index_range)
        emit(
            "get_range_response",
            {"success": True, "index_range": index_range},
        )


socketio.on_namespace(RDFNamespace("/rdf"))
socketio.on_namespace(ViewerNamespace("/viewer"))
socketio.on_namespace(CenterCalibrationNamespace("/center_calibration"))

if __name__ == "__main__":
    socketio.run(app, debug=False, host="127.0.0.1", port=5000)
