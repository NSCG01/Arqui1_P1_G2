import RPi.GPIO as GPIO
import threading
import time

class Turret:

    # ---------------- CONFIG ----------------
    PINS = [6, 13, 19, 26]

    BUTTON_LEFT = 20
    BUTTON_RIGHT = 21
    BUTTON_FIRE = 16

    LASER = 12
    BUZZER = 25

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

        # ---------------- GPIO ----------------
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

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()

        self.current_step = 0
        self.current_angle = 0.0
        self.target_angle = 0.0

        self.step_index = 0
        self.moving = False

    # ---------------- STEPPER ----------------
    def step_once(self, direction):

        self.step_index = (self.step_index + direction) % len(self.SEQ)

        for pin, val in zip(self.PINS, self.SEQ[self.step_index]):
            GPIO.output(pin, val)

        self.current_step += direction
        self.current_angle = (self.current_step * self.DEG_PER_STEP) % 360

    def motor_loop(self):
        if self.stop_event.is_set():
            return

        diff = (self.target_angle - self.current_angle + 540) % 360 - 180

        if abs(diff) > self.DEG_PER_STEP:
            self.moving = True
            direction = 1 if diff > 0 else -1
            self.step_once(direction)
        else:
            self.moving = False
            self.release_motor()

        threading.Timer(0.003, self.motor_loop).start()

    def release_motor(self):
        for p in self.PINS:
            GPIO.output(p, 0)

    # ---------------- BOTONES ----------------
    def button_loop(self):
        if self.stop_event.is_set():
            return

        if GPIO.input(self.BUTTON_LEFT) == 0:
            self.target_angle = (self.target_angle - 5) % 360

        if GPIO.input(self.BUTTON_RIGHT) == 0:
            self.target_angle = (self.target_angle + 5) % 360

        if GPIO.input(self.BUTTON_FIRE) == 0:
            self.fire()

        threading.Timer(0.1, self.button_loop).start()

    # ---------------- DISPARO ----------------
    def fire(self):
        print(" FIRE!")

        GPIO.output(self.LASER, True)

        def buzz():
            GPIO.output(self.BUZZER, True)
            threading.Timer(0.05, lambda: GPIO.output(self.BUZZER, False)).start()

        for i in range(5):
            threading.Timer(i * 0.08, buzz).start()

        threading.Timer(0.4, lambda: GPIO.output(self.LASER, False)).start()

    # ---------------- ESTADO PARA LCD ----------------
    def get_turret_status(self):
        return f"{round(self.current_angle,1)}°"

    # ---------------- START ----------------
    def start(self):
        print(" Turret iniciado")
        self.motor_loop()
        self.button_loop()

    # ---------------- STOP ----------------
    def stop(self):
        print("Turret detenido")
        self.stop_event.set()
        self.release_motor()
        GPIO.cleanup()