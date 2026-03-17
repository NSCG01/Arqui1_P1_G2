import RPi.GPIO as GPIO
import pigpio
import time

# ========================
# CONFIGURACIÓN DE PINES
# ========================
SERVO_PIN = 27      # GPIO27 (PWM)
BUTTON_PIN = 19     # GPIO17 (Push button)

# ========================
# ESTADO
# ========================
estado_compuerta = False  # False = cerrada, True = abierta

# ========================
# SETUP GPIO
# ========================
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ========================
# SETUP SERVO (pigpio)
# ========================
pi = pigpio.pi()

if not pi.connected:
    print("Error: pigpio no está corriendo")
    exit()

pi.set_mode(SERVO_PIN, pigpio.OUTPUT)

# ========================
# FUNCIÓN SERVO
# ========================
def mover_servo(abrir):
    if abrir:
        print("Abriendo compuerta")
        pi.set_servo_pulsewidth(SERVO_PIN, 2000)  # ~90°
    else:
        print("Cerrando compuerta")
        pi.set_servo_pulsewidth(SERVO_PIN, 1000)  # ~0°

    time.sleep(0.5)
    pi.set_servo_pulsewidth(SERVO_PIN, 0)  # detener señal

# ========================
# CALLBACK BOTÓN
# ========================
def boton_presionado(channel):
    global estado_compuerta
    estado_compuerta = not estado_compuerta
    mover_servo(estado_compuerta)

# Detectar presión (flanco)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=boton_presionado, bouncetime=300)

# ========================
# LOOP PRINCIPAL
# ========================
try:
    print("Sistema de compuertas activo...")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Saliendo...")

finally:
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    pi.stop()
    GPIO.cleanup()