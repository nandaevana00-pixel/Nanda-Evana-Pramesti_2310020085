import paho.mqtt.client as mqtt
import json, time, random
from datetime import datetime

BROKER = "broker.hivemq.com"
PORT = 1883
PREFIX = "iotkampus/2310020085"
TOPIC_SENSOR = f"{PREFIX}/iot/sensor"
TOPIC_KONTROL = f"{PREFIX}/iot/kontrol"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ESP32-Simulator")
client.connect(BROKER, PORT, 60)
client.loop_start()

print("ESP32 Simulator berjalan... Ctrl+C untuk stop")

try:
    while True:
        data = {
            "suhu": round(random.uniform(25, 32), 1),
            "kelembaban": round(random.uniform(55, 80), 1),
            "timestamp": datetime.now().isoformat()
        }
        client.publish(TOPIC_SENSOR, json.dumps(data))
        print(f"-> Publish: {data}")
        time.sleep(3)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()