from numba import cuda, float32
import math

@cuda.jit
def update_motion_kernel(
    pos, vel, heading,
    cmd_speed, cmd_turn, cmd_alt,
    max_accel, max_turn_rate, max_climb_rate,
    dt, n,
    cmd_target_heading
):
    i = cuda.grid(1)
    if i >= n:
        return

    # Ambil heading & velocity sekarang
    current_heading = heading[i]
    vx = vel[i][0]
    vy = vel[i][1]
    vz = vel[i][2]

    # Hitung kecepatan sekarang (horizontal only)
    speed = math.sqrt(vx * vx + vy * vy)

    # ===============================
    #   SPEED CONTROL
    # ===============================
    target_speed = cmd_speed[i]
    delta_speed = target_speed - speed
    max_delta_v = max_accel[i] * dt

    if abs(delta_speed) > max_delta_v:
        delta_speed = math.copysign(max_delta_v, delta_speed)

    new_speed = speed + delta_speed

    # ===============================
    #   ALTITUDE CONTROL
    # ===============================
    target_alt = cmd_alt[i]
    delta_alt = target_alt - pos[i][2]
    max_delta_alt = max_climb_rate[i] * dt / 60.0  # ft/min → ft/sec

    if abs(delta_alt) > max_delta_alt:
        delta_alt = math.copysign(max_delta_alt, delta_alt)
    pos[i][2] += delta_alt  # langsung update z-nya

    # ===============================
    #   HEADING CONTROL (ABSOLUT)
    # ===============================
    target_heading = cmd_target_heading[i]
    if not math.isnan(target_heading):
        # Normalisasi heading saat ini dan target ke [0, 2π)
        ch = current_heading % (2 * math.pi)
        th = target_heading % (2 * math.pi)

        # Hitung delta arah terpendek [-π, π]
        delta = (th - ch + math.pi) % (2 * math.pi) - math.pi
        max_delta = max_turn_rate[i] * dt

        if abs(delta) <= max_delta:
            # Sudah cukup dekat — langsung ke target
            new_heading = th
            cmd_turn[i] = 0.0
            cmd_target_heading[i] = float('nan')
        else:
            new_heading = ch + math.copysign(max_delta, delta)

        heading[i] = new_heading
    else:
        # Tidak ada target heading → lanjutkan rotasi biasa
        delta = cmd_turn[i]
        max_delta = max_turn_rate[i] * dt
        if abs(delta) > max_delta:
            delta = math.copysign(max_delta, delta)
        new_heading = current_heading + delta 
        new_heading = new_heading % (2 * math.pi)

        heading[i] = new_heading

    # ===============================
    #   UPDATE VELOCITY & POSISI
    # ===============================
    vx = new_speed * math.cos(heading[i])
    vy = new_speed * math.sin(heading[i])
    vel[i][0] = vx
    vel[i][1] = vy

    pos[i][0] += vx * dt * 0.00015  # konversi ke derajat lon
    pos[i][1] += vy * dt * 0.00015  # konversi ke derajat lat

# from numba import cuda, float32
# import math

# @cuda.jit
# def update_motion_kernel(
    # pos, vel, heading,
    # cmd_speed, cmd_turn, cmd_alt,
    # max_accel, max_turn_rate, max_climb_rate,
    # dt, n, cmd_target_heading
# ):
    # i = cuda.grid(1)
    # if i >= n:
        # return


    # # Update posisi berdasarkan velocity konstan
    # #pos[i][0] += vel[i][0] * dt * 0.00015  # lon
    # #pos[i][1] += vel[i][1] * dt * 0.00015  # lat
    
    # # # Konversi vektor kecepatan menjadi speed dan heading
    # speed = math.sqrt(vel[i][0] ** 2 + vel[i][1] ** 2)
    # current_heading = heading[i]

    # # # Speed control
    # target_speed = cmd_speed[i]
    # delta_speed = target_speed - speed
    # max_delta_v = max_accel[i] * dt
    # if abs(delta_speed) > max_delta_v:
        # delta_speed = math.copysign(max_delta_v, delta_speed)
    # new_speed = speed + delta_speed

    # # # Turn control
    # # target_turn = cmd_turn[i]
    # # max_delta_heading = max_turn_rate[i] * dt
    # # if abs(target_turn) > max_delta_heading:
        # # target_turn = math.copysign(max_delta_heading, target_turn)
    # # new_heading = current_heading + target_turn
    # # heading[i] = new_heading
    # # Ambil target heading absolut (jika ada)
    # target_heading = cmd_target_heading[i]

    # if not math.isnan(target_heading):
        # # ✅ Normalisasi kedua heading ke [0, 2π)
        # ch = current_heading % (2 * math.pi)
        # th = target_heading % (2 * math.pi)

        # # ✅ Hitung delta ke arah pendek (bisa negatif atau positif)
        # delta = (th - ch + math.pi) % (2 * math.pi) - math.pi

        # max_delta = max_turn_rate[i] * dt

        # if abs(delta) <= max_delta:
            # # Sudah dekat, langsung set heading
            # new_heading = target_heading
            # heading[i] = new_heading
            # cmd_turn[i] = 0.0
            # cmd_target_heading[i] = float('nan')
        # else:
            # # Belok ke arah pendek
            # heading[i] = current_heading + math.copysign(max_delta, delta)
            

    # # # Climb control
    # target_alt = cmd_alt[i]
    # delta_alt = target_alt - pos[i][2]
    # max_delta_alt = max_climb_rate[i] * dt / 60.0  # convert ft/min to ft/sec
    # if abs(delta_alt) > max_delta_alt:
        # delta_alt = math.copysign(max_delta_alt, delta_alt)
    # pos[i][2] += delta_alt

    # # # Update velocity berdasarkan heading dan speed
    # vx = new_speed * math.cos(heading[i])
    # vy = new_speed * math.sin(heading[i])
    # vel[i][0] = vx
    # vel[i][1] = vy

    # # # Update posisi
    # pos[i][0] += vx * dt * 0.00015  # koefisien konversi lon (sekitar 1 NM = 0.00015 derajat)
    # pos[i][1] += vy * dt * 0.00015  # koefisien konversi lat
