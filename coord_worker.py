# coord_worker.py

import os
import numpy as np
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal
from main_helpers import load_activities, filter_coords

ACTIVITIES = "activities"
FIT_EXT = ".fit"

class CoordMode(Enum):
    REGENERATE = "regenerate"
    MERGE = "merge"

class CoordWorker(QObject):

    finished = pyqtSignal(np.ndarray, name='finished')

    def __init__(self, mode: CoordMode, files=None, existing_coords=None):

        super().__init__()

        self.mode = mode
        self.files = files
        self.existing_coords = existing_coords

    def run(self):

        if self.mode == CoordMode.REGENERATE:
            files = {f for f in os.listdir(ACTIVITIES) if f.lower().endswith(FIT_EXT)}
            coords = load_activities(files)
            coords = filter_coords(coords, min_distance=100)

        elif self.mode == CoordMode.MERGE:
            coords = load_activities(self.files)
            coords = filter_coords(coords, filtered=self.existing_coords.tolist(), min_distance=100)

        else:
            coords = np.empty((0, 2))

        self.finished.emit(coords)
