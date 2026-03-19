import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class ControlPanel:

    # ---------------- CONFIG ----------------
    EMERGENCY_BUTTON = 11
    LED_STATUS = 9

    BUZZER_METEOR = 17
    BUZZER_TURRET = 25

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_ALERT = "nave/alertas/criticas"

    DEBOUNCE_TIME = 0.3

    def __init__(self, systems):

        self.systems = systems

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.EMERGENCY_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_STATUS, GPIO.OUT)

        GPIO.setup(self.BUZZER_FIRE, GPIO.OUT)
        GPIO.setup(self.BUZZER_TURRET, GPIO.OUT)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.loop_start()

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()

        self.emergency_active = False
        self.last_button_state = 1
        self.last_press_time = 0

    # ---------------- TIMESTAMP ----------------
    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- MQTT ----------------
    def publish_alert(self, state):
        payload = [
            {
                "system": "control_panel",
                "event": "EMERGENCY",
                "state": state,
                "timestamp": self.get_timestamp()
            }
        ]
        self.client.publish(self.TOPIC_ALERT, json.dumps(payload))

    # ---------------- LED SISTEMA ----------------
    def system_led(self):
        if self.stop_event.is_set():
            return

        GPIO.output(self.LED_STATUS, not self.emergency_active)

        threading.Timer(1.0, self.system_led).start()

    # ---------------- BOTÓN ----------------
    def button_loop(self):
        if self.stop_event.is_set():
            return

        current = GPIO.input(self.EMERGENCY_BUTTON)
        now = time.time()

        # FLANCO + DEBOUNCE
        if self.last_button_state == 1 and current == 0:
            if now - self.last_press_time > self.DEBOUNCE_TIME:
                self.last_press_time = now
                self.handle_press()

        self.last_button_state = current

        threading.Timer(0.05, self.button_loop).start()

    # ---------------- LÓGICA ----------------
    def handle_press(self):
        if not self.emergency_active:
            self.activate_emergency()
        else:
            self.deactivate_emergency()

    # ---------------- EMERGENCIA ----------------
    def activate_emergency(self):
        print("🚨 EMERGENCIA ACTIVADA")
        self.emergency_active = True

        # detener sistemas
        for name, system in self.systems.items():
            try:
                system.stop()
            except Exception as e:
                print(f"Error deteniendo {name}: {e}")

        GPIO.output(self.BUZZER_FIRE, True)
        GPIO.output(self.BUZZER_TURRET, True)
        GPIO.output(self.LED_STATUS, False)

        self.publish_alert("ON")

    def deactivate_emergency(self):
        print("EMERGENCIA DESACTIVADA")
        self.emergency_active = False

        GPIO.output(self.BUZZER_FIRE, False)
        GPIO.output(self.BUZZER_TURRET, False)
        GPIO.output(self.LED_STATUS, True)

        # reiniciar sistemas
        for name, system in self.systems.items():
            try:
                system.start()
            except Exception as e:
                print(f"Error iniciando {name}: {e}")

        self.publish_alert("OFF")

    # ---------------- LCD ----------------
    def get_emergency_status(self):
        return "!!! EMERGENCY !!!" if self.emergency_active else None

    def is_emergency(self):
        return self.emergency_active

    # ---------------- START ----------------
    def start(self):
        print("ControlPanel iniciado")
        GPIO.output(self.LED_STATUS, True)
        self.system_led()
        self.button_loop()

    # ---------------- STOP ----------------
    def stop(self):
        print("ControlPanel detenido")
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()