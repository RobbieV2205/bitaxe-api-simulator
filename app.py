import os
import random
import time
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)

STARTED_AT = time.time()

DEVICE_IP = os.environ.get("DEVICE_IP", "192.168.1.41")
HOSTNAME = os.environ.get("HOSTNAME", "bitaxe")
MAC_ADDR = os.environ.get("MAC_ADDR", "02:BA:41:00:00:01")
BOARD_VERSION = os.environ.get("BOARD_VERSION", "601")
FIRMWARE_VERSION = os.environ.get("FIRMWARE_VERSION", "v2.12.2")
STRATUM_USER = os.environ.get(
    "STRATUM_USER",
    "bc1qnp980s5fpp8l94p5cvttmtdqy8rvrq74qly2yrfmzkdsntqzlc5qkc4rkq.bitaxe",
)


def _jitter(value: float, spread: float) -> float:
    return value + random.uniform(-spread, spread)


def _uptime_seconds() -> int:
    return int(time.time() - STARTED_AT)


def build_system_info() -> dict:
    frequency = random.choice([490, 500, 525, 550, 575])
    core_voltage = random.choice([1100, 1150, 1200, 1250])
    temp_target = random.randint(55, 65)
    fan_speed = round(random.uniform(28.0, 72.0), 7)
    fan_rpm = int(1800 + fan_speed * 45 + random.uniform(-120, 120))
    hash_rate = round(random.uniform(980.0, 1320.0), 7)
    temp = round(random.uniform(48.0, 66.0), 3)
    power = round(random.uniform(13.5, 18.5), 7)
    uptime = _uptime_seconds()

    core_voltage_actual = core_voltage + random.randint(-8, 4)
    actual_frequency = frequency + random.choice([-2, -1, 0, 0, 1])
    voltage = round(random.uniform(4980.0, 5120.0), 2)
    current = round((power / (voltage / 1000.0)) * 1000.0, 3)
    vr_temp = round(temp + random.uniform(1.5, 6.0), 1)
    expected = {490: 1071, 500: 1100, 525: 1155, 550: 1210, 575: 1265}.get(
        frequency, 1071
    )
    hash_rate_1m = round(_jitter(hash_rate, 25), 7)
    hash_rate_10m = round(_jitter(hash_rate, 15), 7)
    hash_rate_1h = round(_jitter(hash_rate, 8), 7)
    domain_share = hash_rate / 4.0
    shares_accepted = max(0, uptime // random.randint(3, 6))
    shares_rejected = random.randint(0, max(1, shares_accepted // 80))

    return {
        "power": power,
        "voltage": voltage,
        "current": current,
        "temp": temp,
        "temp2": -1,
        "vrTemp": vr_temp,
        "maxPower": 40,
        "nominalVoltage": 5,
        "hashRate": hash_rate,
        "hashRate_1m": hash_rate_1m,
        "hashRate_10m": hash_rate_10m,
        "hashRate_1h": hash_rate_1h,
        "expectedHashrate": expected,
        "errorPercentage": round(random.uniform(0.0, 0.4), 4),
        "bestDiff": random.randint(1_000_000, 50_000_000),
        "bestSessionDiff": random.randint(50_000, 3_000_000),
        "poolDifficulty": 1000,
        "isUsingFallbackStratum": 0,
        "poolAddrFamily": 2,
        "poolConnectionInfo": "IPv4",
        "isPSRAMAvailable": 1,
        "freeHeap": random.randint(8_000_000, 8_400_000),
        "freeHeapInternal": random.randint(90_000, 120_000),
        "freeHeapSpiram": random.randint(7_900_000, 8_200_000),
        "minFreeHeap": random.randint(7_500_000, 7_900_000),
        "maxAllocHeap": random.randint(80_000, 110_000),
        "coreVoltage": core_voltage,
        "coreVoltageActual": core_voltage_actual,
        "frequency": frequency,
        "actualFrequency": actual_frequency,
        "ssid": "HomeNET",
        "macAddr": MAC_ADDR,
        "hostname": HOSTNAME,
        "fullHostname": f"{HOSTNAME}.local",
        "mdnsHostname": f"{HOSTNAME}.local",
        "ipv4": DEVICE_IP,
        "ipv6": "FE80::F2F5:BDFF:FE44:B2F0",
        "wifiStatus": "Connected!",
        "wifiRSSI": random.randint(-62, -38),
        "apEnabled": 0,
        "sharesAccepted": shares_accepted,
        "sharesRejected": shares_rejected,
        "sharesRejectedReasons": (
            [{"message": "Stale", "count": shares_rejected}]
            if shares_rejected
            else []
        ),
        "sharesPending": 0,
        "uptimeSeconds": uptime,
        "totalUptimeSeconds": uptime,
        "smallCoreCount": 2040,
        "ASICModel": "BM1370",
        "stratumURL": "public-pool.io",
        "stratumPort": 21496,
        "stratumUser": STRATUM_USER,
        "stratumSuggestedDifficulty": 1000,
        "stratumExtranonceSubscribe": 0,
        "stratumProtocol": "SV1",
        "stratumTLS": False,
        "stratumCert": "",
        "stratumDecodeCoinbase": False,
        "stratumShareWarning": True,
        "stratumV2AuthorityPubkey": "",
        "stratumV2ChannelType": "standard",
        "fallbackStratumURL": "solo.ckpool.org",
        "fallbackStratumPort": 3333,
        "fallbackStratumUser": STRATUM_USER,
        "fallbackStratumSuggestedDifficulty": 1000,
        "fallbackStratumExtranonceSubscribe": 0,
        "fallbackStratumTLS": False,
        "fallbackStratumCert": "",
        "fallbackStratumDecodeCoinbase": False,
        "fallbackStratumShareWarning": True,
        "fallbackStratumProtocol": "SV1",
        "fallbackStratumV2AuthorityPubkey": "",
        "fallbackStratumV2ChannelType": "standard",
        "responseTime": round(random.uniform(80.0, 220.0), 3),
        "version": FIRMWARE_VERSION,
        "axeOSVersion": FIRMWARE_VERSION,
        "idfVersion": "v5.5.1",
        "boardVersion": BOARD_VERSION,
        "resetReason": "Software reset via esp_restart",
        "runningPartition": "factory",
        "overheat_mode": 0,
        "overclockEnabled": 0,
        "display": "SSD1306 (128x32)",
        "rotation": 0,
        "invertscreen": 0,
        "displayTimeout": -1,
        "autofanspeed": 1,
        "fanspeed": fan_speed,
        "manualFanSpeed": 100,
        "minFanSpeed": 25,
        "temptarget": temp_target,
        "fanrpm": fan_rpm,
        "fan2rpm": 0,
        "statsFrequency": 0,
        "statsLimit": 0,
        "blockFound": 0,
        "blockHeight": random.randint(860_000, 940_000),
        "scriptsig": "...._i.F.W...ckpool./solo.ckpool.org/",
        "networkDifficulty": 146472570619930,
        "blockSignals": [],
        "coinbaseValueTotalSatoshis": 312500000,
        "coinbaseValueUserSatoshis": 0,
        "coinbaseOthersCount": 0,
        "coinbaseOthersValueSatoshis": 0,
        "miningPaused": False,
        "useNTP": True,
        "useCustomWWW": 0,
        "cpuUsage": round(random.uniform(8.0, 35.0), 2),
        "primaryPoolIndex": 0,
        "secondaryPoolIndex": 1,
        "useFallbackStratum": 0,
        "pools": [
            {
                "stratumProtocol": "SV1",
                "stratumURL": "public-pool.io",
                "stratumPort": 21496,
                "stratumUser": STRATUM_USER,
                "stratumSuggestedDifficulty": 1000,
                "stratumExtranonceSubscribe": False,
                "stratumTLS": 0,
                "stratumCert": "",
                "stratumDecodeCoinbase": False,
                "stratumShareWarning": True,
            },
            {
                "stratumProtocol": "SV1",
                "stratumURL": "solo.ckpool.org",
                "stratumPort": 3333,
                "stratumUser": STRATUM_USER,
                "stratumSuggestedDifficulty": 1000,
                "stratumExtranonceSubscribe": False,
                "stratumTLS": 0,
                "stratumCert": "",
                "stratumDecodeCoinbase": False,
                "stratumShareWarning": True,
            },
        ],
        "partitions": [
            {
                "label": "factory",
                "otaSlot": 0,
                "version": FIRMWARE_VERSION,
                "compileDate": datetime.now(timezone.utc).strftime("%b %d %Y"),
                "compileTime": "12:00:00",
                "isCurrent": True,
                "isFactory": True,
                "usagePercent": 42,
            }
        ],
        "hashrateMonitor": {
            "asics": [
                {
                    "total": hash_rate,
                    "domains": [
                        round(_jitter(domain_share, 12), 7),
                        round(_jitter(domain_share, 12), 7),
                        round(_jitter(domain_share, 12), 7),
                        round(_jitter(domain_share, 12), 7),
                    ],
                    "errorCount": random.randint(0, 2000),
                }
            ]
        },
    }


def build_asic_info() -> dict:
    return {
        "ASICModel": "BM1370",
        "deviceModel": "Gamma",
        "swarmColor": "purple",
        "asicCount": 1,
        "defaultFrequency": 490,
        "frequencyOptions": [400, 425, 450, 475, 485, 490, 500, 525, 550, 575],
        "defaultVoltage": 1200,
        "voltageOptions": [1100, 1150, 1200, 1250, 1300],
    }


@app.get("/api/system/info")
def system_info():
    return jsonify(build_system_info())


@app.get("/api/system/asic")
def system_asic():
    return jsonify(build_asic_info())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
