"""HTTP API that mimics a Bitaxe running ESP-Miner."""

from __future__ import annotations

import os

from flask import Flask, jsonify, request

from device import BitaxeDevice

app = Flask(__name__)
device = BitaxeDevice()


@app.get("/")
def root():
    return jsonify({"status": "ok", "device": device.hostname, "model": device.model_name})


@app.get("/api/system/info")
def system_info():
    return jsonify(device.system_info())


@app.get("/api/system/asic")
def system_asic():
    return jsonify(device.asic_info())


@app.get("/api/system/wifi/scan")
def wifi_scan():
    return jsonify(
        {
            "networks": [
                {"ssid": device.ssid, "rssi": device.wifi_rssi, "authmode": 3},
                {"ssid": "Neighbor-WiFi", "rssi": -72, "authmode": 4},
            ]
        }
    )


@app.get("/api/system/statistics")
def statistics():
    info = device.system_info()
    return jsonify(
        {
            "currentTimestamp": device.uptime_seconds(),
            "labels": ["hashrate", "asicTemp", "power"],
            "statistics": [[info["hashRate"], info["temp"], info["power"]]],
        }
    )


@app.get("/api/system/statistics/dashboard")
def statistics_dashboard():
    return statistics()


@app.post("/api/system/restart")
def restart():
    device.restart()
    return jsonify({"message": "restarting"})


@app.post("/api/system/identify")
def identify():
    return jsonify({"message": "ok"})


@app.patch("/api/system")
def patch_system():
    payload = request.get_json(silent=True) or {}
    device.apply_settings(payload)
    return jsonify({"message": "ok"})


def main() -> None:
    host = os.getenv("BIND_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "80"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
