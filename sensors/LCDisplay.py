import time
import threading
import json
import paho.mqtt.client as mqtt
from rpi_lcd import LCD


class Display:

    # ---------------- MQTT ----------------
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_MSG = "nave/dashboard/msg"

    def __init__(self, systems):

        """
        systems = {
            "env": Environment,
            "meteor": MeteorDetector,
            "turret": Turret,
            "control": ControlPanel
        }
        """

        self.systems = systems

        # ---------------- LCD ----------------
        self.lcd = LCD(0x27, 1, 16, 2, True)
        self.lcd.clear()
        self.lcd.backlight(True)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.subscribe(self.TOPIC_MSG)
        self.client.loop_start()

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()

        self.view_index = 0
        self.last_message = ""
        self.last_update = 0
        self.period = 3.0

    # ---------------- MQTT RECEIVE ----------------
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.last_message = data.get("msg", "")
        except:
            self.last_message = msg.payload.decode()

    # ---------------- VISTAS ----------------
    def show_environment(self):
        env = self.systems["env"]
        text = env.get_env_status()

        self.lcd.clear()
        self.lcd.text("ENVIRONMENT", 1)
        self.lcd.text(text[:16], 2)

    def show_meteor(self):
        meteor = self.systems["meteor"]
        text = meteor.get_meteor_status()

        self.lcd.clear()
        self.lcd.text("METEOR", 1)
        self.lcd.text(text[:16], 2)

    def show_turret(self):
        turret = self.systems["turret"]
        angle = turret.get_turret_status()

        self.lcd.clear()
        self.lcd.text("TURRET", 1)
        self.lcd.text(f"Angle: {angle}", 2)

    def show_message(self):
        self.lcd.clear()
        self.lcd.text("MESSAGE", 1)
        self.lcd.text(self.last_message[:16], 2)

    # ---------------- EMERGENCIA ----------------
    def show_emergency(self):
        self.lcd.clear()
        self.lcd.text("!!! ALERT !!!", 1)
        self.lcd.text("SYSTEM HALTED", 2)

    # ---------------- LOOP ----------------
    def update(self):

        if self.stop_event.is_set():
            return

        control = self.systems["control"]

        # PRIORIDAD TOTAL
        if control.is_emergency():
            self.show_emergency()
            threading.Timer(1.0, self.update).start()
            return

        # Rotación cada 3 segundos
        if time.time() - self.last_update >= self.period:

            if self.view_index == 0:
                self.show_environment()

            elif self.view_index == 1:
                self.show_meteor()

            elif self.view_index == 2:
                self.show_turret()

            elif self.view_index == 3:
                self.show_message()

            self.view_index = (self.view_index + 1) % 4
            self.last_update = time.time()

        threading.Timer(0.5, self.update).start()

    # ---------------- START ----------------
    def start(self):
        print(" LCD iniciado")
        self.update()

    # ---------------- STOP ----------------
    def stop(self):
        print(" LCD detenido")
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()
        self.lcd.clear()