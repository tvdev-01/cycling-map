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

# main.py

import io
import os
import sys
import numpy as np
import folium
from folium.plugins import HeatMap

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QPushButton, QVBoxLayout, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView

from coord_worker import CoordMode, CoordWorker
from main_helpers import ACTIVITY_COORDS, ACTIVITY_FILES, GENERATED, get_new_activity_files
from main_print import generate_a2_map

class MainWindow(QDialog):

    def __init__(self):

        super().__init__()

        self.coords = None

        self.setWindowTitle('Map Activities')

        # Buttons

        regen_btn = QPushButton('Regenerate')
        regen_btn.clicked.connect(lambda: self.run_async_task(CoordMode.REGENERATE))

        map_btn = QPushButton('Create Offline Map')
        map_btn.clicked.connect(self.create_offline_map)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.addButton(regen_btn, QDialogButtonBox.ButtonRole.ActionRole)
        button_box.addButton(map_btn, QDialogButtonBox.ButtonRole.ActionRole)
        button_box.rejected.connect(self.close)

        # Web view

        self.web_engine_view = QWebEngineView()
        self.web_engine_view.setGeometry(0, 0, 1600, 1200)
        self.web_engine_view.setMinimumSize(40, 30)

        layout = QVBoxLayout(self)
        layout.addWidget(self.web_engine_view)
        layout.addWidget(button_box)

        # Dialog window

        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)

        self.resize(800, 600)
        self.center_on_cursor_screen()

        # Show activities

        self.show_activities()

    def center_on_cursor_screen(self):

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()

        screen_geometry = screen.availableGeometry()
        size = self.size()

        x = screen_geometry.x() + (screen_geometry.width() - size.width()) // 2
        y = screen_geometry.y() + (screen_geometry.height() - size.height()) // 2

        self.move(x, y)

    def show_activities(self):

        if not os.path.isdir(GENERATED):
            os.mkdir(GENERATED)

        if not os.path.exists(ACTIVITY_COORDS) or not os.path.exists(ACTIVITY_FILES):
            self.run_async_task(CoordMode.REGENERATE)
        else:
            new_files = get_new_activity_files()
            if new_files:
                existing = np.load(ACTIVITY_COORDS)
                self.run_async_task(CoordMode.MERGE, files=new_files, existing_coords=existing)
            else:
                self.create_map(np.load(ACTIVITY_COORDS))

    def run_async_task(self, mode: CoordMode, files=None, existing_coords=None):

        self.progress_popup = QMessageBox(self)
        self.progress_popup.setWindowTitle("Please Wait")
        self.progress_popup.setText("Processing activity files...")
        self.progress_popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.progress_popup.show()

        self.thread = QThread()
        self.worker = CoordWorker(mode, files, existing_coords)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_processing_finished(self, coords):

        self.progress_popup.hide()
        self.progress_popup.deleteLater()

        if coords is None or len(coords) == 0:
            QMessageBox.information(self, "No Data", "No coordinates were processed.")
            return

        self.create_map(coords)

    def create_map(self, coords):

        if coords is None or len(coords) == 0:
            QMessageBox.warning(self, "No Data", "No valid coordinates to display.")
            return

        if np.isnan(coords).any():
            QMessageBox.warning(self, "Invalid Data", "Coordinate data contains NaNs.")
            return

        self.coords = coords

        lat_min, lon_min = coords.min(axis=0)
        lat_max, lon_max = coords.max(axis=0)

        folium_map = folium.Map(control_scale=True, max_zoom=19, zoom_snap=0.1)
        folium_map.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])
        folium_map.add_child(HeatMap(coords.tolist(), radius=3, blur=4))
        folium.LayerControl(position='bottomleft').add_to(folium_map)

        html_buffer = io.BytesIO()
        folium_map.save(html_buffer, close_file=False)
        self.web_engine_view.setHtml(html_buffer.getvalue().decode())

        self.resize(1600, 1200)
        self.center_on_cursor_screen()

    def create_offline_map(self):

        if self.coords is not None:
            from threading import Thread
            Thread(target=generate_a2_map, args=(self.coords,)).start()

def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
