import base64

import cv2
from flask import Flask
from flask_socketio import SocketIO, emit
import numpy as np

from DM4Processor import DM4_Processor
from ImageProcessor import Image_Processor
from RDFProcessor import RDF_Processor
from CenterCalibrationProcessor import Cen_Cal_Processor

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:9300")



def image_response(img: np.ndarray, id=None):
    ### Convert float image in range 0-1 to uint8 and encode to base64
    img = (img * 255).astype(np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    image_base64 = base64.b64encode(buffer).decode("utf-8")
    if id is None:
        emit("image_response", {"image_data": image_base64})
    else:
        emit("image_response", {"image_data": image_base64, "id": id})


@socketio.on("upload_dm4")
def handle_file_name(file_path):
    print(file_path)
    DM4_Processor.load_file(file_path)
    x_range, y_range = DM4_Processor.get_range()
    index_range = x_range * y_range
    RDF_Processor.set_image(DM4_Processor.get_mean_img())
    emit(
        "file_name_response",
        {"success": True, "index_range": index_range},
    )


@socketio.on("request_image")
def handle_get_image(index):
    index = int(index)
    img = DM4_Processor.get_img(index)
    Image_Processor.load_img(img)

    image_response(Image_Processor.get_img())


@socketio.on("update_adjust_params")
def handle_adjust_image(data):
    gamma = data["gamma"]
    contrast = data["contrast"]
    brightness = data["brightness"]
    Image_Processor.updata_params(gamma, contrast, brightness)


@socketio.on("selecte_elements")
def handle_selected_elements(data):
    RDF_Processor.set_element_data(data)
    RDF_Processor.set_scattering_factor_function()
    emit("success", {"success": True})


@socketio.on("update_rdf_params")
def handle_update_rdf_params(data):
    RDF_Processor.set_parameters(
        data["qPerPixel"],
        data["startIndex"],
        data["endIndex"],
        data["fitThreshold"],
        data["rMin"],
        data["rMax"],
    )
    result = RDF_Processor.process()
    emit("rdf_result_response", result)


@socketio.on("request_img_with_range")
def handle_request_img_with_range(data):
    start_index = data["startIndex"]
    end_index = data["endIndex"]
    Image_Processor.load_img(RDF_Processor.get_image())
    img = Image_Processor.get_img()

    # Convert image to color (if it's grayscale)
    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Get image center
    center = (img.shape[1] // 2, img.shape[0] // 2)

    # Draw circles
    cv2.circle(img_color, center, int(start_index / np.sqrt(2)), (0, 0, 1), 1)
    cv2.circle(img_color, center, int(end_index / np.sqrt(2)), (0, 0, 1), 1)

    image_response(img_color, "rdf_left")


@socketio.on("request_polar_img_with_range")
def handle_request_polar_img_with_range(data):
    start_index = data["startIndex"]
    end_index = data["endIndex"]
    Image_Processor.load_img(RDF_Processor.get_polar_image())
    img = Image_Processor.get_img()

    # Convert image to color (if it's grayscale)
    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Draw lines

    # Transpose the image to match the orientation in plot_utils.py
    img_color = cv2.transpose(img_color)
    img_color = cv2.flip(img_color, 0)  # Flip vertically to invert y-axis

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


@socketio.on("request_center_calibration")
def handle_request_center_calibration(data):
    index = int(data["index"])
    thres = float(data["threshold"])
    Cen_Cal_Processor.load_img(DM4_Processor.get_image(index))
    corrected_img = Cen_Cal_Processor.calibrate_center(thres)
    image_response(corrected_img, "center_calibration")


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
