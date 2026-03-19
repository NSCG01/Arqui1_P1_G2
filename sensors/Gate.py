import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class Gate:

    # ---------------- CONFIG ----------------
    SERVO = 24
    BUTTON_OPEN = 5
    BUTTON_CLOSE = 6

    OPEN_ANGLE = 90
    CLOSED_ANGLE = 0

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_COMMAND = "nave/actuadores/compuertas"

    DEBOUNCE_TIME = 0.3

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.SERVO, GPIO.OUT)
        GPIO.setup(self.BUTTON_OPEN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_CLOSE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.pwm = GPIO.PWM(self.SERVO, 50)
        self.pwm.start(0)

        # MQTT
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.subscribe(self.TOPIC_COMMAND)
        self.client.loop_start()

        # Estado
        self.stop_event = threading.Event()
        self.current_angle = self.CLOSED_ANGLE
        self.target_angle = self.CLOSED_ANGLE
        self.state = "CLOSED"

        self.moving = False

        # debounce
        self.last_press_open = 0
        self.last_press_close = 0

        # inicial
        self.target_angle = self.CLOSED_ANGLE

    # ---------------- SERVO ----------------
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

            self.stop_event.wait(0.02)

    # ---------------- BOTONES ----------------
    def button_loop(self):

        while not self.stop_event.is_set():

            now = time.time()

            # ABRIR
            if GPIO.input(self.BUTTON_OPEN) == 0:
                if now - self.last_press_open > self.DEBOUNCE_TIME:
                    self.open_gate()
                    self.last_press_open = now

            # CERRAR
            if GPIO.input(self.BUTTON_CLOSE) == 0:
                if now - self.last_press_close > self.DEBOUNCE_TIME:
                    self.close_gate()
                    self.last_press_close = now

            self.stop_event.wait(0.1)

    # ---------------- MQTT ----------------
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            cmd = data.get("cmd", "").upper()

            if cmd == "OPEN":
                self.open_gate()

            elif cmd == "CLOSE":
                self.close_gate()

        except Exception as e:
            print("MQTT ERROR:", e)

    # ---------------- CONTROL ----------------
    def open_gate(self):
        if self.state != "OPEN" and not self.moving:
            print("GATE OPEN")
            self.target_angle = self.OPEN_ANGLE
            self.state = "OPEN"

    def close_gate(self):
        if self.state != "CLOSED" and not self.moving:
            print("GATE CLOSED")
            self.target_angle = self.CLOSED_ANGLE
            self.state = "CLOSED"

    # ---------------- LCD ----------------
    def get_gate_status(self):
        return self.state

    # ---------------- START ----------------
    def start(self):
        print("Gate iniciado")

        threading.Thread(target=self.motor_loop, daemon=True).start()
        threading.Thread(target=self.button_loop, daemon=True).start()

    # ---------------- STOP ----------------
    def stop(self):
        print("Gate detenido")
        self.stop_event.set()
        self.pwm.stop()
        self.client.loop_stop()
        self.client.disconnect()