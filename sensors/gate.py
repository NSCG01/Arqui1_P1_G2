import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class Gate:

    # ---------------- CONFIG ----------------
    SERVO = 11
    BUTTON_OPEN = 10   # Pines libres (conflicto resuelto)
    BUTTON_CLOSE = 22  # Pines libres

    OPEN_ANGLE = 90
    CLOSED_ANGLE = 0

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_COMMAND = "nave/actuadores/compuertas"
    TOPIC_STATUS = "nave/actuadores/compuertas/estado"

    DEBOUNCE_TIME = 0.3

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.SERVO, GPIO.OUT)
        GPIO.setup(self.BUTTON_OPEN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_CLOSE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.pwm = GPIO.PWM(self.SERVO, 50)
        self.pwm.start(0)

        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.subscribe(self.TOPIC_COMMAND)
            self.client.loop_start()
        except Exception as e:
            print(f" Gate MQTT error: {e}")

        self.stop_event = threading.Event()
        self.current_angle = self.CLOSED_ANGLE
        self.target_angle = self.CLOSED_ANGLE
        self.state = "CLOSED"
        self.moving = False

        self.last_press_open = 0
        self.last_press_close = 0
        self.last_status_pub = 0

        self.target_angle = self.CLOSED_ANGLE
        print(" Gate inicializado")

    def angle_to_duty(self, angle):
        return 2 + (angle / 18)

    def motor_loop(self):
        while not self.stop_event.is_set():
            if self.current_angle != self.target_angle:
                self.moving = True
                step = 1 if self.target_angle > self.current_angle else -1
                self.current_angle += step
                self.pwm.ChangeDutyCycle(self.angle_to_duty(self.current_angle))
            else:
                if self.moving:
                    self.pwm.ChangeDutyCycle(0)
                    self.moving = False

            now = time.time()
            if now - self.last_status_pub >= 2.0:
                self.publish_status()
                self.last_status_pub = now

            time.sleep(0.02)

    def button_loop(self):
        while not self.stop_event.is_set():
            now = time.time()

            if GPIO.input(self.BUTTON_OPEN) == 0:
                if now - self.last_press_open > self.DEBOUNCE_TIME:
                    self.open_gate()
                    self.last_press_open = now

            if GPIO.input(self.BUTTON_CLOSE) == 0:
                if now - self.last_press_close > self.DEBOUNCE_TIME:
                    self.close_gate()
                    self.last_press_close = now

            time.sleep(0.1)

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            print(f" MQTT Gate recibe: {data}")

            cmd = data.get("cmd", "").upper()

            if cmd == "OPEN":
                self.open_gate()
            elif cmd == "CLOSE":
                self.close_gate()

        except Exception as e:
            print("MQTT ERROR:", e)

    def publish_status(self):
        payload = {
            "actuator": "gate",
            "state": self.state,
            "angle": self.current_angle,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            self.client.publish(self.TOPIC_STATUS, json.dumps(payload))
        except Exception as e:
            print(f" Gate publish error: {e}")

    def open_gate(self):
        if self.state != "OPEN" and not self.moving:
            print(" GATE OPEN")
            self.target_angle = self.OPEN_ANGLE
            self.state = "OPEN"
            self.publish_status()

    def close_gate(self):
        if self.state != "CLOSED" and not self.moving:
            print(" GATE CLOSED")
            self.target_angle = self.CLOSED_ANGLE
            self.state = "CLOSED"
            self.publish_status()

    def get_gate_status(self):
        return self.state

    def start(self):
        print(" Gate iniciado")
        threading.Thread(target=self.motor_loop, daemon=True).start()
        threading.Thread(target=self.button_loop, daemon=True).start()

    def stop(self):
        print("Gate detenido")
        self.stop_event.set()
        self.pwm.stop()
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass