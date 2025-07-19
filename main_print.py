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

import os
from datetime import datetime

import folium
from folium.plugins import HeatMap

def generate_a2_map(coords):

    # Bounds

    # lat_min, long_min = coords.min(axis=0)
    # lat_max, long_max = coords.max(axis=0)

    lat_min, long_min = 51.66, -8.99
    lat_max, long_max = 51.90, -7.95

    width, height = determine_orientation(lat_min, lat_max, long_min, long_max, scale_factor=20)

    # Map

    map = folium.Map(
        control_scale = False,
        title = "Activities",
        max_bounds = True,
        max_zoom = 19,
        zoom_control = False,
        zoom_snap = 0.1,
        width=width,
        height=height)
    map.fit_bounds([[lat_min, long_min], [lat_max, long_max]])
    map.add_child(HeatMap(coords.tolist(), name='Heat Map', radius=10, blur=10))

    # Finish

    add_header_and_footer(map, width, height, '', scale_factor=4)
    generate_png(map, 'activity-map')

    print('Done')

def determine_orientation(min_latitude, max_latitude, min_longitude, max_longitude, scale_factor=5):

    width=210*scale_factor
    height=297*scale_factor
    if min_latitude and max_latitude and min_longitude and max_longitude:
        if (max_longitude - min_longitude) > (max_latitude - min_latitude):
            width=297*scale_factor
            height=210*scale_factor

    return width, height

def add_header_and_footer(map, width, height, heading, scale_factor=1):

    font_size = 40 * scale_factor
    padding = 8 * scale_factor
    margin = 32 * scale_factor
    shadow = 1.25 * scale_factor

    footer_font_size = 8 * scale_factor
    footer_top = height - margin - footer_font_size
    footer_left = width-50*scale_factor

    title_html = f'''
        <h1
            style="
                font-family: Arial;
                font-size: {font_size}px;
                left: {margin}px;
                margins: 0px;
                padding: {padding}px {padding*2}px {padding}px {padding*2}px;
                position: fixed;
                text-align: center;
                text-shadow: {shadow}px {shadow}px Silver;
                top: {margin}px;
                white-space: nowrap;
                z-index: 999;">
            {heading}
        </h1>
        <p
            style="
                font-size: {footer_font_size}px;
                left: {footer_left}px;
                position: fixed;
                top: {footer_top}px;
                z-index: 999;">
            {datetime.now().strftime('%d/%m/%y')}
        </p>
    '''
    map.get_root().html.add_child(folium.Element(title_html))

def generate_png(map, name, prefix='', suffix=''):

    output_filename = os.path.join('generated', f'{prefix}{name}{suffix}.png')
    with open(output_filename, 'wb') as f:
        f.write(map._to_png())

    return output_filename
