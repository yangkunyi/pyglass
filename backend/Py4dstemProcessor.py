import py4DSTEM


class Py4dstemProcessor:
    def __init__(self):
        pass

    def load_data(self, raw_data, x_range, y_range):
        self.x_range = x_range
        self.y_range = y_range
        self.data_cube = py4DSTEM.DataCube(data=raw_data)
        self.dp_mean = self.data_cube.get_dp_mean().data
        self.dp_max = self.data_cube.get_dp_max().data
        self.probe_semiangle, probe_x, probe_y = self.data_cube.get_probe_size(
            self.data_cube.tree("dp_mean").data,
        )
        self.probe_center = (probe_x, probe_y)
        self.probe_radius_range = (self.probe_semiangle * 3, self.probe_semiangle * 6)
        self.adf = self.data_cube.get_virtual_image(
            mode="annulus",
            geometry=(self.probe_center, self.probe_radius_range),
            name="dark_field",
        ).data

    def set_probe(self):
        self.probe = py4DSTEM.Probe.generate_synthetic_probe(
            radius=self.probe_semiangle, width=0.7, Qshape=self.data_cube.Qshape
        )
        self.probe.get_kernel(
            mode="sigmoid",
            origin=(self.data_cube.Qshape[0] / 2, self.data_cube.Qshape[0] / 2),
            radii=(self.probe_semiangle * 1.2, self.probe_semiangle * 4),
        )

    def get_adf(self):
        return self.adf

    def _find_bragg_disks_helper(self, index):
        y = index // self.x_range
        x = index % self.x_range

        disk_detection_parameter_map = {
            "minAbsoluteIntensity": 0,
            "minRelativeIntensity": 0.00000001,
            "minPeakSpacing": 0,
            "edgeBoundary": 20,
            "sigma": 0,
            "maxNumPeaks": 100,
            "subpixel": "poly",
            "corrPower": 1.0,
            "CUDA": False,
        }

        disk_detection_check_result = self.data_cube.find_Bragg_disks(
            data=([x], [y]), template=self.probe.kernel, **disk_detection_parameter_map
        )
        print(x, y)
        return disk_detection_check_result[0].data


Py4dstem_Processor = Py4dstemProcessor()
