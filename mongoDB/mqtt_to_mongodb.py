"""
Listener MQTT que guarda datos en MongoDB
Escucha todos los tópicos de sensores y eventos
"""

import json
import paho.mqtt.client as mqtt
from datetime import datetime
from mongodb_manager import db_manager

class MQTTtoMongoDB:
    
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        
        # Cliente MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        print(f"Conectando a MQTT broker: {mqtt_broker}:{mqtt_port}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta a MQTT"""
        if rc == 0:
            print("Conectado a MQTT broker")
            
            # Suscribirse a todos los tópicos de sensores
            self.client.subscribe("nave/sensores/#")        # Sensores
            self.client.subscribe("nave/alertas/#")         # Alertas
            self.client.subscribe("nave/comandos/#")        # Comandos
            self.client.subscribe("nave/mensajes/#")        # Mensajes
            
            print("Suscrito a tópicos MQTT")
        else:
            print(f"Error conexión MQTT: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback cuando recibe un mensaje MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"MQTT recibido: {topic}")
            
            # Enrutar según el tipo de tópico
            if "sensores" in topic:
                self._save_sensor_reading(topic, payload)
            elif "alertas" in topic:
                self._save_alert(topic, payload)
            elif "comandos" in topic:
                self._save_command(topic, payload)
            elif "mensajes" in topic:
                self._save_message(topic, payload)
        
        except json.JSONDecodeError:
            print(f"Error decodificando JSON: {msg.payload}")
        except Exception as e:
            print(f"Error procesando mensaje: {e}")
    
    def _save_sensor_reading(self, topic, payload):
        """Guarda lecturas de sensores"""
        # Extraer tipo de sensor del tópico
        # "nave/sensores/temperatura" → "temperatura"
        parts = topic.split("/")
        sensor_type = parts[-1] if len(parts) > 0 else "unknown"
        
        data = {
            "topic": topic,
            **payload  # Incluir todos los datos del payload
        }
        
        db_manager.save_sensor_reading(sensor_type, data)
    
    def _save_alert(self, topic, payload):
        """Guarda alertas"""
        event_type = payload.get("type", "UNKNOWN_ALERT")
        description = payload.get("message", "Sin descripción")
        
        db_manager.save_event(
            event_type=event_type,
            description=description,
            severity="WARNING"
        )
    
    def _save_command(self, topic, payload):
        """Guarda comandos ejecutados"""
        command_type = payload.get("command", "UNKNOWN")
        status = payload.get("status", "PENDING")
        
        db_manager.save_command(
            command_type=command_type,
            status=status,
            details=payload
        )
    
    def _save_message(self, topic, payload):
        """Guarda mensajes"""
        message = payload.get("message", "")
        sender = payload.get("sender", "MQTT")
        
        db_manager.save_message(
            message=message,
            room="CONTROL_ROOM",
            sender=sender
        )
    
    def start(self):
        """Inicia el listener MQTT"""
        try:
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_start()
            print("Listener MQTT iniciado")
        except Exception as e:
            print(f"Error iniciando listener MQTT: {e}")
    
    def stop(self):
        """Detiene el listener MQTT"""
        self.client.loop_stop()
        self.client.disconnect()
        print("Listener MQTT detenido")


# Usar como servicio independiente
if __name__ == "__main__":
    mqtt_listener = MQTTtoMongoDB(mqtt_broker="localhost", mqtt_port=1883)
    mqtt_listener.start()
    
    # Mantener ejecutando
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mqtt_listener.stop()
        print("Listener MQTT cerrado correctamente")