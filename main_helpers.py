# main_helpers.py

import os
import math
import numpy as np
import pandas as pd
from multiprocessing import Pool
from garmin_fit_sdk import Stream, Decoder


ACTIVITIES = "activities"
GENERATED = "generated"

ACTIVITY_COORDS = os.path.join(GENERATED, "activity_coords.npy")
ACTIVITY_FILES =  os.path.join(GENERATED, "activity_files")

FIT_EXT = ".fit"
FIT_SCALE = 180 / 2147483648

EARTH_RADIUS_M = 6371000

def get_new_activity_files():

    known_files = set()
    if os.path.exists(ACTIVITY_FILES):
        with open(ACTIVITY_FILES, "r") as f:
            known_files = {line.strip() for line in f}

    current_files = {f for f in os.listdir(ACTIVITIES) if f.lower().endswith(FIT_EXT)}
    new_files = current_files - known_files

    if new_files:
        print("New .fit files detected:", new_files)
        with open(ACTIVITY_FILES, "w") as f:
            for fname in sorted(current_files):
                f.write(f"{fname}\n")
    else:
        print("No new .fit files.")

    return new_files

def load_activity(file):

    path = os.path.join(ACTIVITIES, file)
    stream = Stream.from_file(path)
    decoder = Decoder(stream)

    messages, errors = decoder.read(
        apply_scale_and_offset=False,
        convert_datetimes_to_dates=False,
        convert_types_to_strings=False,
        enable_crc_check=False,
        expand_sub_fields=False,
        expand_components=False,
        merge_heart_rates=False
    )

    if errors:
        print(f"Errors in {file}:", errors)

    if 'record_mesgs' not in messages:
        print(f'No "record_mesgs" in {file}')
        return np.empty((0, 2), dtype=np.int32)

    df = pd.DataFrame(messages['record_mesgs'])
    coords = df[['position_lat', 'position_long']].dropna().to_numpy()
    coords = np.round(coords, -3)
    return coords[::10]

def load_activities(files):

    with Pool(processes=max(1, os.cpu_count() - 1)) as pool:
        results = pool.map(load_activity, files)

    if not results:
        return np.empty((0, 2))

    coords = np.vstack(results)
    return coords * FIT_SCALE

def haversine(coord1, coord2):

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def filter_coords(coords, filtered=None, min_distance=5):

    if coords is None or len(coords) == 0:
        return np.array(filtered) if filtered else np.array([])

    if filtered is None:
        filtered = [coords[0]]
        coords_iter = coords[1:]
    else:
        coords_iter = coords

    for coord in coords_iter:
        if all(haversine(coord, f) >= min_distance for f in filtered):
            filtered.append(coord)

    return np.array(filtered)
