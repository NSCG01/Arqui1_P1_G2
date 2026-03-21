import signal
import sys
import time
import RPi.GPIO as GPIO

# -------- IMPORTS --------
from sensors.esp32_interface import ESP32Interface
from fire_detector import FireDetector
from meteor_detector import MeteorDetector
from disguise import Disguise
from turret import Turret
from gate import Gate
from control_panel import ControlPanel
from LCDisplay import Display


def main():

    print("=" * 50)
    print("🚀 Iniciando sistema de la nave con ESP32...")
    print("=" * 50)

    systems = {}

    try:
        # -------- INICIALIZAR ESP32 (I2C) --------
        print("\n📡 Conectando con ESP32...")
        esp32 = ESP32Interface()
        time.sleep(2)  # Dar tiempo para que ESP32 inicie

        # -------- INICIALIZAR MÓDULOS --------
        print("\n🔧 Inicializando módulos...")
        fire = FireDetector(esp32)
        meteor = MeteorDetector(esp32)
        disguise = Disguise(esp32)
        turret = Turret(esp32)
        gate = Gate()

        systems = {
            "fire": fire,
            "meteor": meteor,
            "disguise": disguise,
            "turret": turret,
            "gate": gate
        }

        # -------- CONTROL PANEL (con ESP32) --------
        control = ControlPanel(systems, esp32)

        # -------- LCD --------
        lcd = Display({
            "env": esp32,           # ESP32 ahora provee datos ambientales
            "meteor": meteor,
            "turret": turret,
            "control": control
        })

    except Exception as e:
        print(f"\n❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # -------- START SEGURO --------
    def safe_start(name, system):
        try:
            system.start()
            print(f"✅ {name} iniciado")
        except Exception as e:
            print(f"❌ Error iniciando {name}: {e}")

    print("\n🚀 Iniciando todos los sistemas...")
    safe_start("ESP32 Interface", esp32)
    safe_start("FireDetector", fire)
    safe_start("MeteorDetector", meteor)
    safe_start("Disguise", disguise)
    safe_start("Turret", turret)
    safe_start("Gate", gate)
    safe_start("ControlPanel", control)
    safe_start("LCD", lcd)

    print("\n" + "=" * 50)
    print("🟢 SISTEMA COMPLETAMENTE OPERATIVO")
    print("=" * 50)
    print("Presiona Ctrl+C para apagar el sistema\n")

    # -------- SHUTDOWN LIMPIO --------
    def shutdown(signum=None, frame=None):
        print("\n\n🛑 Apagando sistema...")

        shutdown_order = [
            ("LCD", lcd),
            ("ControlPanel", control),
            ("Gate", gate),
            ("Turret", turret),
            ("Disguise", disguise),
            ("Meteor", meteor),
            ("Fire", fire),
            ("ESP32", esp32),
        ]

        for name, system in shutdown_order:
            try:
                system.stop()
                print(f"🔻 {name} detenido")
            except Exception as e:
                print(f"⚠️ Error deteniendo {name}: {e}")

        try:
            GPIO.cleanup()
            print("🧹 GPIO liberado")
        except Exception as e:
            print(f"GPIO cleanup error: {e}")

        print("\n✅ Sistema apagado correctamente")
        sys.exit(0)

    # -------- SIGNALS --------
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # -------- LOOP PRINCIPAL --------
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()