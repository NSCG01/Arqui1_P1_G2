import RPi.GPIO as GPIO
import time
from datetime import datetime
from LCDisplay import LCDDisplay

GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO = 24
BUZZER = 9

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(TRIG, False)

lcd = LCDDisplay()

# -------------------------------------------------
# MEDIR DISTANCIA
# -------------------------------------------------

def medir_distancia():

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start = time.time()
    stop = time.time()

    while GPIO.input(ECHO) == 0:
        start = time.time()

    while GPIO.input(ECHO) == 1:
        stop = time.time()

    tiempo = stop - start
    distancia = (tiempo * 34300) / 2

    return round(distancia, 2)

# -------------------------------------------------
# CLASIFICAR DISTANCIA
# -------------------------------------------------

def clasificar_distancia(distancia):

    if distancia > 50:
        return "LEJANO"

    elif 20 <= distancia <= 50:
        return "CERCANO"

    else:
        return "CRITICO"

# -------------------------------------------------
# PATRONES BUZZER
# -------------------------------------------------

def beep(duration):
    GPIO.output(BUZZER, True)
    time.sleep(duration)
    GPIO.output(BUZZER, False)

def buzzer_lejano():

    beep(0.2)
    time.sleep(2)

def buzzer_cercano():

    for _ in range(3):
        beep(0.1)
        time.sleep(0.1)

    time.sleep(1)

def buzzer_critico():

    GPIO.output(BUZZER, True)

# -------------------------------------------------
# REGISTRO DETECCION (PARA MONGODB FUTURO)
# -------------------------------------------------

def registrar_deteccion(distancia, estado):

    data = {
        "distancia": distancia,
        "estado": estado,
        "timestamp": datetime.now()
    }

    # FUTURO:
    # mongo.insert_one(data)

    return data

# -------------------------------------------------
# ENVIO A DASHBOARD (API FUTURA)
# -------------------------------------------------

def enviar_dashboard(distancia, estado):

    payload = {
        "distance": distancia,
        "status": estado
    }

    # FUTURO
    # requests.post(API_URL, json=payload)

    return payload

# -------------------------------------------------
# ACTUALIZAR LCD
# -------------------------------------------------

def actualizar_lcd(distancia, estado):

    linea1 = f"Dist: {distancia} cm"
    linea2 = f"Estado: {estado}"

    lcd.display(linea1, linea2)

# -------------------------------------------------
# CONTROL BUZZER
# -------------------------------------------------

def controlar_buzzer(estado):

    if estado == "LEJANO":
        buzzer_lejano()

    elif estado == "CERCANO":
        buzzer_cercano()

    elif estado == "CRITICO":
        buzzer_critico()

# -------------------------------------------------
# LOOP PRINCIPAL
# -------------------------------------------------

def sistema_deteccion():

    try:

        while True:

            distancia = medir_distancia()

            estado = clasificar_distancia(distancia)

            actualizar_lcd(distancia, estado)

            registrar_deteccion(distancia, estado)

            enviar_dashboard(distancia, estado)

            controlar_buzzer(estado)

            time.sleep(0.2)

    except KeyboardInterrupt:

        GPIO.cleanup()
        lcd.clear()

# -------------------------------------------------

if __name__ == "__main__":

    sistema_deteccion()