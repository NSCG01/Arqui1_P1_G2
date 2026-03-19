import threading
import time
import json
import paho.mqtt.client as mqtt
from rpi_lcd import LCD


class Display:

    # ---------------- MQTT ----------------
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_MSG = "nave/control/mensajes"

    def __init__(self, systems):

        self.systems = systems

        # ---------------- LCD ----------------
        self.lcd = LCD(0x27, 1, 16, 2, True)
        self.lcd.clear()
        self.lcd.backlight(True)

        # ---------------- MQTT ----------------
        self.client = mqtt.Client()
        self.client.on_message = self.on_message

        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.subscribe(self.TOPIC_MSG)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT error: {e}")

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()

        self.view_index = 0
        self.last_message = ""
        self.message_time = 0

        self.last_update = 0

    # ---------------- TIMESTAMP ----------------
    def now(self):
        return time.time()

    # ---------------- MQTT RECEIVE ----------------
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.last_message = data.get("msg", "")
        except Exception:
            try:
                self.last_message = msg.payload.decode()
            except:
                self.last_message = "MSG ERROR"

        self.message_time = self.now()

    # ---------------- UTILIDADES ----------------
    def safe_text(self, text):
        return text if text else ""

    def display_two_lines(self, line1, line2):

        try:
            self.lcd.clear()
            self.lcd.text(line1[:16], 1)
            self.lcd.text(line2[:16], 2)
        except Exception as e:
            print(f"LCD error: {e}")

    def scroll_text(self, title, text):

        text = self.safe_text(text)

        if len(text) <= 16:
            self.display_two_lines(title, text)
            return

        # scroll dinámico sin sleep
        window = text[:16]
        self.display_two_lines(title, window)

        def scroll_step(index=0):
            if self.stop_event.is_set():
                return

            if index + 16 <= len(text):
                window = text[index:index+16]
                self.display_two_lines(title, window)
                threading.Timer(0.4, lambda: scroll_step(index + 1)).start()

        scroll_step()

    # ---------------- VISTAS ----------------
    def show_environment(self):
        try:
            env = self.systems["env"]
            text = env.get_env_status()
            self.display_two_lines("ENVIRONMENT", text)
        except Exception as e:
            print(f"ENV error: {e}")

    def show_meteor(self):
        try:
            meteor = self.systems["meteor"]
            text = meteor.get_meteor_status()
            self.display_two_lines("METEOR", text)
        except Exception as e:
            print(f"METEOR error: {e}")

    def show_turret(self):
        try:
            turret = self.systems["turret"]
            angle = turret.get_turret_status()
            self.display_two_lines("TURRET", f"{angle}")
        except Exception as e:
            print(f"TURRET error: {e}")

    def show_message(self):
        self.scroll_text("MESSAGE", self.last_message)

    # ---------------- EMERGENCIA ----------------
    def show_emergency(self):
        self.display_two_lines("!!! ALERT !!!", "SYSTEM HALTED")

    # ---------------- LOOP ----------------
    def update(self):

        if self.stop_event.is_set():
            return

        try:
            control = self.systems["control"]
        except:
            control = None

        # PRIORIDAD TOTAL
        if control and control.is_emergency():
            self.show_emergency()
            threading.Timer(1.0, self.update).start()
            return

        now = self.now()

        # -------- MENSAJE PRIORIDAD --------
        if self.last_message and (now - self.message_time < 5):
            if now - self.last_update >= 5:
                self.show_message()
                self.last_update = now

        # -------- VISTAS NORMALES --------
        elif now - self.last_update >= 3:

            if self.view_index == 0:
                self.show_environment()

            elif self.view_index == 1:
                self.show_meteor()

            elif self.view_index == 2:
                self.show_turret()

            self.view_index = (self.view_index + 1) % 3
            self.last_update = now

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