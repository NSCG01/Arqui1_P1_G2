import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt

import board
import neopixel


class Disguise:

    # ---------------- CONFIG ----------------
    S0, S1, S2, S3, OUT = 19, 26, 16, 20, 21

    BLUE_LED = 12  # indicador físico

    # WS2812B
    PIXEL_PIN = board.D18   # GPIO18 obligatorio
    NUM_PIXELS = 8          # ajusta a tu tira

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "nave/sensores/color"
    TOPIC_ALERT = "nave/alertas/criticas"

    SEQUENCE_TARGET = ["RED", "YELLOW", "BLUE"]

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup([self.S0, self.S1, self.S2, self.S3], GPIO.OUT)
        GPIO.setup(self.OUT, GPIO.IN)

        GPIO.setup(self.BLUE_LED, GPIO.OUT)

        # Escala frecuencia TCS3200
        GPIO.output(self.S0, True)
        GPIO.output(self.S1, False)

        # ---------------- WS2812B ----------------
        self.pixels = neopixel.NeoPixel(
            self.PIXEL_PIN,
            self.NUM_PIXELS,
            brightness=0.5,
            auto_write=False
        )

        # MQTT
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # Estado
        self.detected_sequence = []
        self.camouflage_active = False
        self.prev_state = False

        self.stop_event = threading.Event()

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- CONTROL LED STRIP ----------------
    def set_color(self, r, g, b):
        # WS2812B usa formato GRB
        for i in range(self.NUM_PIXELS):
            self.pixels[i] = (g, r, b)
        self.pixels.show()

    # ---------------- LOOP CAMUFLAJE ----------------
    def camouflage_loop(self):

        colors = [
            (255, 0, 0),     # RED
            (255, 255, 0),   # YELLOW
            (0, 0, 255)      # BLUE
        ]

        index = 0

        while not self.stop_event.is_set():

            if self.camouflage_active:
                self.set_color(*colors[index])
                index = (index + 1) % 3
                self.stop_event.wait(1)
            else:
                self.set_color(0, 0, 0)
                self.stop_event.wait(0.2)

    # ---------------- MEDICIÓN ----------------
    def measure_channel(self, s2, s3):

        GPIO.output(self.S2, s2)
        GPIO.output(self.S3, s3)

        count = 0
        start = time.time()

        while time.time() - start < 0.1:
            if GPIO.input(self.OUT) == 0:
                count += 1

                timeout = time.time()
                while GPIO.input(self.OUT) == 0:
                    if time.time() - timeout > 0.002:
                        break

        return count

    # ---------------- CLASIFICACIÓN ----------------
    def classify_color(self, r, g, b):
        if r > g and r > b:
            return "RED"
        elif g > r and g > b:
            return "GREEN"
        elif b > r and b > g:
            return "BLUE"
        elif r > b and g > b:
            return "YELLOW"
        return "UNKNOWN"

    # ---------------- MQTT SENSOR ----------------
    def publish_sensor(self, color):
        payload = {
            "sensor": self.TOPIC_SENSOR,
            "color": color,
            "sequence": self.detected_sequence,
            "camouflage": self.camouflage_active,
            "timestamp": self.get_timestamp()
        }
        self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))

    # ---------------- MQTT ALERT ----------------
    def publish_alert(self, state):
        payload = {
            "type": "CAMOUFLAGE",
            "state": "ON" if state else "OFF",
            "timestamp": self.get_timestamp()
        }
        self.client.publish(self.TOPIC_ALERT, json.dumps(payload))

    # ---------------- SECUENCIA ----------------
    def process_sequence(self, color):

        if color == "UNKNOWN":
            return

        self.detected_sequence.append(color)

        if len(self.detected_sequence) > 3:
            self.detected_sequence.pop(0)

        if self.detected_sequence == self.SEQUENCE_TARGET:
            self.camouflage_active = True
        else:
            self.camouflage_active = False

        # Cambio de estado
        if self.camouflage_active != self.prev_state:
            print("CAMOUFLAJE:", "ON" if self.camouflage_active else "OFF")
            self.publish_alert(self.camouflage_active)
            GPIO.output(self.BLUE_LED, self.camouflage_active)
            self.prev_state = self.camouflage_active

        self.publish_sensor(color)

    # ---------------- LOOP SENSOR ----------------
    def sensor_loop(self):

        while not self.stop_event.is_set():

            red = self.measure_channel(False, False)
            blue = self.measure_channel(False, True)
            green = self.measure_channel(True, True)

            color = self.classify_color(red, green, blue)

            self.process_sequence(color)

            self.stop_event.wait(1.5)

    # ---------------- START ----------------
    def start(self):
        print("Disguise iniciado")

        threading.Thread(target=self.sensor_loop, daemon=True).start()
        threading.Thread(target=self.camouflage_loop, daemon=True).start()

    # ---------------- STOP ----------------
    def stop(self):
        print("Disguise detenido")
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()
        self.set_color(0, 0, 0)