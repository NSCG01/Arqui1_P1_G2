import RPi.GPIO as GPIO
import threading
import time
import json
import statistics
import paho.mqtt.client as mqtt


class MeteorDetector:

    # ---------------- CONFIG ----------------
    TRIG_PIN = 8
    ECHO_PIN = 25

    SPEED_OF_SOUND_CM_S = 34300
    TIMEOUT_S = 0.02
    SAMPLES = 5

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_SENSOR = "nave/sensores/proximidad"
    TOPIC_ALERT = "nave/alertas/criticas"

    def __init__(self, esp32):
        self.esp32 = esp32

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)

        GPIO.output(self.TRIG_PIN, GPIO.LOW)

        # MQTT
        self.client = mqtt.Client()
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"⚠️ MeteorDetector MQTT error: {e}")

        # Estado
        self.stop_event = threading.Event()
        self.distance = 0
        self.level = "FAR"
        self.prev_level = None

        self.invalid_count = 0
        print("✅ MeteorDetector inicializado")

    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def read_distance_cm(self):
        GPIO.output(self.TRIG_PIN, False)
        time.sleep(0.00001)

        GPIO.output(self.TRIG_PIN, True)
        time.sleep(0.00001)
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
            time.sleep(0.01)

        if samples:
            return round(statistics.median(samples), 2)
        return None

    def classify(self):
        if self.distance < 20:
            self.level = "CRITICAL"
        elif 20 <= self.distance <= 50:
            self.level = "NEAR"
        else:
            self.level = "FAR"

    def update_buzzer_and_led(self):
        """Actualizar buzzer y LED en ESP32 según nivel"""
        if self.level == "CRITICAL":
            self.esp32.set_buzzer_meteor_pattern(3)  # Patrón continuo
            self.esp32.set_led_yellow_meteor(True)
        elif self.level == "NEAR":
            self.esp32.set_buzzer_meteor_pattern(2)  # 3 beeps rápidos
            self.esp32.set_led_yellow_meteor(True)
        else:  # FAR
            self.esp32.set_buzzer_meteor_pattern(1)  # 1 beep cada 2 segundos
            self.esp32.set_led_yellow_meteor(False)

    def publish_sensor(self):
        payload = {
            "distance": self.distance,
            "level": self.level,
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))
        except Exception as e:
            print(f"⚠️ MeteorDetector publish error: {e}")

    def publish_alert(self):
        payload = {
            "type": "METEOR",
            "level": self.level,
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_ALERT, json.dumps(payload))
        except Exception as e:
            print(f"⚠️ MeteorDetector alert error: {e}")

    def loop(self):
        while not self.stop_event.is_set():
            distance = self.get_filtered_distance()

            if distance is None:
                self.invalid_count += 1
                if self.invalid_count >= 3:
                    print("⚠️ METEOR: Lectura inválida persistente")
                self.stop_event.wait(0.5)
                continue

            self.invalid_count = 0
            self.distance = distance
            self.classify()

            # Actualizar buzzer y LED vía ESP32
            self.update_buzzer_and_led()

            # MQTT sensor
            self.publish_sensor()

            # Alerta solo si cambia a CRITICAL
            if self.level != self.prev_level:
                print(f"☄️ METEOR: {self.distance} cm | {self.level}")
                if self.level == "CRITICAL":
                    self.publish_alert()
                self.prev_level = self.level

            self.stop_event.wait(0.5)

    def get_meteor_status(self):
        return f"{self.distance}cm {self.level}"

    def start(self):
        print("✅ MeteorDetector iniciado (usando ESP32)")
        threading.Thread(target=self.loop, daemon=True).start()

    def stop(self):
        print("MeteorDetector detenido")
        self.stop_event.set()
        self.esp32.set_buzzer_meteor_pattern(0)  # Apagar buzzer
        self.esp32.set_led_yellow_meteor(False)
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass