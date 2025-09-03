# radar_config.py
import numpy as np

RADAR_COUNT = 100
RADAR_RANGE_KM = 250.0

RADAR_LON_MIN, RADAR_LON_MAX = 95.0, 141.0
RADAR_LAT_MIN, RADAR_LAT_MAX = -11.0, 6.0

_RAND_SEED = 42

def generate_radars(count: int = RADAR_COUNT, seed: int = _RAND_SEED):
    rng = np.random.default_rng(seed)
    lons = rng.uniform(RADAR_LON_MIN, RADAR_LON_MAX, size=count).astype(np.float32)
    lats = rng.uniform(RADAR_LAT_MIN, RADAR_LAT_MAX, size=count).astype(np.float32)
    radars = [{"lon": float(lon), "lat": float(lat), "range_km": float(RADAR_RANGE_KM)} for lon, lat in zip(lons, lats)]
    return radars

RADARS = generate_radars()
