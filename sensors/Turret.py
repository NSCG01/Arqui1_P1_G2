import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class Turret:

    # ---------------- CONFIG ----------------
    PINS = [7, 9, 10, 11]

    BUTTON_LEFT = 0
    BUTTON_RIGHT = 1
    BUTTON_FIRE = 12

    LASER = 12
    BUZZER = 25

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_COMMAND = "nave/actuadores/torreta"

    DEBOUNCE = 0.2

    # Stepper
    STEPS_PER_REV = 2048
    DEG_PER_STEP = 360.0 / STEPS_PER_REV

    SEQ = [
        [1,0,0,0],
        [1,1,0,0],
        [0,1,0,0],
        [0,1,1,0],
        [0,0,1,0],
        [0,0,1,1],
        [0,0,0,1],
        [1,0,0,1]
    ]

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for p in self.PINS:
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, 0)

        GPIO.setup(self.BUTTON_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_FIRE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.setup(self.LASER, GPIO.OUT)
        GPIO.setup(self.BUZZER, GPIO.OUT)

        # MQTT
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.subscribe(self.TOPIC_COMMAND)
        self.client.loop_start()

        # Estado
        self.stop_event = threading.Event()

        self.current_step = 0
        self.current_angle = 0.0
        self.target_angle = 0.0

        self.step_index = 0
        self.moving = False
        self.is_firing = False

        # debounce
        self.last_left = 0
        self.last_right = 0
        self.last_fire = 0

    # ---------------- STEPPER ----------------
    def step_once(self, direction):

        self.step_index = (self.step_index + direction) % len(self.SEQ)

        for pin, val in zip(self.PINS, self.SEQ[self.step_index]):
            GPIO.output(pin, val)

        self.current_step += direction
        self.current_angle = (self.current_step * self.DEG_PER_STEP) % 360

    def motor_loop(self):

        while not self.stop_event.is_set():

            diff = (self.target_angle - self.current_angle + 540) % 360 - 180

            if abs(diff) > self.DEG_PER_STEP:
                self.moving = True
                direction = 1 if diff > 0 else -1
                self.step_once(direction)
            else:
                if self.moving:
                    self.release_motor()
                    self.moving = False

            self.stop_event.wait(0.003)

    def release_motor(self):
        for p in self.PINS:
            GPIO.output(p, 0)

    # ---------------- BOTONES ----------------
    def button_loop(self):

        while not self.stop_event.is_set():

            now = time.time()

            if GPIO.input(self.BUTTON_LEFT) == 0:
                if now - self.last_left > self.DEBOUNCE:
                    self.target_angle = (self.target_angle - 5) % 360
                    self.last_left = now

            if GPIO.input(self.BUTTON_RIGHT) == 0:
                if now - self.last_right > self.DEBOUNCE:
                    self.target_angle = (self.target_angle + 5) % 360
                    self.last_right = now

            if GPIO.input(self.BUTTON_FIRE) == 0:
                if now - self.last_fire > self.DEBOUNCE:
                    self.fire()
                    self.last_fire = now

            self.stop_event.wait(0.05)

    # ---------------- FIRE ----------------
    def fire(self):

        if self.is_firing:
            return

        self.is_firing = True
        print("FIRE!")

        GPIO.output(self.LASER, True)

        def fire_loop():
            count = 0

            while count < 5 and not self.stop_event.is_set():
                GPIO.output(self.BUZZER, True)
                self.stop_event.wait(0.05)
                GPIO.output(self.BUZZER, False)
                self.stop_event.wait(0.05)
                count += 1

            GPIO.output(self.LASER, False)
            self.is_firing = False

        threading.Thread(target=fire_loop, daemon=True).start()

    # ---------------- MQTT ----------------
    def on_message(self, client, userdata, msg):

        try:
            data = json.loads(msg.payload.decode())

            if "angle" in data:
                self.target_angle = float(data["angle"]) % 360

            cmd = data.get("cmd", "").upper()

            if cmd == "LEFT":
                self.target_angle = (self.target_angle - 5) % 360

            elif cmd == "RIGHT":
                self.target_angle = (self.target_angle + 5) % 360

            elif cmd == "FIRE":
                self.fire()

            elif cmd == "HOME":
                self.target_angle = 0

        except Exception as e:
            print("MQTT ERROR:", e)

    # ---------------- LCD ----------------
    def get_turret_status(self):
        return f"{round(self.current_angle,1)}°"

    # ---------------- START ----------------
    def start(self):
        print("Turret iniciado")

        threading.Thread(target=self.motor_loop, daemon=True).start()
        threading.Thread(target=self.button_loop, daemon=True).start()

    # ---------------- STOP ----------------
    def stop(self):
        print("Turret detenido")
        self.stop_event.set()
        self.release_motor()
        self.client.loop_stop()
        self.client.disconnect()