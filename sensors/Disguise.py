import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from datetime import datetime

GPIO.setmode(GPIO.BCM)

# ------------------------
# TCS3200
# ------------------------
S0, S1, S2, S3, OUT = 5, 6, 13, 19, 26

GPIO.setup(S0, GPIO.OUT)
GPIO.setup(S1, GPIO.OUT)
GPIO.setup(S2, GPIO.OUT)
GPIO.setup(S3, GPIO.OUT)
GPIO.setup(OUT, GPIO.IN)

GPIO.output(S0, GPIO.HIGH)
GPIO.output(S1, GPIO.LOW)

# ------------------------
# LED RGB (PARALELO)
# ------------------------
LED_R = 18
LED_G = 12
LED_B = 16

GPIO.setup(LED_R, GPIO.OUT)
GPIO.setup(LED_G, GPIO.OUT)
GPIO.setup(LED_B, GPIO.OUT)

# CAMBIA ESTO SEGÚN TU LED
COMMON_ANODE = False  # True si es ánodo común

# ------------------------
# MQTT + Mongo
# ------------------------
client = mqtt.Client()
client.connect("localhost", 1883, 60)

mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["nave"]
events = db["events"]

# ------------------------
# VARIABLES
# ------------------------
sequence_detected = []
correct_sequence = ["RED", "YELLOW", "BLUE"]
camouflage_active = False

# ------------------------
# CONTROL LED
# ------------------------
def set_rgb(r, g, b):

    if COMMON_ANODE:
        GPIO.output(LED_R, not r)
        GPIO.output(LED_G, not g)
        GPIO.output(LED_B, not b)
    else:
        GPIO.output(LED_R, r)
        GPIO.output(LED_G, g)
        GPIO.output(LED_B, b)


def set_color(color):

    if color == "RED":
        set_rgb(1,0,0)

    elif color == "YELLOW":
        set_rgb(1,1,0)

    elif color == "BLUE":
        set_rgb(0,0,1)

    else:
        set_rgb(0,0,0)

# ------------------------
# SENSOR (frecuencia real)
# ------------------------
def measure_frequency():

    start = time.time()
    count = 0

    while time.time() - start < 0.1:
        if GPIO.input(OUT) == GPIO.LOW:
            count += 1
            while GPIO.input(OUT) == GPIO.LOW:
                pass

    return count


def read_color():

    GPIO.output(S2, GPIO.LOW)
    GPIO.output(S3, GPIO.LOW)
    red = measure_frequency()

    GPIO.output(S2, GPIO.HIGH)
    GPIO.output(S3, GPIO.HIGH)
    green = measure_frequency()

    GPIO.output(S2, GPIO.LOW)
    GPIO.output(S3, GPIO.HIGH)
    blue = measure_frequency()

    if red < green and red < blue:
        return "RED"
    elif green < red and green < blue:
        return "GREEN"
    elif blue < red and blue < green:
        return "BLUE"
    elif red < 200 and green < 200:
        return "YELLOW"
    else:
        return "UNKNOWN"

# ------------------------
# EVENTOS
# ------------------------
def log_event(name):

    events.insert_one({
        "type": name,
        "timestamp": datetime.now()
    })

# ------------------------
# CAMUFLAJE
# ------------------------
def activate_camouflage():

    global camouflage_active

    if not camouflage_active:

        camouflage_active = True

        print("🟦 CAMUFLAJE ACTIVADO")

        client.publish("nave/alertas/camuflaje", "ON")
        log_event("camouflage_on")

        for color in correct_sequence:
            set_color(color)
            time.sleep(1)


def deactivate_camouflage():

    global camouflage_active

    if camouflage_active:

        camouflage_active = False

        print("❌ CAMUFLAJE DESACTIVADO")

        client.publish("nave/alertas/camuflaje", "OFF")
        log_event("camouflage_off")

        set_color("OFF")

# ------------------------
# LOOP
# ------------------------
def run():

    global sequence_detected

    while True:

        color = read_color()

        if color != "UNKNOWN":

            print("Color:", color)
            client.publish("nave/sensores/color", color)

            sequence_detected.append(color)

            if len(sequence_detected) > 3:
                sequence_detected.pop(0)

            if sequence_detected == correct_sequence:
                activate_camouflage()
                sequence_detected = []

        else:
            deactivate_camouflage()

        time.sleep(0.5)


if __name__ == "__main__":

    try:
        run()

    except KeyboardInterrupt:
        GPIO.cleanup()