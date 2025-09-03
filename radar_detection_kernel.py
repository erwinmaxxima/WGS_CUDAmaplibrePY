# radar_detection_kernel.py
from numba import cuda
import math

@cuda.jit
def radar_detection_kernel(pos, radar_lon, radar_lat, detect_flags, range_km, n_planes, radar_count):
    """
    pos: (N,3) float32 [lon, lat, alt]
    radar_lon, radar_lat: arrays of radar positions (float32)
    detect_flags: int32 array length N (0/1)
    range_km: float scalar (km)
    """
    i = cuda.grid(1)
    if i >= n_planes:
        return

    px = pos[i, 0]
    py = pos[i, 1]

    # convert lat -> rad for lon scaling
    lat_rad = py * (math.pi / 180.0)

    # approx km per degree
    km_per_deg_lat = 111.32
    km_per_deg_lon = km_per_deg_lat * math.cos(lat_rad)
    if km_per_deg_lon <= 0.0:
        km_per_deg_lon = km_per_deg_lat * 1e-6

    detected = 0
    for r in range(radar_count):
        dlon = radar_lon[r] - px
        dlat = radar_lat[r] - py

        dx_km = dlon * km_per_deg_lon
        dy_km = dlat * km_per_deg_lat
        dist = math.sqrt(dx_km * dx_km + dy_km * dy_km)

        if dist <= range_km:
            detect_flags[i] = 1
            detected = 1
            break

    if detected == 0:
        detect_flags[i] = 0
