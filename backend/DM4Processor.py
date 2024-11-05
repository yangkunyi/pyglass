from ncempy.io import dm
import numpy as np
import os


def normalize(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


class DM4Processor:
    def __init__(self):
        self.raw_data = None

    def clear(self):
        pass

    def load_file(self, file_path, is_normalize=False):
        if os.path.splitext(file_path)[1] == ".dm4":
            dm4 = dm.dmReader(file_path)
            self.raw_data = dm4["data"]
            self.y_range = dm4["data"].shape[0]
            self.x_range = dm4["data"].shape[1]
        if os.path.splitext(file_path)[1] == ".npy":
            self.raw_data = np.load(file_path)
        if self.raw_data.ndim == 2:
            self.raw_data = self.raw_data.reshape(
                1, 1, self.raw_data.shape[0], self.raw_data.shape[1]
            )
        if self.raw_data.ndim == 3:
            x = y = int(np.sqrt(self.raw_data.shape[0]))
            self.raw_data = self.raw_data.reshape(
                x, y, self.raw_data.shape[1], self.raw_data.shape[2]
            )

        self.y_range = self.raw_data.shape[0]
        self.x_range = self.raw_data.shape[1]

        if is_normalize:
            self.raw_data = self.raw_data.astype(np.float64)
            self.raw_data = normalize(self.raw_data)

        self.mean_img = np.mean(self.raw_data, axis=(0, 1))

    def get_img(self, img_index):
        y = img_index // self.x_range
        x = img_index % self.x_range
        return self.raw_data[y, x]

    def get_mean_img(self):
        return self.mean_img

    def get_range(self):
        return self.y_range, self.x_range


DM4_Processor = DM4Processor()
