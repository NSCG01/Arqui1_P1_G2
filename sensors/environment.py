import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt
import Adafruit_DHT


class Environment:

    # ---------------- CONFIG ----------------
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 13
    SOIL_PIN = 22

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_TEMP = "nave/sensores/temperatura"
    TOPIC_AMBIENTE = "nave/sensores/ambiente"
    TOPIC_SOIL = "nave/sensores/humedad"
    TOPIC_ALERT = "nave/alertas/criticas"

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.SOIL_PIN, GPIO.IN)

        # MQTT
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # Estado
        self.stop_event = threading.Event()

        self.temperature = 0
        self.humidity = 0
        self.soil = 0

        self.prev_alert_state = None

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- MQTT ----------------
    def publish(self, topic, payload):
        self.client.publish(topic, json.dumps(payload))

    def publish_all(self):
        ts = self.get_timestamp()

        self.publish(self.TOPIC_TEMP, {
            "value": self.temperature,
            "timestamp": ts
        })

        self.publish(self.TOPIC_AMBIENTE, {
            "value": self.humidity,
            "timestamp": ts
        })

        self.publish(self.TOPIC_SOIL, {
            "value": "DRY" if self.soil else "WET",
            "raw": int(self.soil),
            "timestamp": ts
        })

    def publish_alert(self, alerts):
        payload = {
            "type": "ENVIRONMENT",
            "alerts": alerts,
            "timestamp": self.get_timestamp()
        }
        self.publish(self.TOPIC_ALERT, payload)

    # ---------------- ALERTAS ----------------
    def check_alerts(self):

        alerts = []

        if self.temperature > 35:
            alerts.append("HIGH_TEMP")
        elif self.temperature < 10:
            alerts.append("LOW_TEMP")

        if self.humidity < 20:
            alerts.append("LOW_HUM")
        elif self.humidity > 80:
            alerts.append("HIGH_HUM")

        return alerts

    # ---------------- LOOP PRINCIPAL ----------------
    def loop(self):

        while not self.stop_event.is_set():

            # ---- DHT11 ----
            hum, temp = Adafruit_DHT.read_retry(self.DHT_SENSOR, self.DHT_PIN)

            if hum is None or temp is None:
                print("Error leyendo DHT11")
            else:
                self.temperature = temp
                self.humidity = hum

            # ---- YL-69 ----
            self.soil = GPIO.input(self.SOIL_PIN)

            # ---- PUBLICAR ----
            self.publish_all()

            # ---- ALERTAS ----
            alerts = self.check_alerts()

            if alerts != self.prev_alert_state:
                if alerts:
                    print("ALERTAS:", alerts)
                    self.publish_alert(alerts)

                self.prev_alert_state = alerts

            self.stop_event.wait(3)

    # ---------------- LCD ----------------
    def get_env_status(self):
        soil_status = "DRY" if self.soil else "WET"
        return f"T:{self.temperature}C H:{self.humidity}% S:{soil_status}"

    # ---------------- START ----------------
    def start(self):
        print("Environment iniciado")
        threading.Thread(target=self.loop, daemon=True).start()

    # ---------------- STOP ----------------
    def stop(self):
        print("Environment detenido")
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()