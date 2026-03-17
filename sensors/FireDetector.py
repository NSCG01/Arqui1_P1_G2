import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime

from LCDisplay import LCDisplay


# -------------------------
# PINES BCM
# -------------------------

GAS_SENSOR_PIN = 17
FAN1_PIN = 7
FAN2_PIN = 1
LED_PIN = 27


DANGER_LEVEL = 1


class FireDetector:

    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(GAS_SENSOR_PIN, GPIO.IN)
        GPIO.setup(FAN1_PIN, GPIO.OUT)
        GPIO.setup(FAN2_PIN, GPIO.OUT)
        GPIO.setup(LED_PIN, GPIO.OUT)

        GPIO.output(FAN1_PIN, GPIO.LOW)
        GPIO.output(FAN2_PIN, GPIO.LOW)
        GPIO.output(LED_PIN, GPIO.LOW)

        self.running = True
        self.alarm_active = False

        self.lcd = LCDisplay()

        self.lcd.display_message(
            "Sistema Incendio",
            "Inicializando"
        )

        time.sleep(2)

        self.lcd.display_message(
            "Estado:",
            "Monitoreando"
        )

    # -------------------------
    # LED PARPADEANTE
    # -------------------------

    def blink_led(self):

        while self.alarm_active:

            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.5)

            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.5)

    # -------------------------
    # ACTIVAR ALERTA
    # -------------------------

    def trigger_alarm(self):

        if self.alarm_active:
            return

        self.alarm_active = True

        print("⚠️ GAS DETECTADO")

        GPIO.output(FAN1_PIN, GPIO.HIGH)
        GPIO.output(FAN2_PIN, GPIO.HIGH)

        self.lcd.display_message(
            "ALERTA GAS!",
            "Ventilando..."
        )

        self.log_event()

        threading.Thread(
            target=self.blink_led,
            daemon=True
        ).start()

        self.send_dashboard_alert()

    # -------------------------
    # DESACTIVAR ALERTA
    # -------------------------

    def reset_alarm(self):

        if not self.alarm_active:
            return

        self.alarm_active = False

        GPIO.output(FAN1_PIN, GPIO.LOW)
        GPIO.output(FAN2_PIN, GPIO.LOW)
        GPIO.output(LED_PIN, GPIO.LOW)

        self.lcd.display_message(
            "Estado:",
            "Monitoreando"
        )

        print("Sistema normal")

    # -------------------------
    # LOG EVENTO
    # -------------------------

    def log_event(self):

        with open("fire_log.txt", "a") as log:

            log.write(
                f"{datetime.now()} - GAS DETECTADO\n"
            )

    # -------------------------
    # ALERTA DASHBOARD
    # -------------------------

    def send_dashboard_alert(self):

        # aquí luego conectarás tu API REST
        print("📡 Enviando alerta al dashboard...")

    # -------------------------
    # MONITOREO CONTINUO
    # -------------------------

    def monitor(self):

        print("Sistema de detección iniciado")

        try:

            while self.running:

                gas_state = GPIO.input(GAS_SENSOR_PIN)

                if gas_state == DANGER_LEVEL:
                    self.trigger_alarm()

                else:
                    self.reset_alarm()

                time.sleep(1)

        except KeyboardInterrupt:

            print("Sistema detenido")

        finally:

            GPIO.cleanup()


if __name__ == "__main__":

    detector = FireDetector()
    detector.monitor()