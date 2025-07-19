#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

# coord_worker.py

import os
import numpy as np
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal
from main_helpers import ACTIVITY_COORDS, ACTIVITY_FILES, load_activities, filter_coords

ACTIVITIES = "activities"
FIT_EXT = ".fit"

class CoordMode(Enum):
    REGENERATE = "regenerate"
    MERGE = "merge"

class CoordWorker(QObject):

    finished = pyqtSignal(np.ndarray, name='finished')
    progress = pyqtSignal(str, name='progress')

    def __init__(self, mode: CoordMode, files=None, existing_coords=None):

        super().__init__()

        self.mode = mode
        self.files = files
        self.existing_coords = existing_coords

    def run(self):

        if self.mode == CoordMode.REGENERATE:

            self.progress.emit('<b>Regenerating Activities</b><br><br>')

            self.progress.emit('Saving File List<br>')
            files = {f for f in os.listdir(ACTIVITIES) if f.lower().endswith(FIT_EXT)}
            with open(ACTIVITY_FILES, "w") as f:
                for fname in sorted(files):
                    f.write(f"{fname}\n")
            self.progress.emit('Saving File List - Done<br><br>')

            self.progress.emit('Loading Activities<br>')
            coords = load_activities(files)
            self.progress.emit('Loading Activities - Done<br><br>')

            self.progress.emit('Filtering Coords<br>')
            coords = filter_coords(coords, min_distance=100, signal=self.progress)
            self.progress.emit('Filtering Coords - Done<br><br>')

        elif self.mode == CoordMode.MERGE:

            self.progress.emit('<b>Merging New Activities</b><br><br>')

            self.progress.emit('Loading Activities<br>')
            coords = load_activities(self.files)
            self.progress.emit('Loading Activities - Done<br><br>')

            self.progress.emit('Filtering Coords<br>')
            coords = filter_coords(coords, filtered=self.existing_coords.tolist(), min_distance=100, signal=self.progress)
            self.progress.emit('Filtering Coords - Done<br><br>')

        else:

            coords = np.empty((0, 2))

        self.progress.emit('Saving Coords<br>')
        np.save(ACTIVITY_COORDS, coords)
        self.progress.emit('Saving Coords - Done<br><br>')

        self.finished.emit(coords)
