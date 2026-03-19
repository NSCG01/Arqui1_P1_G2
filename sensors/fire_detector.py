import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt

class FireDetector:

    # ---------------- CONFIG ----------------
    MQ_PIN = 14
    LED = 15
    FAN1 = 18
    FAN2 = 23

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "nave/sensores/gas"

    THRESHOLD = 1  # HIGH = peligro

    def __init__(self):

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.MQ_PIN, GPIO.IN)
        GPIO.setup(self.LED, GPIO.OUT)
        GPIO.setup(self.FAN1, GPIO.OUT)
        GPIO.setup(self.FAN2, GPIO.OUT)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()
        self.fire_detected = False
        self.led_state = False

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- LED BLINK ----------------
    def blink_led(self):
        if self.stop_event.is_set():
            return

        if self.fire_detected:
            self.led_state = not self.led_state
            GPIO.output(self.LED, self.led_state)
        else:
            GPIO.output(self.LED, False)

        threading.Timer(0.5, self.blink_led).start()

    # ---------------- PUBLICAR ----------------
    def publish_sensor(self, value):
        payload = [
            {
                "sensor": self.TOPIC_SENSOR,
                "value": int(value),
                "timestamp": self.get_timestamp()
            }
        ]

        self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))

    # ---------------- LECTURA ----------------
    def read_sensor(self):
        if self.stop_event.is_set():
            return

        value = GPIO.input(self.MQ_PIN)

        # Estado interno
        self.fire_detected = (value == self.THRESHOLD)

        if self.fire_detected:
            print("GAS DETECTADO")

        # Ventiladores
        GPIO.output(self.FAN1, self.fire_detected)
        GPIO.output(self.FAN2, self.fire_detected)

        # Publicar SIEMPRE
        self.publish_sensor(value)

        threading.Timer(1.0, self.read_sensor).start()

    # ---------------- ESTADO ----------------
    def get_fire_status(self):
        return "FIRE!" if self.fire_detected else "SAFE"

    # ---------------- START ----------------
    def start(self):
        print("FireDetector iniciado")
        self.blink_led()
        self.read_sensor()

    # ---------------- STOP ----------------
    def stop(self):
        print("FireDetector detenido")
        self.stop_event.set()
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.disconnect()