import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in nautical miles between two points
    on the earth (specified in decimal degrees).
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    # Radius of earth in nautical miles is approx 3440.06
    r = 3440.06
    return c * r

def run_test():
    # Test parameters
    start_pos = (0.0, 0.0, 10000.0)  # lon, lat, alt
    speed_knots = 1.0
    heading_deg = 0  # North
    # Convert to simulation's angle convention (0 deg North = 90 deg mathematical angle)
    heading_rad = math.radians(90 - heading_deg)

    total_time_seconds = 3600
    dt = 1.0  # 1 second timestep

    # Simulation variables
    current_pos = start_pos
    time_elapsed = 0.0

    print("Starting calculation test...")
    print(f"Aircraft at {start_pos}, Speed: {speed_knots} kts, Heading: {heading_deg} deg (North)")
    print("-" * 80)
    print(f"{'Time (s)':>10} | {'Dist (NM)':>15} | {'Expected Dist (NM)':>20} | {'Speed (kts)':>15} | {'Error (NM)':>15}")
    print("-" * 80)

    # Pre-calculate velocity components
    vx = speed_knots * math.cos(heading_rad)
    vy = speed_knots * math.sin(heading_rad)

    for step in range(int(total_time_seconds / dt)):
        time_elapsed += dt

        # Update position using the corrected logic from the CUDA kernel
        deg_per_sec_factor = 1.0 / (3600.0 * 60.0)
        current_pos = (
            current_pos[0] + (vx * dt * deg_per_sec_factor),
            current_pos[1] + (vy * dt * deg_per_sec_factor),

            current_pos[2]
        )

        distance_nm = haversine_distance(start_pos[1], start_pos[0], current_pos[1], current_pos[0])
        expected_distance_nm = speed_knots * (time_elapsed / 3600.0)
        current_speed_kts = (distance_nm / time_elapsed) * 3600.0 if time_elapsed > 0 else 0
        error_nm = distance_nm - expected_distance_nm

        # Print progress every 10 minutes and at the very end
        if step % 600 == 0 or step == int(total_time_seconds/dt) - 1:
             print(f"{time_elapsed:10.0f} | {distance_nm:15.6f} | {expected_distance_nm:20.6f} | {current_speed_kts:15.6f} | {error_nm:15.6f}")

    print("-" * 80)
    print("Test finished.")
    print(f"Final position: lon={current_pos[0]:.6f}, lat={current_pos[1]:.6f}")
    print(f"Total time: {time_elapsed} s")
    print(f"Total distance traveled: {distance_nm:.6f} NM")
    print(f"Expected distance: {1.0:.6f} NM")
    print(f"Final error: {error_nm:.6f} NM ({abs(error_nm / 1.0) * 100:.2f}%)")

if __name__ == "__main__":
    run_test()
