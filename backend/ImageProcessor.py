import numpy as np


def normalize(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


class ImageProcessor:
    def __init__(self):
        self.raw_img = None
        self.adjusted_img = None
        self.gamma = 1
        self.contrast = 1
        self.brightness = 0

    def load_img(self, img: np.ndarray):
        self.raw_img = normalize(img)
        self.adjusted_img = None

    def updata_params(self, gamma: float, contrast: float, brightness: float):
        self.gamma = gamma
        self.contrast = contrast
        self.brightness = brightness

    def adjust(self):
        if self.raw_img is None:
            raise ValueError("No image loaded.")

        self.adjusted_img = self.raw_img
        # Gamma correction
        if self.gamma != 1:
            inv_gamma = 1.0 / self.gamma
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in range(256)]
            ).astype("uint8")
            image_255 = (self.raw_img * 255).astype(np.uint8)
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
