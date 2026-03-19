import RPi.GPIO as GPIO
import threading
import time
import json
import statistics
import paho.mqtt.client as mqtt

class MeteorDetector:

    # ---------------- CONFIG ----------------
    TRIG_PIN = 23
    ECHO_PIN = 24
    BUZZER = 18
    Y_LED = 25

    SPEED_OF_SOUND_CM_S = 34300
    TIMEOUT_S = 0.02
    SAMPLES = 5
    MEASURE_DELAY = 0.5

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_SENSOR = "nave/sensores/proximidad"

    def __init__(self):

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        GPIO.setup(self.BUZZER, GPIO.OUT)
        GPIO.setup(self.Y_LED, GPIO.OUT)

        GPIO.output(self.TRIG_PIN, GPIO.LOW)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()
        self.distance = 0
        self.level = "SAFE"

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- LECTURA BASE (ESTABLE) ----------------
    def read_distance_cm(self):

        GPIO.output(self.TRIG_PIN, GPIO.LOW)
        time.sleep(0.0002)

        GPIO.output(self.TRIG_PIN, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.TRIG_PIN, GPIO.LOW)

        start_time = time.time()

        # Esperar subida
        while GPIO.input(self.ECHO_PIN) == GPIO.LOW:
            if time.time() - start_time > self.TIMEOUT_S:
                return None

        pulse_start = time.time()

        # Esperar bajada
        while GPIO.input(self.ECHO_PIN) == GPIO.HIGH:
            if time.time() - pulse_start > self.TIMEOUT_S:
                return None

        pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start

        distance = (pulse_duration * self.SPEED_OF_SOUND_CM_S) / 2
        return distance

    # ---------------- LECTURA FILTRADA ----------------
    def get_filtered_distance(self):

        samples = []

        for _ in range(self.SAMPLES):
            value = self.read_distance_cm()
            if value is not None:
                samples.append(value)
            time.sleep(0.05)

        if samples:
            return round(statistics.median(samples), 2)
        return None

    # ---------------- CLASIFICACIÓN ----------------
    def classify_distance(self):

        if self.distance < 20:
            self.level = "CRITICAL"
        elif 20 <= self.distance <= 50:
            self.level = "NEAR"
        else:
            self.level = "FAR"

    # ---------------- ACTUADORES ----------------
    def control_outputs(self):

        # LED
        GPIO.output(self.Y_LED, self.level != "FAR")

        # Buzzer
        if self.level == "CRITICAL":
            GPIO.output(self.BUZZER, True)

        elif self.level == "NEAR":
            self.beep_pattern([0.1, 0.1, 0.1])

        elif self.level == "FAR":
            self.beep_pattern([0.2])

    def beep_pattern(self, beeps):

        def play(index=0):
            if index < len(beeps):
                GPIO.output(self.BUZZER, True)
                threading.Timer(beeps[index], lambda: stop(index)).start()
            else:
                GPIO.output(self.BUZZER, False)

        def stop(index):
            GPIO.output(self.BUZZER, False)
            threading.Timer(0.1, lambda: play(index + 1)).start()

        play()

    # ---------------- MQTT ----------------
    def publish_data(self):

        payload = [
            {
                "sensor": self.TOPIC_SENSOR,
                "value": self.distance,
                "level": self.level,
                "timestamp": self.get_timestamp()
            }
        ]

        self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))

    # ---------------- LOOP PRINCIPAL ----------------
    def loop(self):
        if self.stop_event.is_set():
            return

        distance = self.get_filtered_distance()

        if distance is not None:
            self.distance = distance
            self.classify_distance()
            self.control_outputs()
            self.publish_data()

            print(f" {self.distance} cm | {self.level}")
        else:
            print(" Lectura inválida")

        threading.Timer(self.MEASURE_DELAY, self.loop).start()

    # ---------------- LCD ----------------
    def get_meteor_status(self):
        return f"{self.distance}cm {self.level}"

    # ---------------- START ----------------
    def start(self):
        print(" MeteorDetector iniciado")
        self.loop()

    # ---------------- STOP ----------------
    def stop(self):
        print(" MeteorDetector detenido")
        self.stop_event.set()
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.disconnect()