from orix.quaternion.rotation import Rotation
from orix.vector.vector3d import Vector3d
import numpy as np
import hyperspy.api as hs
from orix.plot import IPFColorKeyTSL
from pyxem.utils import indexation_utils as iutls
from pyxem.utils import plotting_utils as putls
from pyxem.utils.diffraction import find_beam_center_blur
from pyxem.utils.polar_transform_utils import get_template_cartesian_coordinates
from orix.quaternion import symmetry

def get_template_coordinates(pattern, simulation, in_plane_angle, mirrored_template, size_factor=1):
        c_x, c_y = find_beam_center_blur(pattern, 1)
        x, y, intensities = get_template_cartesian_coordinates(
            simulation,
            center=(c_x, c_y),
            in_plane_angle=in_plane_angle,
            window_size=(pattern.shape[1], pattern.shape[0]),
            mirrored=mirrored_template,
        )
        y = pattern.shape[0] - y
        return x, y, np.sqrt(intensities) * size_factor

class XemACOMViewer:
    def load_data(self, data:np.ndarray):
        self.dp = hs.signals.Signal2D(data)
        self.dp.set_signal_type("electron_diffraction")
        self.dp.center_direct_beam(method="blur", half_square_width=50, sigma=1.5)
        self.dp.data -= self.dp.data.min()
        self.dp.data *= 1 / self.dp.data.max()
        
    def set_pixel_size(self, pixel_size):
        self.dp.set_diffraction_calibration(pixel_size)
        
    def set_symmetry(self, symmetry_name):
        symmetry_dict = {
            "Oh": symmetry.Oh,
            "Th": symmetry.Th,
            "D6h": symmetry.D6h,
            "C6h": symmetry.C6h,
            "D4h": symmetry.D4h,
            "C4h": symmetry.C4h,
            "D3d": symmetry.D3d,
            "S6": symmetry.S6,
            "D2h": symmetry.D2h,
            "C2h": symmetry.C2h,            
            "Ci": symmetry.Ci,
        }
        for name in self.xmap.phases.names:
            self.xmap.phases[name].point_group = symmetry_dict[symmetry_name]
        self.symmetry = self.xmap.phases[0].point_group
        
    def load_simulations(self, simulations):
        self.simulations = simulations

    def load_matching_results(self, result, phase_dict):
        self.result = result
        self.phase_dict = phase_dict
        self.xmap = iutls.results_dict_to_crystal_map(result, phase_dict)

        
    def get_ipf(self, direction, threshold=0.012, phase=None):
        if direction == "x":
            direction = Vector3d.xvector()
        elif direction == "y":
            direction = Vector3d.yvector()
        elif direction == "z":
            direction = Vector3d.zvector()
        else:
            raise ValueError("direction must be x, y or z")
        
        if phase is None:
            phase = self.xmap.phases.names[0]
        phase_id = self.xmap.phases.id_from_name(phase)
        
        ckey = IPFColorKeyTSL(self.symmetry, direction=direction)
        
        rgb_all = np.zeros((self.xmap.size, 3))
        rgb = ckey.orientation2color(self.xmap[phase].orientations)
        rgb_all[self.xmap.phase_id == phase_id] = rgb
        
        mask = self.xmap.correlation[:,0] > (self.xmap.correlation[:,0].max()*threshold)
        mask = mask[:, np.newaxis]
        
        return np.reshape(rgb_all * mask, (self.dp.data.shape[0], self.dp.data.shape[1], 3))
    
    def get_template_over_pattern(self, px, py, n_sol = 0):
        sim_sol_index = self.result["template_index"][py, px, n_sol]
        mirrored_sol = self.result["mirrored_template"][py, px, n_sol]
        in_plane_angle = self.result["orientation"][py, px, n_sol, 0] #! NOTE: the first angle is the in plane angle!
        # query the appropriate template
        sim_sol = self.simulations[sim_sol_index]
        
        x, y, intensity = get_template_coordinates(self.dp.inav[px, py].data, sim_sol, in_plane_angle, mirrored_sol)
        return self.dp.inav[px, py].data, x, y, intensity
    
    def get_orientation_pos(self, px, py, n_sol = 0, direction = "z"):
        if direction == "x":
            direction = Vector3d.xvector()
        elif direction == "y":
            direction = Vector3d.yvector()
        elif direction == "z":
            direction = Vector3d.zvector()
        else:
            raise ValueError("direction must be x, y or z")
        
        orientation = self.result["orientation"][py, px, n_sol]
        solution_vectors = Rotation.from_euler(np.deg2rad(orientation))*direction
        
        return solution_vectors.in_fundamental_sector(self.symmetry)
    
    def get_legend(self):
        from orix.plot.direction_color_keys import DirectionColorKeyTSL
        d = DirectionColorKeyTSL(self.symmetry)
        return d._create_rgba_grid()[:,:,:3]
        
        