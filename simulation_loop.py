import numpy as np
import math
from numba import cuda
from update_motion_kernel import update_motion_kernel
from radar_detection_kernel import radar_detection_kernel  # new
from radar_config import RADARS, RADAR_COUNT, RADAR_RANGE_KM


# Konstanta
NUM_PLANES = 1000
DT = 1.0  # deltaT dalam detik

ids = np.arange(NUM_PLANES, dtype=np.int32)  # ID tetap untuk tiap pesawat
pos = np.random.uniform(low=[94.5, -9.4, 10000], high=[140.0, 6.0, 10000], size=(NUM_PLANES, 3)).astype(np.float32)

# Heading awal acak dalam radian
heading = np.random.uniform(0, 2 * np.pi, size=NUM_PLANES).astype(np.float32)

cmd_target_heading = np.full(NUM_PLANES, np.nan, dtype=np.float32)

# Kecepatan awal (vx, vy, vz) dari heading dan kecepatan tetap (250 knots)
speed = 250.0  # knots
vx = speed * np.cos(heading)
vy = speed * np.sin(heading)
vz = np.zeros(NUM_PLANES, dtype=np.float32)
vel = np.stack((vx, vy, vz), axis=1).astype(np.float32)

# Perintah kontrol
cmd_speed = np.full(NUM_PLANES, 0.0, dtype=np.float32)  # knots
cmd_turn = np.zeros(NUM_PLANES, dtype=np.float32)         # radian
cmd_alt = np.full(NUM_PLANES, 10000.0, dtype=np.float32)  # feet

max_accel = np.random.uniform(5, 20, size=NUM_PLANES).astype(np.float32)       # knot/s
max_turn_rate = np.random.uniform(0.1, 0.5, size=NUM_PLANES).astype(np.float32)  # rad/s
max_climb_rate = np.random.uniform(500, 3000, size=NUM_PLANES).astype(np.float32)  # ft/min


# -----------------------------
# Radar configuration (baru)
# -----------------------------
RADAR_COUNT = 100
RADAR_RANGE_KM = 250.0  # jangkauan 250 km

# wilayah indonesia (approx bounding box)
RADAR_LON_MIN, RADAR_LON_MAX = 95.0, 141.0
RADAR_LAT_MIN, RADAR_LAT_MAX = -11.0, 6.0

# generate radar positions (di host)
#radar_lon = np.random.uniform(RADAR_LON_MIN, RADAR_LON_MAX, size=RADAR_COUNT).astype(np.float32)
#radar_lat = np.random.uniform(RADAR_LAT_MIN, RADAR_LAT_MAX, size=RADAR_COUNT).astype(np.float32)
radar_lon = np.array([r["lon"] for r in RADARS], dtype=np.float32)
radar_lat = np.array([r["lat"] for r in RADARS], dtype=np.float32)

# Salin ke device
d_pos = cuda.to_device(pos)
d_vel = cuda.to_device(vel)
d_heading = cuda.to_device(heading)
d_cmd_speed = cuda.to_device(cmd_speed)
d_cmd_turn = cuda.to_device(cmd_turn)
d_cmd_alt = cuda.to_device(cmd_alt)
d_cmd_target_heading = cuda.to_device(cmd_target_heading)

d_max_accel = cuda.to_device(max_accel)
d_max_turn_rate = cuda.to_device(max_turn_rate)
d_max_climb_rate = cuda.to_device(max_climb_rate)


# radar device arrays
d_radar_lon = cuda.to_device(radar_lon)
d_radar_lat = cuda.to_device(radar_lat)

# detection flags (0/1)
detect_flags = np.zeros(NUM_PLANES, dtype=np.int32)
d_detect_flags = cuda.to_device(detect_flags)

threads_per_block = 128
blocks_per_grid = (NUM_PLANES + (threads_per_block - 1)) // threads_per_block


if __name__ == "__main__":
    update_motion_kernel[blocks_per_grid, threads_per_block](
        d_pos, d_vel, d_heading, d_cmd_speed, d_cmd_turn, d_cmd_alt,
        d_max_accel, d_max_turn_rate, d_max_climb_rate, DT, NUM_PLANES, d_cmd_target_heading
    )

    # detection kernel
    radar_detection_kernel[blocks_per_grid, threads_per_block](
        d_pos, d_radar_lon, d_radar_lat, d_detect_flags, np.float32(RADAR_RANGE_KM),
        NUM_PLANES, RADAR_COUNT
    )

    new_pos = d_pos.copy_to_host()
    new_heading = d_heading.copy_to_host()
    flags = d_detect_flags.copy_to_host()

    print("Sample posisi:", new_pos[:3])
    print("Sample heading:", new_heading[:3])
    print("Sample detect flags (3):", flags[:3])
    print("Total detected:", int(flags.sum()))

def simulate_one_step():
    update_motion_kernel[blocks_per_grid, threads_per_block](
        d_pos, d_vel, d_heading, d_cmd_speed, d_cmd_turn, d_cmd_alt,
        d_max_accel, d_max_turn_rate, d_max_climb_rate, DT, NUM_PLANES, d_cmd_target_heading
    )

    # run radar detection kernel on GPU
    radar_detection_kernel[blocks_per_grid, threads_per_block](
        d_pos, d_radar_lon, d_radar_lat, d_detect_flags, np.float32(RADAR_RANGE_KM),
        NUM_PLANES, RADAR_COUNT
    )
    
def get_positions():
    pos_host = d_pos.copy_to_host()
    heading_host = d_heading.copy_to_host()
    flags = d_detect_flags.copy_to_host()

    result = []
    for idx, (p, h, f) in enumerate(zip(pos_host, heading_host, flags)):
        if int(f) == 1:
            result.append({
                "id": int(ids[idx]),         # ID sesuai indeks
                "lon": float(p[0]),
                "lat": float(p[1]),
                "alt": float(p[2]),
                "heading": float(h)
            })

    return result

id_to_index = {i: idx for idx, i in enumerate(ids)}

def apply_pending_commands(commands):
    for cmd in commands:
        plane_id = cmd["id"]
        cmd_type = cmd["command"]
        value = float(cmd["value"])

        if plane_id not in id_to_index:
            continue  # abaikan jika ID tidak ditemukan

        idx = id_to_index[plane_id]
        print(commands)
        if cmd_type == "speedto":
            cmd_speed[idx] = value
        elif cmd_type == "headingto":
            degrees_adjusted = (90 - value) % 360
            target_heading_rad = math.radians(degrees_adjusted % 360)
            cmd_target_heading[idx] = target_heading_rad
        elif cmd_type == "heightto":
            cmd_alt[idx] = value

def normalize_angle(angle_rad):
    while angle_rad > math.pi:
        angle_rad -= 2 * math.pi
    while angle_rad < -math.pi:
        angle_rad += 2 * math.pi
    return angle_rad

def sync_cmd_buffers_to_device():
    d_cmd_speed.copy_to_device(cmd_speed)
    d_cmd_turn.copy_to_device(cmd_turn)
    d_cmd_alt.copy_to_device(cmd_alt)
    d_cmd_target_heading.copy_to_device(cmd_target_heading)
