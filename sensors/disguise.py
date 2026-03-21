import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt
import board
import neopixel


class Disguise:

    S0, S1, S2, S3, OUT = 7, 12, 16, 20, 21

    PIXEL_PIN = board.D18
    NUM_PIXELS = 8

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "nave/sensores/color"
    TOPIC_ALERT = "nave/alertas/criticas"

    SEQUENCE_TARGET = ["RED", "YELLOW", "BLUE"]

    def __init__(self, esp32):
        self.esp32 = esp32

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup([self.S0, self.S1, self.S2, self.S3], GPIO.OUT)
        GPIO.setup(self.OUT, GPIO.IN)

        GPIO.output(self.S0, True)
        GPIO.output(self.S1, False)

        self.pixels = neopixel.NeoPixel(
            self.PIXEL_PIN,
            self.NUM_PIXELS,
            brightness=0.5,
            auto_write=False
        )

        self.client = mqtt.Client()
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f" Disguise MQTT error: {e}")

        self.detected_sequence = []
        self.camouflage_active = False
        self.prev_state = False

        self.stop_event = threading.Event()
        print("Disguise inicializado")

    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def set_color(self, r, g, b):
        for i in range(self.NUM_PIXELS):
            self.pixels[i] = (g, r, b)
        self.pixels.show()

    def camouflage_loop(self):
        colors = [(255, 0, 0), (255, 255, 0), (0, 0, 255)]
        index = 0

        while not self.stop_event.is_set():
            if self.camouflage_active:
                self.set_color(*colors[index])
                index = (index + 1) % 3
                time.sleep(1)
            else:
                self.set_color(0, 0, 0)
                time.sleep(0.2)

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

    def publish_sensor(self, color):
        payload = {
            "sensor": self.TOPIC_SENSOR,
            "color": color,
            "sequence": self.detected_sequence,
            "camouflage": self.camouflage_active,
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))
        except Exception as e:
            print(f"Disguise publish error: {e}")

    def publish_alert(self, state):
        payload = {
            "type": "CAMOUFLAGE",
            "state": "ON" if state else "OFF",
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_ALERT, json.dumps(payload))
        except Exception as e:
            print(f" Disguise alert error: {e}")

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

        if self.camouflage_active != self.prev_state:
            print("CAMOUFLAJE:", "ON" if self.camouflage_active else "OFF")
            self.publish_alert(self.camouflage_active)
            # Controlar LED azul vía ESP32
            self.esp32.set_led_blue_camo(self.camouflage_active)
            self.prev_state = self.camouflage_active

        self.publish_sensor(color)

    def sensor_loop(self):
        while not self.stop_event.is_set():
            red = self.measure_channel(False, False)
            blue = self.measure_channel(False, True)
            green = self.measure_channel(True, True)

            color = self.classify_color(red, green, blue)

            self.process_sequence(color)

            time.sleep(1.5)

    def start(self):
        print("Disguise iniciado (LED azul vía ESP32)")
        threading.Thread(target=self.sensor_loop, daemon=True).start()
        threading.Thread(target=self.camouflage_loop, daemon=True).start()

    def stop(self):
        print("Disguise detenido")
        self.stop_event.set()
        self.esp32.set_led_blue_camo(False)
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass
        self.set_color(0, 0, 0)