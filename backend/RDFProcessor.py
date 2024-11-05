import numpy as np

from utils import (
    get_scattering_factor_function,
    radial_profile,
    fit_leastsq,
    calculate_phi,
    fit_polynomial,
    cut_at_zero,
    calculate_pdf,
)


class RDFProcessor:
    def __init__(self):
        self.elements = []
        self.img = None
        self.q_per_pixel = 0.036
        self.start_index = 0
        self.end_index = 100
        self.fit_threshold = 0.9
        self.r_min = 0.0
        self.r_max = 10.0
        self.element_data = None
        self.scattering_factor = None
        self.scattering_factor_sq = None

    def set_image(self, img):
        self.img = img
        polar_image, _ = radial_profile(self.img)
        self.polar_img = polar_image

    def get_image(self):
        return self.img

    def get_polar_image(self):
        return self.polar_img

    def set_parameters(
        self, q_per_pixel, start_index, end_index, fit_threshold, r_min, r_max
    ):
        self.q_per_pixel = np.float64(q_per_pixel)
        self.start_index = np.int64(start_index)
        self.end_index = np.int64(end_index)
        self.fit_threshold = np.float64(fit_threshold)
        self.r_min = np.float64(r_min)
        self.r_max = np.float64(r_max)

    def set_element_data(self, element_data):
        self.element_data = element_data

    def set_scattering_factor_function(self):
        self.scattering_factor_function, self.scattering_factor_function_sq = (
            get_scattering_factor_function(self.element_data)
        )

    def process(self):
        if self.img is None or self.element_data is None:
            raise ValueError("Image and element data must be set before processing")

        polar_image, radial_mean = radial_profile(self.img)
        s = self.q_per_pixel * np.arange(len(radial_mean)) / np.sqrt(2)

        range_indices = np.arange(self.start_index, self.end_index)
        part_s = s[range_indices]
        part_radial_mean = radial_mean[range_indices]

        self.scattering_factor, self.scattering_factor_sq = (
            self._calculate_scattering_factor(part_s)
        )

        N_fit = fit_leastsq(
            part_radial_mean, self.scattering_factor_sq, self.fit_threshold
        )
        background = N_fit * self.scattering_factor
        phi = calculate_phi(
            part_s,
            part_radial_mean,
            N_fit,
            self.scattering_factor,
            self.scattering_factor_sq,
        )
        y_fit = fit_polynomial(part_s, phi)

        indices = cut_at_zero(y_fit)
        ind_s = part_s[indices]
        ind_phi = phi[indices]
        ind_y_fit = y_fit[indices]
        ind_modified_phi = ind_phi - ind_y_fit

        step = (self.r_max - self.r_min) / 600
        r_ranges = np.arange(self.r_min, self.r_max, step)
        pdf = calculate_pdf(ind_s, ind_modified_phi, r_ranges)

        return {
            "s": part_s.tolist(),
            "radial_mean": part_radial_mean.tolist(),
            "scattering_factor": self.scattering_factor.tolist(),
            "background": background.tolist(),
            "phi": phi.tolist(),
            "y_fit": y_fit.tolist(),
            "ind_s": ind_s.tolist(),
            "ind_modified_phi": ind_modified_phi.tolist(),
            "r_ranges": r_ranges.tolist(),
            "pdf": pdf,
        }

    def _calculate_scattering_factor(self, part_s):
        scattering_factor = self.scattering_factor_function(part_s**2)
        scattering_factor_sq = self.scattering_factor_function_sq(part_s**2)
        return scattering_factor, scattering_factor_sq


RDF_Processor = RDFProcessor()
