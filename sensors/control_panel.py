import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class ControlPanel:

    EMERGENCY_BUTTON = 11
    LED_STATUS = 9

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_ALERT = "nave/alertas/criticas"

    DEBOUNCE_TIME = 0.3

    def __init__(self, systems, esp32):
        self.systems = systems
        self.esp32 = esp32

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.EMERGENCY_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_STATUS, GPIO.OUT)

        self.client = mqtt.Client()
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"ControlPanel MQTT error: {e}")

        self.stop_event = threading.Event()

        self.emergency_active = False
        self.last_button_state = 1
        self.last_press_time = 0
        self.led_timer_running = False
        
        print(" ControlPanel inicializado")

    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def publish_alert(self, state):
        payload = {
            "system": "control_panel",
            "event": "EMERGENCY",
            "state": state,
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_ALERT, json.dumps(payload))
            print(f" EMERGENCY MQTT: {state}")
        except Exception as e:
            print(f"ControlPanel publish error: {e}")

    def system_led_loop(self):
        """Loop separado para el LED de estado"""
        while not self.stop_event.is_set():
            if self.emergency_active:
                # Parpadeo rápido en emergencia
                GPIO.output(self.LED_STATUS, not GPIO.input(self.LED_STATUS))
                time.sleep(0.3)
            else:
                # LED fijo encendido en modo normal
                GPIO.output(self.LED_STATUS, True)
                time.sleep(1)

    def button_loop(self):
        while not self.stop_event.is_set():
            current = GPIO.input(self.EMERGENCY_BUTTON)
            now = time.time()

            if self.last_button_state == 1 and current == 0:
                if now - self.last_press_time > self.DEBOUNCE_TIME:
                    self.last_press_time = now
                    self.handle_press()

            self.last_button_state = current
            time.sleep(0.05)

    def handle_press(self):
        if not self.emergency_active:
            self.activate_emergency()
        else:
            self.deactivate_emergency()

    def activate_emergency(self):
        print("EMERGENCIA ACTIVADA")
        self.emergency_active = True

        # detener sistemas
        for name, system in self.systems.items():
            try:
                system.stop()
                print(f" Sistema {name} detenido")
            except Exception as e:
                print(f"Error deteniendo {name}: {e}")

        # Activar buzzer en ESP32
        self.esp32.set_buzzer_general(True)
        
        self.publish_alert("ON")

    def deactivate_emergency(self):
        print("EMERGENCIA DESACTIVADA")
        self.emergency_active = False

        # Apagar buzzer
        self.esp32.set_buzzer_general(False)

        # reiniciar sistemas
        for name, system in self.systems.items():
            try:
                system.start()
                print(f"Sistema {name} reiniciado")
            except Exception as e:
                print(f"Error iniciando {name}: {e}")

        self.publish_alert("OFF")

    def get_emergency_status(self):
        return "!!! EMERGENCY !!!" if self.emergency_active else None

    def is_emergency(self):
        return self.emergency_active

    def start(self):
        print("ControlPanel iniciado (buzzer vía ESP32)")
        GPIO.output(self.LED_STATUS, True)
        threading.Thread(target=self.system_led_loop, daemon=True).start()
        threading.Thread(target=self.button_loop, daemon=True).start()

    def stop(self):
        print("ControlPanel detenido")
        self.stop_event.set()
        self.esp32.set_buzzer_general(False)
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass
