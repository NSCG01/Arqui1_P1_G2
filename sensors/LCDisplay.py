import threading
import time
import json
import paho.mqtt.client as mqtt
from rpi_lcd import LCD


class Display:

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_MSG = "nave/control/mensajes"

    def __init__(self, systems):
        self.systems = systems

        try:
            self.lcd = LCD(0x27, 1, 16, 2, True)
            self.lcd.clear()
            self.lcd.backlight(True)
            print(" LCD inicializado")
        except Exception as e:
            print(f" LCD error: {e}")
            self.lcd = None

        self.client = mqtt.Client()
        self.client.on_message = self.on_message

        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.subscribe(self.TOPIC_MSG)
            self.client.loop_start()
        except Exception as e:
            print(f"Display MQTT error: {e}")

        self.stop_event = threading.Event()

        self.view_index = 0
        self.last_message = ""
        self.message_time = 0
        self.last_update = 0
        
        print(" Display inicializado")

    def now(self):
        return time.time()

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.last_message = data.get("msg", "")
            print(f" LCD recibe mensaje: {self.last_message}")
        except Exception:
            try:
                self.last_message = msg.payload.decode()
            except:
                self.last_message = "MSG ERROR"

        self.message_time = self.now()

    def safe_text(self, text):
        return text if text else ""

    def display_two_lines(self, line1, line2):
        if self.lcd is None:
            print(f"LCD (simulado): {line1[:16]} | {line2[:16]}")
            return
            
        try:
            self.lcd.clear()
            self.lcd.text(line1[:16], 1)
            self.lcd.text(line2[:16], 2)
            print(f"LCD: {line1[:16]} | {line2[:16]}")
        except Exception as e:
            print(f"LCD error: {e}")

    def scroll_text(self, title, text):
        text = self.safe_text(text)

        if len(text) <= 16:
            self.display_two_lines(title, text)
            return

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

    def show_environment(self):
        try:
            env = self.systems["env"]
            text = env.get_env_status()
            self.display_two_lines("ENVIRONMENT", text)
        except Exception as e:
            print(f"ENV error: {e}")
            self.display_two_lines("ENVIRONMENT", "ERROR")

    def show_meteor(self):
        try:
            meteor = self.systems["meteor"]
            text = meteor.get_meteor_status()
            self.display_two_lines("METEOR", text)
        except Exception as e:
            print(f"METEOR error: {e}")
            self.display_two_lines("METEOR", "ERROR")

    def show_turret(self):
        try:
            turret = self.systems["turret"]
            angle = turret.get_turret_status()
            self.display_two_lines("TURRET", f"Angle: {angle}")
        except Exception as e:
            print(f"TURRET error: {e}")
            self.display_two_lines("TURRET", "ERROR")

    def show_message(self):
        self.scroll_text("MESSAGE", self.last_message)

    def show_emergency(self):
        self.display_two_lines("!!! ALERT !!!", "SYSTEM HALTED")

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

    def start(self):
        print("LCD iniciado")
        self.update()

    def stop(self):
        print("LCD detenido")
        self.stop_event.set()
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass
        if self.lcd:
            self.lcd.clear()