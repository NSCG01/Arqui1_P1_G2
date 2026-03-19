import signal
import sys

# -------- IMPORTS DE TUS MODULOS --------
from fire_detector import FireDetector
from meteor_detector import MeteorDetector
from disguise import Disguise
from environment import Environment
from turret import Turret
from gate import Gate
from control_panel import ControlPanel
from LCDisplay import Display


def main():

    print(" Iniciando sistema de la nave...")

    # -------- INICIALIZAR SISTEMAS --------
    fire = FireDetector()
    meteor = MeteorDetector()
    disguise = Disguise()
    env = Environment()
    turret = Turret()
    gate = Gate()

    # -------- CONTROL PANEL (RECIBE TODOS) --------
    control = ControlPanel({
        "fire": fire,
        "meteor": meteor,
        "disguise": disguise,
        "env": env,
        "gate": gate,
        "turret": turret
    })

    # -------- LCD (LEE SISTEMAS) --------
    lcd = Display({
        "env": env,
        "meteor": meteor,
        "turret": turret,
        "control": control
    })

    # -------- START DE TODOS --------
    fire.start()
    meteor.start()
    disguise.start()
    env.start()
    turret.start()
    gate.start()
    control.start()
    lcd.start()

    print(" Sistema completamente operativo")

    # -------- MANEJO DE SALIDA LIMPIA --------
    def shutdown(signum, frame):
        print("\n Apagando sistema...")

        try:
            fire.stop()
            meteor.stop()
            disguise.stop()
            env.stop()
            turret.stop()
            gate.stop()
            control.stop()
            lcd.stop()
        except:
            pass

        sys.exit(0)

    # Captura Ctrl+C y kill
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # -------- LOOP PRINCIPAL --------
    while True:
        signal.pause()


if __name__ == "__main__":
    main()