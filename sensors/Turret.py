import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# Motor pins
IN1 = 20
IN2 = 21
IN3 = 25
IN4 = 8

motor_pins = [IN1, IN2, IN3, IN4]

# Botones
BTN_LEFT = 5
BTN_RIGHT = 6
BTN_FIRE = 22

# Actuadores
LED_FIRE = 0
BUZZER = 10

# Configuración GPIO
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

GPIO.setup(BTN_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BTN_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BTN_FIRE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(LED_FIRE, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

# Secuencia del motor (half-step)
sequence = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1]
]

step_delay = 0.002
steps_per_rev = 512  # aprox para 28BYJ-48

current_angle = 0

def step_motor(direction=1, steps=1):
    global current_angle
    for _ in range(steps):
        for step in (sequence if direction == 1 else reversed(sequence)):
            for i in range(4):
                GPIO.output(motor_pins[i], step[i])
            time.sleep(step_delay)

    # actualizar ángulo aproximado
    current_angle += direction * (360 / steps_per_rev * steps)
    current_angle %= 360

def go_home():
    global current_angle
    steps_to_home = int((current_angle / 360) * steps_per_rev)
    step_motor(direction=-1, steps=steps_to_home)
    current_angle = 0

def rotate_to_angle(target_angle):
    global current_angle
    diff = target_angle - current_angle

    steps = int(abs(diff) / 360 * steps_per_rev)

    if diff > 0:
        step_motor(direction=1, steps=steps)
    else:
        step_motor(direction=-1, steps=steps)

def fire():
    GPIO.output(LED_FIRE, 1)
    
    for _ in range(3):
        GPIO.output(BUZZER, 1)
        time.sleep(0.1)
        GPIO.output(BUZZER, 0)
        time.sleep(0.1)

    time.sleep(0.3)
    GPIO.output(LED_FIRE, 0)

try:
    while True:
        if GPIO.input(BTN_LEFT):
            step_motor(direction=-1, steps=5)

        if GPIO.input(BTN_RIGHT):
            step_motor(direction=1, steps=5)

        if GPIO.input(BTN_FIRE):
            fire()

        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()