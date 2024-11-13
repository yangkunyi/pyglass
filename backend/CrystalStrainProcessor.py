import py4DSTEM
import numpy as np
from py4DSTEM import show


class CrystalStrainProcessor:
    __slots__ = [
        "datacube",
        "_dp_mean",
        "_dp_max",
        "_radius_bf",
        "_guess_center",
        "_geometry_bf",
        "_geometry_adf",
        "_bf",
        "_adf",
        "_rx",
        "_ry",
        "_probe_xlims",
        "_probe_ylims",
        "_probe_ROI",
        "_probe",
        "_probe_semiangle",
        "_probe_qx0",
        "_probe_qy0",
        "_rxs",
        "_rys",
        "_colors",
        "_disk_detect_params",
        "_bragg_peaks",
        "_bvm_raw",
        "_bvm_vis_params",
        "_amorph_xlims",
        "_amorph_ylims",
        "_amorph_ROI",
        "_ellipse_fit_range",
        "_im_SAED_amorph",
        "_p_ellipse",
        "_p_dsg",
        "_strain_map",
        "_choose_basis_vector_params",
        "_fit_basis_vectors_params",
        "_get_strain_params",
    ]

    def load_data(self, file_path: str):
        self.datacube = py4DSTEM.import_file(filepath=file_path)

        self._dp_mean = self.datacube.get_dp_mean()
        self._dp_max = self.datacube.get_dp_max()
        self._radius_bf = None
        self._guess_center = None
        self._geometry_bf = None
        self._geometry_adf = None
        self._bf = None
        self._adf = None
        self._rx = None
        self._ry = None
        self._probe_xlims = None
        self._probe_ylims = None
        self._probe_ROI = None
        self._probe = None
        self._probe_semiangle = None
        self._probe_qx0 = None
        self._probe_qy0 = None
        self._rxs = None
        self._rys = None
        self._colors = [
            "deeppink",
            "coral",
            "gold",
            "chartreuse",
            "dodgerblue",
            "rebeccapurple",
        ]
        self._disk_detect_params = None
        self._bragg_peaks = None
        self._bvm_raw = None
        self._bvm_vis_params = {
            "scaling": "power",
            "power": 0.5,
            "intensity_range": "absolute",
            "vmin": 0,
            "vmax": 2e3,
        }
        self._amorph_xlims = None
        self._amorph_ylims = None
        self._amorph_ROI = None
        self._ellipse_fit_range = None

    def get_dp_image(self):
        fig = show(
            [self._dp_mean, self._dp_max],
            cmap="inferno",
            title=["mean DP", "max DP"],
            returnfig=True,
        )
        return fig[0]

    def set_guess_center(self, center: tuple):
        self._guess_center = center
        self._update_geometry_bf_adf()

    def set_radius_bf(self, radius: int):
        self._radius_bf = radius
        self._update_geometry_bf_adf()

    def _update_geometry_bf_adf(self):
        self._geometry_bf = (self._guess_center, self._radius_bf)
        self._geometry_adf = (self._guess_center, (self._radius_bf, 10e3))

    def get_position_detector_image(self):
        fig1 = self.datacube.position_detector(
            data=self._dp_max,
            mode="circle",
            geometry=self._geometry_bf,
            returnfig=True,
        )
        fig2 = self.datacube.position_detector(
            data=self._dp_max,
            mode="annulus",
            geometry=self._geometry_adf,
            returnfig=True,
        )
        return fig1[0], fig2[0]

    def calc_bf_adf(self):
        self._bf = self.datacube.get_virtual_image(
            mode="circle",
            geometry=self._geometry_bf,
            name="bright_field_cal",
        )
        self._adf = self.datacube.get_virtual_image(
            mode="annulus",
            geometry=self._geometry_adf,
            name="dark_field_cal",
        )

    def get_bf_image(self):
        fig = show([self._bf], bordercolor="w", cmap="gray", returnfig=True)
        return fig[0]

    def get_adf_image(self):
        fig = show([self._adf], bordercolor="w", cmap="gray", returnfig=True)
        return fig[0]

    def set_rx_ry(self, rx: int, ry: int):
        self._rx = rx
        self._ry = ry

    def get_selected_dp_image(self):
        fig = py4DSTEM.visualize.show_selected_dp(
            self.datacube, self._adf, self._rx, self._ry, returnfig=True
        )
        return fig[0]

    def set_probe_xlims_ylims(self, xlims: tuple, ylims: tuple):
        self._probe_xlims = xlims
        self._probe_ylims = ylims
        self._probe_ROI = np.zeros(self.datacube.rshape, dtype=bool)
        self._probe_ROI[
            self._probe_xlims[0] : self._probe_xlims[1],
            self._probe_ylims[0] : self._probe_ylims[1],
        ] = True

    def get_selected_zone_image(self):
        fig = show(
            self._adf,
            mask=self._probe_ROI,
            mask_color="r",
            mask_alpha=0.5,
            returnfig=True,
        )
        return fig[0]

    def set_probe(self):
        self._probe = self.datacube.get_vacuum_probe(ROI=self._probe_ROI)
        self._probe_semiangle, self._probe_qx0, self._probe_qy0 = (
            py4DSTEM.process.calibration.get_probe_size(self._probe.probe)
        )
        self._probe.get_kernel(
            mode="sigmoid",
            origin=(self._probe_qx0, self._probe_qy0),
            radii=(self._probe_semiangle * 1, self._probe_semiangle * 4),
        )

    def get_probe_image(self):
        fig = show(
            self._probe.probe,
            circle={
                "center": (self._probe_qx0, self._probe_qy0),
                "R": self._probe_semiangle,
            },
            vmin=0,
            vmax=1,
            returnfig=True,
        )
        return fig[0]

    def get_kernel_image(self):
        fig = py4DSTEM.visualize.show_kernel(
            self._probe.kernel,
            R=30,
            L=30,
            W=1,
            returnfig=True,
        )
        return fig[0]

    def set_rxs_rys(self, rxs: list, rys: list):
        self._rxs = rxs
        self._rys = rys

    def get_points_image(self):
        fig = py4DSTEM.visualize.show_points(
            self._adf,
            x=self._rxs,
            y=self._rys,
            pointcolor=self._colors,
            returnfig=True,
        )
        return fig[0]

    def get_origin_grid_image(self):
        fig = py4DSTEM.visualize.show_image_grid(
            get_ar=lambda i: self.datacube.data[self._rxs[i], self._rys[i], :, :],
            H=2,
            W=3,
            scaling="log",
            vmin=0,
            vmax=1,
            get_bordercolor=lambda i: self._colors[i],
            returnfig=True,
        )
        return fig[0]

    def set_disk_detect_params(self, params: dict):
        self._disk_detect_params = params

    def get_selected_bragg_disks_image(self):
        disks_selected = self.datacube.find_Bragg_disks(
            data=(self._rxs, self._rys),
            template=self._probe.kernel,
            **self._disk_detect_params,
        )

        fig = py4DSTEM.visualize.show_image_grid(
            get_ar=lambda i: self.datacube.data[self._rxs[i], self._rys[i], :, :],
            H=2,
            W=3,
            scaling="log",
            vmin=0,
            vmax=1,
            get_bordercolor=lambda i: self._colors[i],
            get_x=lambda i: disks_selected[i].data["qx"],
            get_y=lambda i: disks_selected[i].data["qy"],
            get_pointcolors=lambda i: self._colors[i],
            open_circles=True,
            scale=700,
            returnfig=True,
        )
        return fig[0]

    def calc_all_bragg_disks(self):
        self._bragg_peaks = self.datacube.find_Bragg_disks(
            template=self._probe.kernel,
            **self._disk_detect_params,
        )

    def calc_raw_bvm(self):
        self._bvm_raw = self._bragg_peaks.histogram(mode="raw")

    def get_raw_bvm_image(self):
        fig = show(
            self._bvm_raw,
            returnfig=True,
            **self._bvm_vis_params,
        )
        return fig[0]

    def get_raw_bvm_with_center_image(self):
        fig = show(
            self._bvm_raw,
            points={"x": self._guess_center[0], "y": self._guess_center[1]},
            returnfig=True,
            **self.bvm_vis_params,
        )
        return fig[0]

    def calc_origins_fit(self):
        self._bragg_peaks.measure_origin(center_guess=self._guess_center)
        return self._bragg_peaks.fit_origin(returnfig=True)

    def get_centered_bvm_image(self):
        bvm_centered = self._bragg_peaks.histogram()
        fig = show(
            bvm_centered,
            points={"x": self._guess_center[0], "y": self._guess_center[1]},
            returnfig=True,
            **self.bvm_vis_params,
        )
        return fig[0]

    def set_amorph_xlims_ylims(self, xlims: tuple, ylims: tuple):
        self._amorph_xlims = xlims
        self._amorph_ylims = ylims
        self._amorph_ROI = np.zeros(self.datacube.rshape, dtype=bool)
        self._amorph_ROI[
            self._amorph_xlims[0] : self._amorph_xlims[1],
            self._amorph_ylims[0] : self._amorph_ylims[1],
        ] = True

    def get_selected_amorph_zone_image(self):
        fig = show(
            self._adf,
            mask=self._amorph_ROI,
            mask_color="r",
            mask_alpha=0.5,
            returnfig=True,
        )
        return fig[0]

    def get_selected_amorph_zone_diffracion_image(self):
        im_SAED_amorph = self.datacube.get_virtual_diffraction(
            "mean", mask=self._amorph_ROI, shift_center=True
        )

        fig = show(
            im_SAED_amorph, intensity_range="absolute", scaling="log", returnfig=True
        )

        self._im_SAED_amorph = im_SAED_amorph
        return fig[0]

    def set_ellipse_fit_range(self, range: tuple):
        self._ellipse_fit_range = range

    def calc_fit_ellipse_amorphous_ring(self):
        self._p_ellipse, self._p_dsg = (
            py4DSTEM.process.calibration.fit_ellipse_amorphous_ring(
                data=self._im_SAED_amorph.data,
                center=self._im_SAED_amorph.calibration.get_origin_mean(),
                fitradii=self._ellipse_fit_range,
            )
        )
        self._bragg_peaks.calibration.set_p_ellipse(self._p_ellipse)
        self._bragg_peaks.setcal()

    def get_fit_ellipse_amorphous_ring_image(self):
        fig = py4DSTEM.visualize.show_amorphous_ring_fit(
            self._im_SAED_amorph.data,
            fitradii=self._ellipse_fit_range,
            p_dsg=self._p_dsg,
            returnfig=True,
        )
        return fig[0]

    def get_ellipse_bvm_image(self):
        bvm_ellipse = self._bragg_peaks.histogram(mode="cal")
        fig = show(
            bvm_ellipse,
            returnfig=True,
            **self.bvm_vis_params,
        )
        return fig[0]

    def calc_strain_map(self):
        self._strain_map = py4DSTEM.StrainMap(braggvectors=self._bragg_peaks)

    def set_choose_basis_vector_params(self, params: dict):
        self._choose_basis_vector_params = params

    def get_basis_vector_image(self):
        fig = self._strain_map.choose_basis_vectors(
            vis_params=self._bvm_vis_params, returnfig=True, **self._basis_vector_params
        )
        return fig[0]

    def set_fit_basis_vectors_params(self, params: dict):
        self._fit_basis_vectors_params = params

    def calc_fit_basis_vectors(self):
        self._strain_map.fit_basis_vectors(**self._fit_basis_vectors_params)

    def set_get_strain_params(self, params: dict):
        self._get_strain_params = params

    def get_strain_image(self):
        fig = self._strain_map.get_strain_map(**self._get_strain_params, returnfig=True)
        return fig[0]
