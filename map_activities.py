#!python3.10

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


import glob
import io
from multiprocessing import Pool
import os
import sys
from time import time

import folium
from folium.plugins import HeatMap
import pandas as pd
import numpy as np

from garmin_fit_sdk import Decoder, Stream

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QPushButton, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

from utils_print import generate_a2_map


class MainWindow(QDialog):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Map Activities')

        # Button Box

        generate_map_button = QPushButton('Generate Map')
        generate_map_button.clicked.connect(self.generate_map)
        generate_map_button.setAutoDefault(False)
        generate_map_button.setDefault(False)

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttonBox.addButton(generate_map_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttonBox.accepted.connect(self.close)
        buttonBox.rejected.connect(self.close)

        # Web View

        self.web_engine_view = QWebEngineView()
        self.web_engine_view.setGeometry(0, 0, 1600, 1200)
        self.show_activities()

        # Layout

        layout = QVBoxLayout()
        layout.addWidget(self.web_engine_view)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        # Window Flags

        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)

    def show_activities(self):

        start = time()

        # Load Coords

        # self.coords = load_activities()
        self.coords = load_activities_multiprocessor()
        self.coords = np.unique(self.coords, axis=0)
        self.coords = self.coords * 180 / 2147483648

        print(f'Load time: {time() - start:.2f}')

        # Create Map

        lat_min, long_min  = self.coords.min(axis=0)
        lat_max, long_max = self.coords.max(axis=0)

        map = folium.Map(
            control_scale = True,
            max_zoom = 19,
            title = "Map Activities",
            zoom_snap = 0.1)
        map.fit_bounds([[lat_min, long_min], [lat_max, long_max]])
        map.add_child(HeatMap(self.coords.tolist(), name='Heat Map', radius=3, blur=4))

        folium.LayerControl(position='bottomleft').add_to(map)

        # Set HTML

        map_data = io.BytesIO()
        map.save(map_data, close_file=False)
        self.web_engine_view.setHtml(map_data.getvalue().decode())

        print(f'Display time: {time() - start:.2f}')

    def generate_map(self):

        generate_a2_map(self.coords)

def load_activity(path):

    stream = Stream.from_file(path)
    decoder = Decoder(stream)

    messages, errors = decoder.read(
            apply_scale_and_offset = False,
            convert_datetimes_to_dates = False,
            convert_types_to_strings = False,
            enable_crc_check = False,
            expand_sub_fields = False,
            expand_components = False,
            merge_heart_rates = False,
            mesg_listener = None)

    if len(errors) > 0:
        print(errors)

    if not 'record_mesgs' in messages:
        print('no "record_mesgs" in activity', path)
        return np.empty([0, 2], dtype=np.int32)

    coords = pd.DataFrame(messages['record_mesgs'])[['position_lat', 'position_long']].to_numpy()
    coords = coords[~np.isnan(coords).any(axis=1)]
    coords = np.round(coords, -3)

    return coords[::10]

def load_activities():

    activities_pattern = os.path.join('activities', '*.fit')
    activity_paths = glob.glob(activities_pattern)

    result = map(load_activity, activity_paths)

    return np.vstack(list(result))

def load_activities_multiprocessor():

    activities_pattern = os.path.join('activities', '*.fit')
    activity_paths = glob.glob(activities_pattern)

    pool = Pool(os.cpu_count() - 1)
    results = pool.map(load_activity, activity_paths)
    pool.close()
    pool.join()

    return np.vstack(results)

def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    return app.exec()

if __name__ == '__main__':

    sys.exit(main())
