"""
Script de prueba: Envía datos ficticios a MQTT
Para verificar que mqtt_to_mongodb.py los captura y guarda en MongoDB
"""

import json
import time
import random
import paho.mqtt.client as mqtt

# Configuración MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Crear cliente MQTT
client = mqtt.Client()

def connect_mqtt():
    """Conecta a MQTT"""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Conectado a MQTT broker")
        else:
            print(f"Error conexión: {rc}")
    
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

def send_environment_data():
    """Envía datos de temperatura y humedad"""
    data = {
        "temperature": round(random.uniform(18, 30), 2),
        "humidity": round(random.uniform(30, 80), 2),
        "soil_status": "WET" if random.random() > 0.5 else "DRY"
    }
    client.publish("nave/sensores/temperatura", json.dumps(data))
    print(f"Ambiente: {data}")

def send_fire_data():
    """Envía datos de detector de fuego"""
    data = {
        "fire_detected": random.random() < 0.05,  # 5% probabilidad
        "status": "ALARMA" if random.random() < 0.05 else "NORMAL"
    }
    client.publish("nave/sensores/fuego", json.dumps(data))
    print(f"Fuego: {data}")

def send_meteor_data():
    """Envía datos de detector de meteoros"""
    data = {
        "meteor_detected": random.random() < 0.10,  # 10% probabilidad
        "distance": round(random.uniform(100, 1000), 2),
        "velocity": round(random.uniform(20, 72), 2)
    }
    client.publish("nave/sensores/meteoros", json.dumps(data))
    print(f"Meteoro: {data}")

def send_turret_data():
    """Envía datos de torreta"""
    data = {
        "horizontal_angle": round(random.uniform(0, 360), 2),
        "vertical_angle": round(random.uniform(0, 90), 2),
        "is_rotating": random.random() < 0.7,
        "rotation_speed": round(random.uniform(0, 10), 2)
    }
    client.publish("nave/sensores/torreta", json.dumps(data))
    print(f"Torreta: {data}")

def send_gate_data():
    """Envía datos de puerta"""
    state = random.choice(["open", "closed", "opening", "closing"])
    data = {
        "state": state,
        "percentage": 100 if state == "open" else 0 if state == "closed" else round(random.uniform(10, 90), 2),
        "is_moving": state in ["opening", "closing"]
    }
    client.publish("nave/sensores/puerta", json.dumps(data))
    print(f"Puerta: {data}")

def send_alert_data():
    """Envía alertas"""
    alert_types = [
        {"type": "FIRE_ALERT", "message": "¡Fuego detectado en la nave!"},
        {"type": "METEOR_ALERT", "message": "Meteoro detectado aproximándose"},
        {"type": "TEMPERATURE_ALERT", "message": "Temperatura demasiado alta"},
    ]
    alert = random.choice(alert_types)
    client.publish("nave/alertas/criticas", json.dumps(alert))
    print(f"Alerta: {alert}")

def main():
    """Loop principal"""
    print("Iniciando prueba de MQTT...")
    connect_mqtt()
    
    time.sleep(1)  # Espera a conectar
    
    try:
        counter = 0
        while True:
            counter += 1
            print(f"\n--- Ciclo {counter} ---")
            
            # Envía datos cada 2 segundos
            send_environment_data()
            time.sleep(0.5)
            
            send_fire_data()
            time.sleep(0.5)
            
            send_meteor_data()
            time.sleep(0.5)
            
            send_turret_data()
            time.sleep(0.5)
            
            send_gate_data()
            time.sleep(0.5)
            
            # Alertas cada 10 ciclos
            if counter % 10 == 0:
                send_alert_data()
            
            time.sleep(1)  # Espera antes del próximo ciclo
    
    except KeyboardInterrupt:
        print("\n\nPrueba finalizada")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()