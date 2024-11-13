import base64

import cv2
from flask import Flask
from flask_socketio import SocketIO, emit, Namespace
import numpy as np
from engineio.async_drivers import gevent
from loguru import logger

from DM4Processor import DM4_Processor
from ImageProcessor import ImageProcessor
from RDFProcessor import RDFProcessor
from CenterCalibrationProcessor import CenCal

app = Flask(__name__)
socketio = SocketIO(
    app, cors_allowed_origins="http://localhost:9300", async_mode="gevent"
)


def image_response(img: np.ndarray, id=None):
    ### Convert float image in range 0-1 to uint8 and encode to base64
    img = (img * 255).astype(np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    image_base64 = base64.b64encode(buffer).decode("utf-8")
    if id is None:
        emit("image_response", {"image_data": image_base64})
    else:
        emit("image_response", {"image_data": image_base64, "id": id})


class ViewerNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.image_processer = ImageProcessor()

    def on_connect(self):
        print("Client connected: ViwerNamespace")

    def on_disconnect(self):
        print("Client disconnected: ViwerNamespace")

    def on_upload_dm4(self, file_path):
        print(file_path)
        DM4_Processor.load_file(file_path)
        x_range, y_range = DM4_Processor.get_range()
        index_range = x_range * y_range
        emit(
            "file_name_response",
            {"success": True, "index_range": index_range},
        )
        # socketio.emit(
        #     "load_image_rdf", {"load": True}, include_self=True, namespace="/rdf"
        # )

    def on_request_image(self, index):
        index = int(index)
        img = DM4_Processor.get_img(index)
        self.image_processer.load_img(img)
        image_response(self.image_processer.get_img())

    def on_update_adjust_params(self, data):
        gamma = data["gamma"]
        contrast = data["contrast"]
        brightness = data["brightness"]
        self.image_processer.updata_params(gamma, contrast, brightness)


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

        self.center_cal_processor.load_img(DM4_Processor.get_image(index))
        corrected_img = self.center_cal_processor.calibrate_center(thres)
        self.image_processer.load_img(corrected_img)
        processed_img = self.image_processer.get_img()
        img_color = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
        center = (processed_img.shape[1] // 2, processed_img.shape[0] // 2)
        cv2.circle(img_color, center, 3, (0, 0, 1), -1)
        image_response(img_color, "center_calibration")


socketio.on_namespace(RDFNamespace("/rdf"))
socketio.on_namespace(ViewerNamespace("/viewer"))
socketio.on_namespace(CenterCalibrationNamespace("/center_calibration"))

if __name__ == "__main__":
    # print("!!!!!!")
    socketio.run(app, port=5000)
