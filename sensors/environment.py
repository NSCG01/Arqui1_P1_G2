import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt
import Adafruit_DHT

class Environment:

    # ---------------- CONFIG ----------------
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 4
    SOIL_PIN = 27  # YL-69 digital

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    # Topics
    TOPIC_TEMP = "nave/sensores/temperatura"
    TOPIC_AMBIENTE = "nave/sensores/ambiente"
    TOPIC_SOIL = "nave/sensores/humedad"

    def __init__(self):

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.SOIL_PIN, GPIO.IN)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()
        self.temperature = 0
        self.humidity = 0
        self.soil = 0  # 0 húmedo, 1 seco

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- MQTT ----------------
    def publish_temperature(self):
        payload = [
            {
                "sensor": self.TOPIC_TEMP,
                "value": self.temperature,
                "timestamp": self.get_timestamp()
            }
        ]
        self.client.publish(self.TOPIC_TEMP, json.dumps(payload))

    def publish_ambiente(self):
        payload = [
            {
                "sensor": self.TOPIC_AMBIENTE,
                "value": self.humidity,
                "timestamp": self.get_timestamp()
            }
        ]
        self.client.publish(self.TOPIC_AMBIENTE, json.dumps(payload))

    def publish_soil(self):
        payload = [
            {
                "sensor": self.TOPIC_SOIL,
                "value": "DRY" if self.soil else "WET",
                "timestamp": self.get_timestamp()
            }
        ]
        self.client.publish(self.TOPIC_SOIL, json.dumps(payload))

    # ---------------- LECTURA ----------------
    def read_environment(self):
        if self.stop_event.is_set():
            return

        # DHT11
        hum, temp = Adafruit_DHT.read_retry(self.DHT_SENSOR, self.DHT_PIN)

        if hum is not None and temp is not None:
            self.temperature = temp
            self.humidity = hum

        #  YL-69
        self.soil = GPIO.input(self.SOIL_PIN)

        # Publicar SIEMPRE
        self.publish_temperature()
        self.publish_ambiente()
        self.publish_soil()

        threading.Timer(3.0, self.read_environment).start()

    # ---------------- ESTADO ----------------
    def get_env_status(self):
        soil_status = "DRY" if self.soil else "WET"
        return f"T:{self.temperature}C H:{self.humidity}% S:{soil_status}"

    # ---------------- START ----------------
    def start(self):
        print(" Environment iniciado (DHT11 + YL-69)")
        self.read_environment()

    # ---------------- STOP ----------------
    def stop(self):
        print(" Environment detenido")
        self.stop_event.set()
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.disconnect()