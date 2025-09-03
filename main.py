from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from simulation_loop import simulate_one_step, get_positions, apply_pending_commands,sync_cmd_buffers_to_device
import time

pending_commands = []
time_scale = 30.0  # Faktor kecepatan simulasi (dinaikkan dari 1.0)

from radar_config import RADARS


import asyncio
import json
import random

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files di /static
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve index.html secara manual di "/"
@app.get("/")
async def get_index():
    return HTMLResponse((static_dir / "index.html").read_text())


@app.get("/radars")
async def get_radars():
    """
    Kembalikan list radar: [{lon, lat, range_km}, ...]
    Frontend gunakan ini untuk menampilkan marker + circle.
    """
    return {"radars": RADARS}

# WebSocket endpoint tetap di /ws
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("connection open")
    last_time = time.time()
    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            try:
                # Periksa jika ada pesan masuk
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                data = json.loads(msg)
                # Perintah global untuk mengubah kecepatan simulasi
                if data.get("command") == "timescale":
                    global time_scale
                    time_scale = float(data.get("value", 1.0))
                # Perintah untuk pesawat tertentu
                elif "command" in data and "id" in data and "value" in data:
                    pending_commands.append(data)
            except asyncio.TimeoutError:
                pass  # Tidak ada pesan baru, lanjut simulasi

            # Jalankan simulasi satu langkah
            if pending_commands:
                apply_pending_commands(pending_commands)
                sync_cmd_buffers_to_device()
                pending_commands.clear()

            simulate_one_step(dt * time_scale)
            plane_list = get_positions()
            await websocket.send_text(json.dumps({"planes": plane_list}))


    except WebSocketDisconnect:
        print("connection closed")
