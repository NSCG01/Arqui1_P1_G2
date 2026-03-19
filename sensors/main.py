import signal
import sys
import time
import threading
import RPi.GPIO as GPIO

# -------- IMPORTS --------
from fire_detector import FireDetector
from meteor_detector import MeteorDetector
from disguise import Disguise
from environment import Environment
from turret import Turret
from gate import Gate
from control_panel import ControlPanel
from LCDisplay import Display


def main():

    print("🚀 Iniciando sistema de la nave...")

    systems = {}

    try:
        # -------- INICIALIZAR --------
        fire = FireDetector()
        meteor = MeteorDetector()
        disguise = Disguise()
        env = Environment()
        turret = Turret()
        gate = Gate()

        systems = {
            "fire": fire,
            "meteor": meteor,
            "disguise": disguise,
            "env": env,
            "gate": gate,
            "turret": turret
        }

        # -------- CONTROL --------
        control = ControlPanel(systems)

        # -------- LCD --------
        lcd = Display({
            "env": env,
            "meteor": meteor,
            "turret": turret,
            "control": control
        })

    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        sys.exit(1)

    # -------- START SEGURO --------
    def safe_start(name, system):
        try:
            system.start()
            print(f"✅ {name} iniciado")
        except Exception as e:
            print(f"❌ Error iniciando {name}: {e}")

    safe_start("Fire", fire)
    safe_start("Meteor", meteor)
    safe_start("Disguise", disguise)
    safe_start("Environment", env)
    safe_start("Turret", turret)
    safe_start("Gate", gate)
    safe_start("ControlPanel", control)
    safe_start("LCD", lcd)

    print("🟢 Sistema completamente operativo")

    # -------- SHUTDOWN LIMPIO --------
    def shutdown(signum=None, frame=None):
        print("\n🛑 Apagando sistema...")

        shutdown_order = [
            ("LCD", lcd),
            ("ControlPanel", control),
            ("Gate", gate),
            ("Turret", turret),
            ("Fire", fire),
            ("Meteor", meteor),
            ("Disguise", disguise),
            ("Environment", env),
        ]

        for name, system in shutdown_order:
            try:
                system.stop()
                print(f"🔻 {name} detenido")
            except Exception as e:
                print(f"⚠️ Error deteniendo {name}: {e}")

        # GPIO cleanup SOLO AQUÍ (una vez)
        try:
            GPIO.cleanup()
            print("🧹 GPIO liberado")
        except Exception as e:
            print(f"GPIO cleanup error: {e}")

        sys.exit(0)

    # -------- SIGNALS --------
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # -------- LOOP PRINCIPAL --------
    try:
        while True:
            time.sleep(1)  # bajo consumo CPU, no afecta timers
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()