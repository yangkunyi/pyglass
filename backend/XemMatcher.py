from diffsims.libraries.vector_library import load_VectorLibrary
from orix import plot
import pickle
from pathlib import Path
import numpy as np
import py4DSTEM
import hyperspy.api as hs

from pyxem.utils import indexation_utils as iutls
from pyxem.utils import polar_transform_utils as ptutls
from pyxem.utils import expt_utils as eutls


class XemMatcher:
    def load_simulations(self, simulations):
        self.simulations = simulations
        
    def load_data(self, dp):
        self.dp = dp
        
    def set_pixel_size(self, pixel_size):
        self.dp.set_diffraction_calibration(pixel_size)
    
    def do_matching(self):
        frac_keep = 0.5
        self.result, self.phasedict = iutls.index_dataset_with_template_rotation(
            self.dp, self.simulations,
            n_best=1,
            frac_keep=frac_keep,
            n_keep=None,
            delta_r=1,
            delta_theta=1,
            max_r=None,
            intensity_transform_function=None,
            normalize_images=True,
            normalize_templates=True,
        )
    
    def save_result(self, path):
        with open(path, "wb") as f:
            pickle.dump((self.result, self.phasedict), f)
    
    