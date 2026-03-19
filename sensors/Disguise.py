import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt

class Disguise:

    # ---------------- CONFIG ----------------
    S0, S1, S2, S3, OUT = 6, 13, 19, 26, 21
    R_PIN, G_PIN, B_PIN = 2, 3, 10
    BLUE_LED = 12

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "nave/sensores/color"

    SEQUENCE_TARGET = ["RED", "YELLOW", "BLUE"]

    def __init__(self):

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup([self.S0, self.S1, self.S2, self.S3], GPIO.OUT)
        GPIO.setup(self.OUT, GPIO.IN)

        GPIO.setup(self.R_PIN, GPIO.OUT)
        GPIO.setup(self.G_PIN, GPIO.OUT)
        GPIO.setup(self.B_PIN, GPIO.OUT)
        GPIO.setup(self.BLUE_LED, GPIO.OUT)

        # Escala frecuencia
        GPIO.output(self.S0, True)
        GPIO.output(self.S1, False)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # ---------------- ESTADO ----------------
        self.detected_sequence = []
        self.camouflage_active = False
        self.stop_event = threading.Event()

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- RGB LED ----------------
    def set_color(self, r, g, b):
        GPIO.output(self.R_PIN, r)
        GPIO.output(self.G_PIN, g)
        GPIO.output(self.B_PIN, b)

    # ---------------- CAMUFLAJE ----------------
    def activate_camouflage(self):
        self.camouflage_active = True
        GPIO.output(self.BLUE_LED, True)
        self.sequence_loop()

    def deactivate_camouflage(self):
        self.camouflage_active = False
        self.set_color(0, 0, 0)
        GPIO.output(self.BLUE_LED, False)

    def sequence_loop(self):
        if not self.camouflage_active or self.stop_event.is_set():
            return

        colors = [
            (1,0,0),  # rojo
            (1,1,0),  # amarillo
            (0,0,1)   # azul
        ]

        def play(index=0):
            if not self.camouflage_active or self.stop_event.is_set():
                self.set_color(0,0,0)
                return

            self.set_color(*colors[index])
            threading.Timer(1.0, lambda: play((index+1)%3)).start()

        play()

    # ---------------- MEDICIÓN ----------------
    def measure_channel(self, s2, s3):
        GPIO.output(self.S2, s2)
        GPIO.output(self.S3, s3)

        start = time.time()
        count = 0

        while time.time() - start < 0.1:
            if GPIO.input(self.OUT) == 0:
                count += 1
                while GPIO.input(self.OUT) == 0:
                    pass

        return count

    def classify_color(self, r, g, b):
        if r > g and r > b:
            return "RED"
        elif g > r and g > b:
            return "GREEN"
        elif b > r and b > g:
            return "BLUE"
        elif r > 50 and g > 50:
            return "YELLOW"
        return "UNKNOWN"

    # ---------------- MQTT ----------------
    def publish_sensor(self, color):
        payload = [
            {
                "sensor": self.TOPIC_SENSOR,
                "value": color,
                "sequence": self.detected_sequence,
                "camouflage": self.camouflage_active,
                "timestamp": self.get_timestamp()
            }
        ]

        self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))

    # ---------------- SECUENCIA ----------------
    def process_sequence(self, color):

        if color == "UNKNOWN":
            return

        self.detected_sequence.append(color)

        if len(self.detected_sequence) > 3:
            self.detected_sequence.pop(0)

        if self.detected_sequence == self.SEQUENCE_TARGET:
            if not self.camouflage_active:
                print("CAMUFLAJE ACTIVADO")
                self.activate_camouflage()
        else:
            if self.camouflage_active:
                print("CAMUFLAJE DESACTIVADO")
                self.deactivate_camouflage()

        # Publicar SIEMPRE estado
        self.publish_sensor(color)

    # ---------------- LOOP SENSOR ----------------
    def read_color(self):
        if self.stop_event.is_set():
            return

        red = self.measure_channel(False, False)
        blue = self.measure_channel(False, True)
        green = self.measure_channel(True, True)

        color = self.classify_color(red, green, blue)

        self.process_sequence(color)

        threading.Timer(1.5, self.read_color).start()

    # ---------------- START ----------------
    def start(self):
        print("Disguise iniciado")
        self.read_color()

    # ---------------- STOP ----------------
    def stop(self):
        print("Disguise detenido")
        self.stop_event.set()
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.disconnect()