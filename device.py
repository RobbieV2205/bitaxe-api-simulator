"""Live simulated Bitaxe state with correlated, slowly changing telemetry."""

from __future__ import annotations

import hashlib
import os
import random
import time
from typing import Any

from models import get_model


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _walk(value: float, step: float, low: float, high: float) -> float:
    return _clamp(value + random.uniform(-step, step), low, high)


def _mac_from_name(name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()
    parts = [digest[i : i + 2] for i in range(0, 10, 2)]
    parts[0] = f"{int(parts[0], 16) & 0xFE | 0x02:02x}"
    return ":".join(parts).upper()


class BitaxeDevice:
    def __init__(self) -> None:
        self.model_name = os.getenv("BITAXE_MODEL", "gamma")
        self.profile = get_model(self.model_name)
        self.hostname = os.getenv("BITAXE_HOSTNAME", f"bitaxe-{self.model_name}")
        self.ssid = os.getenv("BITAXE_SSID", "HomeNET")
        self.ipv4 = os.getenv("BITAXE_IPV4", "0.0.0.0")
        self.mac_addr = os.getenv("BITAXE_MAC", _mac_from_name(self.hostname))

        self.board_version = int(os.getenv("BITAXE_BOARD_VERSION", self.profile["boardVersion"]))
        self.frequency = int(os.getenv("BITAXE_FREQUENCY", self.profile["defaultFrequency"]))
        self.core_voltage = int(os.getenv("BITAXE_CORE_VOLTAGE", self.profile["defaultVoltage"]))
        self.temp_target = int(os.getenv("BITAXE_TEMP_TARGET", "60"))
        self.auto_fan_speed = 1
        self.manual_fan_speed = 100
        self.min_fan_speed = 25
        self.overclock_enabled = 0
        self.overheat_mode = 0
        self.stats_frequency = 0

        temp_low, temp_high = self.profile["tempRange"]
        power_low, power_high = self.profile["powerRange"]
        self.temp = random.uniform(temp_low + 4, temp_high - 4)
        self.power = random.uniform(power_low + 1, power_high - 1)
        self.hash_rate = self.profile["expectedHashrate"] * random.uniform(0.97, 1.03)
        self.fan_speed = 45.0
        self.fan_rpm = 3600
        self.started_at = time.time() - random.randint(300, 86400)

        self.shares_accepted = random.randint(100, 8000)
        self.shares_rejected = random.randint(0, 20)
        self.best_diff = random.randint(50_000, 50_000_000)
        self.best_session_diff = random.randint(10_000, 2_000_000)
        self.block_height = random.randint(900_000, 940_000)
        self.wifi_rssi = random.randint(-62, -38)
        self.voltage_mv = self.profile["nominalVoltage"] * 1000 + random.uniform(-80, 80)

        self.stratum_url = os.getenv("BITAXE_STRATUM_URL", "public-pool.io")
        self.stratum_port = int(os.getenv("BITAXE_STRATUM_PORT", "21496"))
        self.stratum_user = os.getenv(
            "BITAXE_STRATUM_USER",
            "bc1qexample000000000000000000000000000000.bitaxe",
        )

    def uptime_seconds(self) -> int:
        return int(time.time() - self.started_at)

    def restart(self) -> None:
        self.started_at = time.time()
        self.best_session_diff = 0
        self.shares_accepted = 0
        self.shares_rejected = 0

    def apply_settings(self, payload: dict[str, Any]) -> None:
        if "frequency" in payload:
            self.frequency = int(payload["frequency"])
        if "coreVoltage" in payload:
            self.core_voltage = int(payload["coreVoltage"])
        if "temptarget" in payload:
            self.temp_target = int(payload["temptarget"])
        if "fanspeed" in payload:
            self.manual_fan_speed = int(payload["fanspeed"])
            if not self.auto_fan_speed:
                self.fan_speed = float(self.manual_fan_speed)
        if "autofanspeed" in payload:
            self.auto_fan_speed = int(payload["autofanspeed"])
        if "overclockEnabled" in payload:
            self.overclock_enabled = int(payload["overclockEnabled"])
        if "overheat_mode" in payload:
            self.overheat_mode = int(payload["overheat_mode"])
        if "hostname" in payload:
            self.hostname = str(payload["hostname"])
        if "ssid" in payload:
            self.ssid = str(payload["ssid"])
        if "stratumURL" in payload:
            self.stratum_url = str(payload["stratumURL"])
        if "stratumPort" in payload:
            self.stratum_port = int(payload["stratumPort"])
        if "stratumUser" in payload:
            self.stratum_user = str(payload["stratumUser"])

    def tick(self) -> None:
        temp_low, temp_high = self.profile["tempRange"]
        power_low, power_high = self.profile["powerRange"]
        expected = self.profile["expectedHashrate"]

        self.temp = _walk(self.temp, 0.35, temp_low, temp_high)

        if self.auto_fan_speed:
            error = self.temp - self.temp_target
            target_fan = _clamp(self.min_fan_speed + error * 4.5, self.min_fan_speed, 100)
            self.fan_speed = _walk(self.fan_speed + (target_fan - self.fan_speed) * 0.15, 0.8, 0, 100)
        else:
            self.fan_speed = float(self.manual_fan_speed)

        self.fan_rpm = int(_clamp(self.fan_speed * 48 + random.uniform(-80, 80), 0, 6000))

        load = 0.92 + (self.frequency / max(self.profile["defaultFrequency"], 1)) * 0.08
        self.hash_rate = _walk(self.hash_rate, expected * 0.012, expected * 0.90, expected * 1.08)
        self.hash_rate *= 0.999 + load * 0.001

        nominal_power = (power_low + power_high) / 2
        self.power = _walk(
            self.power,
            0.25,
            power_low,
            power_high,
        )
        self.power = _clamp(
            self.power * 0.97 + (nominal_power * (self.hash_rate / expected)) * 0.03,
            power_low,
            power_high,
        )

        self.voltage_mv = _walk(self.voltage_mv, 8.0, 4800, 5300)
        self.wifi_rssi = int(_walk(float(self.wifi_rssi), 1.2, -75, -35))

        if random.random() < 0.35:
            self.shares_accepted += 1
        if random.random() < 0.01:
            self.shares_rejected += 1

        if random.random() < 0.02:
            self.best_session_diff = max(self.best_session_diff, random.randint(1_000, 500_000))
            self.best_diff = max(self.best_diff, self.best_session_diff)

    def system_info(self) -> dict[str, Any]:
        self.tick()
        current = self.power / max(self.voltage_mv / 1000.0, 0.001) * 1000.0
        domain = self.hash_rate / 4.0
        return {
            "power": round(self.power, 7),
            "voltage": round(self.voltage_mv, 2),
            "current": round(current, 3),
            "temp": round(self.temp, 3),
            "temp2": -1,
            "vrTemp": round(self.temp + random.uniform(0.5, 3.0), 0),
            "maxPower": self.profile["maxPower"],
            "nominalVoltage": self.profile["nominalVoltage"],
            "hashRate": round(self.hash_rate, 7),
            "hashRate_1m": round(self.hash_rate * random.uniform(0.995, 1.005), 7),
            "hashRate_10m": round(self.hash_rate * random.uniform(0.99, 1.01), 7),
            "hashRate_1h": round(self.hash_rate * random.uniform(0.985, 1.015), 7),
            "expectedHashrate": self.profile["expectedHashrate"],
            "errorPercentage": 0,
            "bestDiff": self.best_diff,
            "bestSessionDiff": self.best_session_diff,
            "poolDifficulty": 1000,
            "isUsingFallbackStratum": 0,
            "poolAddrFamily": 2,
            "isPSRAMAvailable": 1,
            "freeHeap": 8212708,
            "freeHeapInternal": 104027,
            "freeHeapSpiram": 8140652,
            "coreVoltage": self.core_voltage,
            "coreVoltageActual": self.core_voltage - random.randint(2, 8),
            "frequency": self.frequency,
            "ssid": self.ssid,
            "macAddr": self.mac_addr,
            "hostname": self.hostname,
            "ipv4": self.ipv4,
            "ipv6": "",
            "wifiStatus": "Connected!",
            "wifiRSSI": self.wifi_rssi,
            "apEnabled": 0,
            "sharesAccepted": self.shares_accepted,
            "sharesRejected": self.shares_rejected,
            "sharesRejectedReasons": [
                {"message": "Stale", "count": self.shares_rejected}
            ]
            if self.shares_rejected
            else [],
            "uptimeSeconds": self.uptime_seconds(),
            "smallCoreCount": self.profile["smallCoreCount"],
            "ASICModel": self.profile["ASICModel"],
            "stratumURL": self.stratum_url,
            "stratumPort": self.stratum_port,
            "stratumUser": self.stratum_user,
            "stratumSuggestedDifficulty": 1000,
            "stratumExtranonceSubscribe": 0,
            "fallbackStratumURL": "solo.ckpool.org",
            "fallbackStratumPort": 3333,
            "fallbackStratumUser": self.stratum_user,
            "fallbackStratumSuggestedDifficulty": 1000,
            "fallbackStratumExtranonceSubscribe": 0,
            "responseTime": round(random.uniform(80.0, 250.0), 3),
            "version": "v2.12.2",
            "axeOSVersion": "v2.12.2",
            "idfVersion": "v5.5.1",
            "boardVersion": str(self.board_version),
            "resetReason": "Software reset via esp_restart",
            "runningPartition": "factory",
            "overheat_mode": self.overheat_mode,
            "overclockEnabled": self.overclock_enabled,
            "display": self.profile["display"],
            "rotation": 0,
            "invertscreen": 0,
            "displayTimeout": -1,
            "autofanspeed": self.auto_fan_speed,
            "fanspeed": round(self.fan_speed, 7),
            "manualFanSpeed": self.manual_fan_speed,
            "minFanSpeed": self.min_fan_speed,
            "temptarget": self.temp_target,
            "fanrpm": self.fan_rpm,
            "fan2rpm": 0,
            "statsFrequency": self.stats_frequency,
            "blockFound": 0,
            "blockHeight": self.block_height,
            "scriptsig": "",
            "networkDifficulty": 146472570619930,
            "hashrateMonitor": {
                "asics": [
                    {
                        "total": round(self.hash_rate, 7),
                        "domains": [round(domain + random.uniform(-8, 8), 7) for _ in range(4)],
                        "errorCount": random.randint(0, 50),
                    }
                ]
            },
        }

    def asic_info(self) -> dict[str, Any]:
        return {
            "ASICModel": self.profile["ASICModel"],
            "deviceModel": self.profile["deviceModel"],
            "swarmColor": self.profile["swarmColor"],
            "asicCount": self.profile["asicCount"],
            "defaultFrequency": self.profile["defaultFrequency"],
            "frequencyOptions": self.profile["frequencyOptions"],
            "defaultVoltage": self.profile["defaultVoltage"],
            "voltageOptions": self.profile["voltageOptions"],
        }
