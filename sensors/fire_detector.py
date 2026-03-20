import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class FireDetector:

    # ---------------- CONFIG ----------------
    MQ_PIN = 14
    LED = 4
    FAN1 = 0
    FAN2 = 0

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "nave/sensores/gas"
    TOPIC_ALERT = "nave/alertas/criticas"

    THRESHOLD = 1  # HIGH = peligro

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.MQ_PIN, GPIO.IN)
        GPIO.setup(self.LED, GPIO.OUT)
        GPIO.setup(self.FAN1, GPIO.OUT)
        GPIO.setup(self.FAN2, GPIO.OUT)

        # MQTT
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # Estado
        self.stop_event = threading.Event()
        self.fire_detected = False
        self.prev_state = None
        self.led_state = False

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- LED PARPADEO ----------------
    def led_loop(self):
        while not self.stop_event.is_set():

            if self.fire_detected:
                self.led_state = not self.led_state
                GPIO.output(self.LED, self.led_state)
                self.stop_event.wait(0.5)
            else:
                GPIO.output(self.LED, False)
                self.stop_event.wait(0.2)

    # ---------------- PUBLICAR SENSOR ----------------
    def publish_sensor(self, value):
        payload = {
            "sensor": self.TOPIC_SENSOR,
            "value": int(value),
            "status": "FIRE" if value else "SAFE",
            "timestamp": self.get_timestamp()
        }
        self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))

    # ---------------- PUBLICAR ALERTA ----------------
    def publish_alert(self, state):
        payload = {
            "type": "FIRE",
            "state": "ON" if state else "OFF",
            "timestamp": self.get_timestamp()
        }
        self.client.publish(self.TOPIC_ALERT, json.dumps(payload))

    # ---------------- LOOP PRINCIPAL ----------------
    def loop(self):
        while not self.stop_event.is_set():

            value = GPIO.input(self.MQ_PIN)
            self.fire_detected = (value == self.THRESHOLD)

            # Ventiladores
            GPIO.output(self.FAN1, self.fire_detected)
            GPIO.output(self.FAN2, self.fire_detected)

            # Publicar sensor SIEMPRE (cada 3s)
            self.publish_sensor(value)

            # Detectar cambio de estado
            if self.prev_state is None:
                self.prev_state = self.fire_detected

            if self.fire_detected != self.prev_state:
                print("CAMBIO DE ESTADO:", "FIRE" if self.fire_detected else "SAFE")
                self.publish_alert(self.fire_detected)
                self.prev_state = self.fire_detected

            self.stop_event.wait(3)

    # ---------------- ESTADO LCD ----------------
    def get_fire_status(self):
        return "FIRE!" if self.fire_detected else "SAFE"

    # ---------------- START ----------------
    def start(self):
        print("FireDetector iniciado")
        threading.Thread(target=self.loop, daemon=True).start()
        threading.Thread(target=self.led_loop, daemon=True).start()

    # ---------------- STOP ----------------
    def stop(self):
        print("FireDetector detenido")
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()