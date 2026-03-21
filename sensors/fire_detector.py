import threading
import time
import json
import paho.mqtt.client as mqtt


class FireDetector:

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "nave/sensores/gas"
    TOPIC_ALERT = "nave/alertas/criticas"

    def __init__(self, esp32):
        self.esp32 = esp32
        self.fire_detected = False
        self.prev_state = None
        
        # MQTT
        self.client = mqtt.Client()
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"⚠️ FireDetector MQTT error: {e}")
        
        self.stop_event = threading.Event()
        print("✅ FireDetector inicializado")

    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def loop(self):
        while not self.stop_event.is_set():
            # Leer estado actual desde ESP32
            self.fire_detected = self.esp32.fire_detected
            
            # Publicar cada 3 segundos
            self.publish_sensor()
            
            # Detectar cambios
            if self.prev_state is None:
                self.prev_state = self.fire_detected
            
            if self.fire_detected != self.prev_state:
                print(f"🔥 FIRE: {'ON' if self.fire_detected else 'OFF'}")
                self.publish_alert()
                self.prev_state = self.fire_detected
            
            self.stop_event.wait(3)

    def publish_sensor(self):
        payload = {
            "value": self.esp32.gas_level,
            "status": "FIRE" if self.fire_detected else "SAFE",
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_SENSOR, json.dumps(payload))
        except Exception as e:
            pass

    def publish_alert(self):
        payload = {
            "type": "FIRE",
            "state": "ON" if self.fire_detected else "OFF",
            "timestamp": self.get_timestamp()
        }
        try:
            self.client.publish(self.TOPIC_ALERT, json.dumps(payload))
        except Exception as e:
            pass

    def get_fire_status(self):
        """Obtener estado para LCD"""
        return "FIRE!" if self.fire_detected else "SAFE"

    def start(self):
        print("✅ FireDetector iniciado (usando ESP32)")
        threading.Thread(target=self.loop, daemon=True).start()

    def stop(self):
        print("FireDetector detenido")
        self.stop_event.set()
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass