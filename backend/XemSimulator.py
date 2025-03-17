import matplotlib.pyplot as plt
import numpy as np
import diffpy.structure
import pyxem as pxm
import hyperspy.api as hs

from diffsims.libraries.structure_library import StructureLibrary
from diffsims.generators.diffraction_generator import DiffractionGenerator
from diffsims.generators.library_generator import DiffractionLibraryGenerator
from diffsims.generators.zap_map_generator import get_rotation_from_z_to_direction
from diffsims.generators.rotation_list_generators import get_grid_around_beam_direction

from pyxem.generators.indexation_generator import AcceleratedIndexationGenerator
from pyxem.utils.indexation_utils import results_dict_to_crystal_map

from diffsims.generators.rotation_list_generators import get_beam_directions_grid

import pickle

def grid_to_xy(grid):
    from orix.quaternion.rotation import Rotation
    from orix.vector.vector3d import Vector3d
    from orix.projections import StereographicProjection
    s = StereographicProjection(pole=-1)
    rotations_regular =  Rotation.from_euler(np.deg2rad(grid))
    rot_reg_test = rotations_regular*Vector3d.zvector()
    x, y = s.vector2xy(rot_reg_test)
    return x, y



class XemSimulator:
    def __init__(self):
        pass
    
    def load_structure(self, cif_path):
        self.structure = diffpy.structure.loadStructure(cif_path)
        
    def create_dif_gen_params(self, accelerating_voltage=300, min_intensity=0.005):
        diff_gen = DiffractionGenerator(accelerating_voltage=accelerating_voltage,
                                             minimum_intensity=min_intensity)
        self.lib_gen = DiffractionLibraryGenerator(diff_gen)
    
    def create_sample_grid(self, resolution = 2, crystal_system = "cubic"):
        self.grid = get_beam_directions_grid(crystal_system, resolution)
        self.grid_x, self.grid_y = grid_to_xy(self.grid)
        
        
    def set_sim_params(self, half_shape, pixel_size, max_excitation_error=0.1):
        self.half_shape = half_shape
        self.pixel_size = pixel_size
        self.max_excitation_error = max_excitation_error
        self.reciprocal_radius = np.sqrt(half_shape[0]**2 + half_shape[1]**2)*pixel_size
    
    def simulate(self):
        structure_library = StructureLibrary(["X"], [self.structure], [self.grid])
        self.diffraction_library = self.lib_gen.get_diffraction_library(
            structure_library=structure_library,
            calibration=self.pixel_size,
            reciprocal_radius=self.reciprocal_radius,
            half_shape=self.half_shape,
            max_excitation_error=self.max_excitation_error,
            with_direct_beam=False,
        )
        
        coords = []
        intensities = []
        
        for sim in self.diffraction_library['X']['simulations']:
            coord = sim._get_transformed_coordinates(angle=0)
            intensity = np.sqrt(sim.intensities)
            coords.append(coord.tolist())
            intensities.append(intensity.tolist())
            
        return coords, intensities
    
    def save_simulation(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.diffraction_library, f)
    
    def load_simulation(self, path):
        with open(path, "rb") as f:
            self.diffraction_library = pickle.load(f)
    