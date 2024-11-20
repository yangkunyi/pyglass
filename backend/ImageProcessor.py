import numpy as np


def normalize(data, log_scale=False):
    if log_scale:
        data = np.log(data - data.min() + 1)
    normalized_data = (data - np.min(data)) / (np.max(data) - np.min(data))
    return normalized_data


class ImageProcessor:
    def __init__(self):
        self.raw_img = None
        self.adjusted_img = None
        self.gamma = 1
        self.contrast = 1
        self.brightness = 0
        self.log_scale = False

    def load_img(self, img: np.ndarray):
        self.raw_img = img
        self.adjusted_img = None

    def updata_params(
        self, gamma: float, contrast: float, brightness: float, log_scale=False
    ):
        self.gamma = gamma
        self.contrast = contrast
        self.brightness = brightness
        self.log_scale = log_scale

    def adjust(self):
        if self.raw_img is None:
            raise ValueError("No image loaded.")
        self.adjusted_img = normalize(self.raw_img, log_scale=self.log_scale)

        # Gamma correction
        if self.gamma != 1:
            inv_gamma = 1.0 / self.gamma
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in range(256)]
            ).astype("uint8")
            image_255 = (self.adjusted_img * 255).astype(np.uint8)
            self.adjusted_img = table[image_255] / 255.0

        # Contrast and brightness adjustment
        self.adjusted_img = np.clip(
            self.contrast * self.adjusted_img + self.brightness, 0, 1
        )

    def get_img(self):
        self.adjust()
        return (
            (self.adjusted_img).astype(np.float32)
            if self.adjusted_img is not None
            else (self.raw_img).astype(np.float32)
        )


Image_Processor = ImageProcessor()
