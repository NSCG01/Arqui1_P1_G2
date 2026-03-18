import time
import json
import Adafruit_DHT
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

# ========================
# CONFIGURACIÓN GPIO (BCM)
# ========================
GPIO.setmode(GPIO.BCM)

# Sensor DHT
DHT_SENSOR = Adafruit_DHT.DHT11   # cambia a DHT22 si usas ese
DHT_PIN = 4  # GPIO4

# Sensor de humedad de suelo YL-69
SOIL_PIN = 22  # GPIO22
GPIO.setup(SOIL_PIN, GPIO.IN)

# ========================
# CONFIGURACIÓN MQTT
# ========================
MQTT_BROKER = "localhost"   # IP del broker (ej: "192.168.1.100")
MQTT_PORT = 1883

TOPIC_DATA = "nave/sensores/ambiente"
TOPIC_ALERT = "nave/alertas/criticas"

client = mqtt.Client()

# ========================
# EVENTOS MQTT
# ========================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado a MQTT")
    else:
        print(f"❌ Error de conexión MQTT: {rc}")

def on_disconnect(client, userdata, rc):
    print("⚠️ Desconectado de MQTT")

client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Conectar
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# ========================
# FUNCIONES
# ========================
def read_dht():
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    return temperature, humidity

def read_soil():
    return GPIO.input(SOIL_PIN)

def check_alerts(temp, hum):
    alerts = []

    if temp is not None:
        if temp > 35:
            alerts.append("TEMP_ALTA")
        elif temp < 10:
            alerts.append("TEMP_BAJA")

    if hum is not None:
        if hum < 20:
            alerts.append("HUM_BAJA")
        elif hum > 80:
            alerts.append("HUM_ALTA")

    return alerts

# ========================
# LOOP PRINCIPAL
# ========================
try:
    print("🚀 Sistema de Monitoreo Ambiental iniciado...\n")

    while True:
        temperature, humidity = read_dht()
        soil = read_soil()

        soil_status = "SECO" if soil == 1 else "HUMEDO"
        alerts = check_alerts(temperature, humidity)

        data = {
            "temperatura": temperature,
            "humedad": humidity,
            "suelo": soil_status,
            "alertas": alerts,
            "timestamp": int(time.time())
        }

        # ========================
        # PUBLICAR DATOS NORMALES
        # ========================
        client.publish(TOPIC_DATA, json.dumps(data), qos=0)

        # ========================
        # PUBLICAR ALERTAS CRÍTICAS
        # ========================
        if alerts:
            alert_msg = {
                "tipo": "AMBIENTAL",
                "alertas": alerts,
                "timestamp": int(time.time())
            }
            client.publish(TOPIC_ALERT, json.dumps(alert_msg), qos=1)

        # ========================
        # LOG CONSOLA
        # ========================
        print("===== LECTURA =====")
        
        if temperature is not None and humidity is not None:
            print(f"🌡 Temperatura: {temperature:.1f}°C")
            print(f"💧 Humedad: {humidity:.1f}%")
        else:
            print("⚠️ Error leyendo DHT")

        print(f"🌱 Suelo: {soil_status}")

        if alerts:
            print("🚨 ALERTAS:")
            for a in alerts:
                print(f" - {a}")
        else:
            print("✅ Todo normal")

        print("------------------------\n")

        time.sleep(5)

except KeyboardInterrupt:
    print("🛑 Sistema detenido por usuario")

finally:
    client.loop_stop()
    client.disconnect()
    GPIO.cleanup()