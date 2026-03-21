import RPi.GPIO as GPIO
import threading
import time
import json
import paho.mqtt.client as mqtt


class Turret:

    # ---------------- CONFIG ----------------
    PINS = [14, 15, 23, 24]

    BUTTON_LEFT = 4
    BUTTON_RIGHT = 17
    BUTTON_FIRE = 27

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    TOPIC_COMMAND = "nave/actuadores/torreta"
    TOPIC_STATUS = "nave/actuadores/torreta/estado"

    DEBOUNCE = 0.2

    STEPS_PER_REV = 2048
    DEG_PER_STEP = 360.0 / STEPS_PER_REV

    SEQ = [
        [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
        [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
    ]

    def __init__(self, esp32):
        self.esp32 = esp32

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for p in self.PINS:
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, 0)

        GPIO.setup(self.BUTTON_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_FIRE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.subscribe(self.TOPIC_COMMAND)
            self.client.loop_start()
        except Exception as e:
            print(f"⚠️ Turret MQTT error: {e}")

        self.stop_event = threading.Event()

        self.current_step = 0
        self.current_angle = 0.0
        self.target_angle = 0.0

        self.step_index = 0
        self.moving = False
        self.is_firing = False

        self.last_left = 0
        self.last_right = 0
        self.last_fire = 0
        self.last_status_pub = 0
        
        print("✅ Turret inicializado")

    def step_once(self, direction):
        self.step_index = (self.step_index + direction) % len(self.SEQ)
        for pin, val in zip(self.PINS, self.SEQ[self.step_index]):
            GPIO.output(pin, val)
        self.current_step += direction
        self.current_angle = (self.current_step * self.DEG_PER_STEP) % 360

    def motor_loop(self):
        while not self.stop_event.is_set():
            diff = (self.target_angle - self.current_angle + 540) % 360 - 180

            if abs(diff) > self.DEG_PER_STEP:
                self.moving = True
                direction = 1 if diff > 0 else -1
                self.step_once(direction)
            else:
                if self.moving:
                    self.release_motor()
                    self.moving = False

            now = time.time()
            if now - self.last_status_pub >= 1.0:
                self.publish_status()
                self.last_status_pub = now

            time.sleep(0.003)

    def release_motor(self):
        for p in self.PINS:
            GPIO.output(p, 0)

    def button_loop(self):
        while not self.stop_event.is_set():
            now = time.time()

            if GPIO.input(self.BUTTON_LEFT) == 0:
                if now - self.last_left > self.DEBOUNCE:
                    self.target_angle = (self.target_angle - 15) % 360
                    print(f"🎯 Torreta: LEFT → {self.target_angle}°")
                    self.last_left = now

            if GPIO.input(self.BUTTON_RIGHT) == 0:
                if now - self.last_right > self.DEBOUNCE:
                    self.target_angle = (self.target_angle + 15) % 360
                    print(f"🎯 Torreta: RIGHT → {self.target_angle}°")
                    self.last_right = now

            if GPIO.input(self.BUTTON_FIRE) == 0:
                if now - self.last_fire > self.DEBOUNCE:
                    self.fire()
                    self.last_fire = now

            time.sleep(0.05)

    def fire(self):
        if self.is_firing:
            return

        self.is_firing = True
        print("🔫 TORRETA: ¡DISPARO!")

        # Encender láser vía ESP32
        self.esp32.set_laser(True)
        self.esp32.set_buzzer_general(True)

        def fire_loop():
            count = 0
            while count < 5 and not self.stop_event.is_set():
                time.sleep(0.05)
                self.esp32.set_buzzer_general(False)
                time.sleep(0.05)
                self.esp32.set_buzzer_general(True)
                count += 1

            self.esp32.set_laser(False)
            self.esp32.set_buzzer_general(False)
            print("🔫 Disparo completado")
            self.is_firing = False

        threading.Thread(target=fire_loop, daemon=True).start()

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            print(f"📩 MQTT Turret recibe: {data}")

            if "angle" in data:
                self.target_angle = float(data["angle"]) % 360
                print(f"🎯 Ángulo remoto: {self.target_angle}°")

            cmd = data.get("cmd", "").upper()

            if cmd == "LEFT":
                self.target_angle = (self.target_angle - 15) % 360
            elif cmd == "RIGHT":
                self.target_angle = (self.target_angle + 15) % 360
            elif cmd == "FIRE":
                self.fire()
            elif cmd == "HOME":
                self.target_angle = 0
                print("🏠 Torreta HOME")

        except Exception as e:
            print(f"MQTT ERROR en turret: {e}")

    def publish_status(self):
        payload = {
            "actuator": "turret",
            "angle": round(self.current_angle, 1),
            "target": round(self.target_angle, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            self.client.publish(self.TOPIC_STATUS, json.dumps(payload))
        except Exception as e:
            print(f"⚠️ Turret publish error: {e}")

    def get_turret_status(self):
        return f"{round(self.current_angle,1)}°"

    def start(self):
        print("✅ Turret iniciado (láser y buzzer vía ESP32)")
        threading.Thread(target=self.motor_loop, daemon=True).start()
        threading.Thread(target=self.button_loop, daemon=True).start()

    def stop(self):
        print("Turret detenido")
        self.stop_event.set()
        self.release_motor()
        self.esp32.set_laser(False)
        self.esp32.set_buzzer_general(False)
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass 