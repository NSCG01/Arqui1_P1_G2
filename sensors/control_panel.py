import RPi.GPIO as GPIO
import threading
import time

class ControlPanel:

    # ---------------- CONFIG ----------------
    EMERGENCY_BUTTON = 11
    LED_STATUS = 9

    # Buzzers (ajusta si cambiaste pines)
    BUZZER_FIRE = 18
    BUZZER_TURRET = 25

    def __init__(self, systems):

        """
        systems = {
            "fire": FireDetector,
            "meteor": MeteorDetector,
            "disguise": Disguise,
            "env": Environment,
            "gate": Gate,
            "turret": Turret
        }
        """

        self.systems = systems

        # ---------------- GPIO ----------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.EMERGENCY_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_STATUS, GPIO.OUT)

        GPIO.setup(self.BUZZER_FIRE, GPIO.OUT)
        GPIO.setup(self.BUZZER_TURRET, GPIO.OUT)

        # ---------------- ESTADO ----------------
        self.stop_event = threading.Event()

        self.emergency_active = False
        self.last_button_state = 1
        self.press_count = 0
        self.last_press_time = 0

    # ---------------- LED SISTEMA ----------------
    def system_led(self):
        if self.stop_event.is_set():
            return

        # LED encendido si NO hay emergencia
        GPIO.output(self.LED_STATUS, not self.emergency_active)

        threading.Timer(1.0, self.system_led).start()

    # ---------------- BOTÓN ----------------
    def button_loop(self):
        if self.stop_event.is_set():
            return

        current = GPIO.input(self.EMERGENCY_BUTTON)

        # detección flanco
        if self.last_button_state == 1 and current == 0:
            now = time.time()

            # reset contador si pasa mucho tiempo
            if now - self.last_press_time > 2:
                self.press_count = 0

            self.press_count += 1
            self.last_press_time = now

            self.handle_presses()

        self.last_button_state = current

        threading.Timer(0.1, self.button_loop).start()

    # ---------------- LÓGICA DE PRESIONES ----------------
    def handle_presses(self):

        # 1 click → activar emergencia
        if self.press_count == 1 and not self.emergency_active:
            self.activate_emergency()

        # 2 clicks → desactivar
        elif self.press_count >= 2 and self.emergency_active:
            self.deactivate_emergency()
            self.press_count = 0

    # ---------------- EMERGENCIA ----------------
    def activate_emergency(self):
        print("🚨 EMERGENCIA ACTIVADA")
        self.emergency_active = True

        # detener todos los sistemas
        for name, system in self.systems.items():
            try:
                system.stop()
            except:
                pass

        # encender buzzers
        GPIO.output(self.BUZZER_FIRE, True)
        GPIO.output(self.BUZZER_TURRET, True)

        # apagar LED sistema
        GPIO.output(self.LED_STATUS, False)

    def deactivate_emergency(self):
        print("EMERGENCIA DESACTIVADA - REINICIANDO")

        self.emergency_active = False

        # apagar buzzers
        GPIO.output(self.BUZZER_FIRE, False)
        GPIO.output(self.BUZZER_TURRET, False)

        # reiniciar sistemas
        for name, system in self.systems.items():
            try:
                system.start()
            except:
                pass

        GPIO.output(self.LED_STATUS, True)

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
        GPIO.cleanup()