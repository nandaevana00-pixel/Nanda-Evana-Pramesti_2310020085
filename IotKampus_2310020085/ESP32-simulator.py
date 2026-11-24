import json
import random
import time
import requests
import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ESP32-simulator")
client.connect("localhost", 1883, 60)
client.loop_start()

API_SUHU_URL = "http://localhost:5000/api/suhu"

while True:
    payload = {
        "device_id": "ESP32-simulator",
        "temperature": round(random.uniform(28.0, 40.0), 2)
    }

    #kirim ke broker MQTT (gunakanjson.dumps agar menjadi string JSON)
    client.publish("sensor/suhu", json.dumps(payload))

    #kirim ke Flask API untuk cek threshold & notifikasi
    
    try:
        res = requests.post(API_SUHU_URL, json=payload, timeout=3)
        print("dikirim:", payload, "|respon API:", res.json())
    except Exception as e: 
        print("Gagal kirim ke API:", e)

    time.sleep(2)