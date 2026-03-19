import RPi.GPIO as GPIO
import threading
import time
import json
import statistics
import paho.mqtt.client as mqtt


class MeteorDetector:

    # ---------------- CONFIG ----------------
    TRIG_PIN = 7
    ECHO_PIN = 8
    BUZZER = 17
    Y_LED = 27

    SPEED_OF_SOUND_CM_S = 34300
    TIMEOUT_S = 0.02
    SAMPLES = 5

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_SENSOR = "nave/sensores/proximidad"
    TOPIC_ALERT = "nave/alertas/criticas"

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        GPIO.setup(self.BUZZER, GPIO.OUT)
        GPIO.setup(self.Y_LED, GPIO.OUT)

        GPIO.output(self.TRIG_PIN, GPIO.LOW)

        # MQTT
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # Estado
        self.stop_event = threading.Event()
        self.distance = 0
        self.level = "FAR"
        self.prev_level = None

        self.invalid_count = 0

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- LECTURA ----------------
    def read_distance_cm(self):

        GPIO.output(self.TRIG_PIN, False)
        start = time.time()

        # Trigger
        GPIO.output(self.TRIG_PIN, True)
        GPIO.output(self.TRIG_PIN, False)

        start_time = time.time()

        while GPIO.input(self.ECHO_PIN) == 0:
            if time.time() - start_time > self.TIMEOUT_S:
                return None

        pulse_start = time.time()

        while GPIO.input(self.ECHO_PIN) == 1:
            if time.time() - pulse_start > self.TIMEOUT_S:
                return None

        pulse_end = time.time()
        duration = pulse_end - pulse_start

        return (duration * self.SPEED_OF_SOUND_CM_S) / 2

    def get_filtered_distance(self):

        samples = []

        for _ in range(self.SAMPLES):
            d = self.read_distance_cm()
            if d is not None:
                samples.append(d)

        if samples:
            return round(statistics.median(samples), 2)

        return None

    # ---------------- CLASIFICACIÓN ----------------
    def classify(self):

        if self.distance < 20:
            self.level = "CRITICAL"
        elif 20 <= self.distance <= 50:
            self.level = "NEAR"
        else:
            self.level = "FAR"

    # ---------------- BUZZER ----------------
    def buzzer_loop(self):

        while not self.stop_event.is_set():

            if self.level == "CRITICAL":
                GPIO.output(self.BUZZER, True)
                self.stop_event.wait(0.1)

            elif self.level == "NEAR":
                for _ in range(3):
                    GPIO.output(self.BUZZER, True)
                    self.stop_event.wait(0.1)
                    GPIO.output(self.BUZZER, False)
                    self.stop_event.wait(0.1)
                self.stop_event.wait(1)

            else:  # FAR
                GPIO.output(self.BUZZER, True)
                self.stop_event.wait(0.2)
                GPIO.output(self.BUZZER, False)
                self.stop_event.wait(2)

    # ---------------- MQTT ----------------
    def publish_sensor(self):
        payload = {
            "distance": self.distance,
            "level": self.level,
            "timestamp": self.get_timestamp()
        }
        self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))

    def publish_alert(self):
        payload = {
            "type": "METEOR",
            "level": self.level,
            "timestamp": self.get_timestamp()
        }
        self.client.publish(self.TOPIC_ALERT, json.dumps(payload))

    # ---------------- LOOP ----------------
    def loop(self):

        while not self.stop_event.is_set():

            distance = self.get_filtered_distance()

            if distance is None:
                self.invalid_count += 1

                if self.invalid_count >= 3:
                    print("Lectura inválida persistente")
                self.stop_event.wait(0.5)
                continue

            self.invalid_count = 0
            self.distance = distance

            self.classify()

            # LED
            GPIO.output(self.Y_LED, self.level != "FAR")

            # MQTT sensor
            self.publish_sensor()

            # ALERTA SOLO SI CAMBIA
            if self.level != self.prev_level:
                print(f"{self.distance} cm | {self.level}")

                if self.level == "CRITICAL":
                    self.publish_alert()

                self.prev_level = self.level

            self.stop_event.wait(0.5)

    # ---------------- LCD ----------------
    def get_meteor_status(self):
        return f"{self.distance}cm {self.level}"

    # ---------------- START ----------------
    def start(self):
        print("MeteorDetector iniciado")

        threading.Thread(target=self.loop, daemon=True).start()
        threading.Thread(target=self.buzzer_loop, daemon=True).start()

    # ---------------- STOP ----------------
    def stop(self):
        print("MeteorDetector detenido")
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()