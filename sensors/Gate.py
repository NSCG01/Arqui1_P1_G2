import RPi.GPIO as GPIO
import threading
import time

class Gate:

    # ---------------- CONFIG ----------------
    SERVO = 22
    BUTTON_OPEN = 5
    BUTTON_CLOSE = 27

    OPEN_ANGLE = 90
    CLOSED_ANGLE = 0

    def __init__(self):

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.SERVO, GPIO.OUT)
        GPIO.setup(self.BUTTON_OPEN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_CLOSE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # PWM
        self.pwm = GPIO.PWM(self.SERVO, 50)
        self.pwm.start(0)

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()

        self.current_angle = self.CLOSED_ANGLE
        self.state = "CLOSED"  # SOLO 2 ESTADOS

        # Inicializar en cerrado
        self.set_angle(self.CLOSED_ANGLE)

    # ---------------- SERVO ----------------
    def angle_to_duty(self, angle):
        return 2 + (angle / 18)

    def set_angle(self, angle):
        self.pwm.ChangeDutyCycle(self.angle_to_duty(angle))
        time.sleep(0.3)  # pequeño tiempo para que llegue
        self.pwm.ChangeDutyCycle(0)  # evitar vibración

    def move_to(self, target):

        if self.stop_event.is_set():
            return

        step = 1 if target > self.current_angle else -1

        def step_move():
            if self.stop_event.is_set():
                return

            if self.current_angle != target:
                self.current_angle += step
                self.pwm.ChangeDutyCycle(self.angle_to_duty(self.current_angle))
                threading.Timer(0.02, step_move).start()
            else:
                self.pwm.ChangeDutyCycle(0)

        step_move()

    # ---------------- BOTONES ----------------
    def button_loop(self):
        if self.stop_event.is_set():
            return

        # ABRIR
        if GPIO.input(self.BUTTON_OPEN) == 0 and self.state != "OPEN":
            print(" OPEN")
            self.state = "OPEN"
            self.move_to(self.OPEN_ANGLE)

        # CERRAR
        if GPIO.input(self.BUTTON_CLOSE) == 0 and self.state != "CLOSED":
            print(" CLOSED")
            self.state = "CLOSED"
            self.move_to(self.CLOSED_ANGLE)

        threading.Timer(0.1, self.button_loop).start()

    # ---------------- ESTADO PARA LCD ----------------
    def get_gate_status(self):
        return self.state  # SOLO OPEN o CLOSED

    # ---------------- START ----------------
    def start(self):
        print(" Gate iniciado (2 estados)")
        self.button_loop()

    # ---------------- STOP ----------------
    def stop(self):
        print(" Gate detenido")
        self.stop_event.set()
        self.pwm.stop()
        GPIO.cleanup()