import smbus2
import time
import threading
import json
import paho.mqtt.client as mqtt

class ESP32Interface:
    """Interfaz I2C para comunicarse con ESP32"""
    
    # Dirección I2C
    I2C_ADDRESS = 0x08
    I2C_BUS = 1  # Raspberry Pi I2C bus 1 (GPIO 2=SDA, GPIO 3=SCL)
    
    # Tipos de datos
    TYPE_DHT11 = 1
    TYPE_YL69 = 2
    TYPE_MQ135 = 3
    TYPE_FIRE_STATUS = 4
    TYPE_METEOR_STATUS = 5
    
    # Comandos
    CMD_BUZZER_GENERAL = ord('B')
    CMD_BUZZER_METEOR = ord('Z')
    CMD_LASER = ord('L')
    CMD_LED_YELLOW = ord('Y')
    CMD_LED_BLUE = ord('C')
    
    def __init__(self):
        # Inicializar I2C
        self.bus = None
        try:
            self.bus = smbus2.SMBus(self.I2C_BUS)
            print("I2C bus iniciado")
        except Exception as e:
            print(f"Error iniciando I2C: {e}")
            print("   Verifica que el ESP32 esté conectado y la dirección I2C correcta")
        
        # Datos recibidos (valores por defecto)
        self.temperature = 25.0  # Valor por defecto
        self.humidity = 50.0     # Valor por defecto
        self.soil_moisture = 0   # 0=WET, 1=DRY
        self.gas_level = 0
        self.fire_detected = False
        self.meteor_alert = False
        
        # MQTT
        self.client = mqtt.Client()
        try:
            self.client.connect("localhost", 1883, 60)
            self.client.loop_start()
            print(" MQTT conectado")
        except Exception as e:
            print(f"Error MQTT: {e}")
        
        # Thread para lectura periódica
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.last_successful_read = 0
        
        print("ESP32 Interface iniciada")
        print("Esperando datos de ESP32...")

    def read_sensors(self):
        """Leer datos de ESP32 por I2C con timeout"""
        if self.bus is None:
            return False
        
        try:
            # Intentar leer con timeout usando try-except
            with self.lock:
                # timeout implícito: si ESP32 no responde, lanzará excepción
                data = self.bus.read_i2c_block_data(self.I2C_ADDRESS, 0, 32)
            
            if len(data) < 5:
                return False
                
            idx = 0
            while idx < len(data) - 1:
                data_type = data[idx]
                idx += 1
                
                if data_type == self.TYPE_DHT11:
                    if idx + 1 < len(data):
                        self.temperature = data[idx] / 10.0
                        self.humidity = data[idx + 1] / 10.0
                        idx += 2
                        
                elif data_type == self.TYPE_YL69:
                    if idx < len(data):
                        self.soil_moisture = data[idx]
                        idx += 1
                        
                elif data_type == self.TYPE_MQ135:
                    if idx + 1 < len(data):
                        self.gas_level = (data[idx] << 8) | data[idx + 1]
                        idx += 2
                        
                elif data_type == self.TYPE_FIRE_STATUS:
                    if idx < len(data):
                        self.fire_detected = (data[idx] == 1)
                        idx += 1
                        
                elif data_type == self.TYPE_METEOR_STATUS:
                    if idx < len(data):
                        self.meteor_alert = (data[idx] == 1)
                        idx += 1
                    else:
                        break
            
            self.last_successful_read = time.time()
            return True
            
        except Exception as e:
            # Error I2C - puede ser que ESP32 no esté listo
            if time.time() - self.last_successful_read > 10:
                print(f"Error I2C lectura (más de 10s sin datos): {e}")
            return False
    
    def send_command(self, cmd, value=None):
        """Enviar comando a ESP32"""
        if self.bus is None:
            return False
        
        try:
            with self.lock:
                if value is not None:
                    self.bus.write_i2c_block_data(self.I2C_ADDRESS, cmd, [value])
                else:
                    self.bus.write_byte(self.I2C_ADDRESS, cmd)
            return True
        except Exception as e:
            print(f" Error enviando comando {chr(cmd)}: {e}")
            return False
    
    # ==================== ACTUADORES ====================
    def set_buzzer_general(self, state):
        """Controlar buzzer general (emergencia, disparo)"""
        self.send_command(self.CMD_BUZZER_GENERAL, 1 if state else 0)
    
    def set_buzzer_meteor_pattern(self, pattern):
        """Controlar buzzer de meteorito: 0=OFF, 1=FAR, 2=NEAR, 3=CRITICAL"""
        self.send_command(self.CMD_BUZZER_METEOR, pattern)
    
    def set_laser(self, state):
        """Controlar LED láser de torreta"""
        self.send_command(self.CMD_LASER, 1 if state else 0)
    
    def set_led_yellow_meteor(self, state):
        """Controlar LED amarillo de alerta meteorito"""
        self.send_command(self.CMD_LED_YELLOW, 1 if state else 0)
    
    def set_led_blue_camo(self, state):
        """Controlar LED azul de camuflaje"""
        self.send_command(self.CMD_LED_BLUE, 1 if state else 0)
    
    # ==================== LOOP DE LECTURA ====================
    def sensor_loop(self):
        """Loop para lectura periódica de sensores"""
        read_count = 0
        while not self.stop_event.is_set():
            if self.read_sensors():
                if read_count % 5 == 0:  # Publicar solo cada 5 lecturas (15s) para no saturar
                    self.publish_sensor_data()
                read_count += 1
            else:
                # Si falla la lectura, mantener valores anteriores
                pass
            
            self.stop_event.wait(3)  # Leer cada 3 segundos
    
    def publish_sensor_data(self):
        """Publicar datos a MQTT"""
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Temperatura
        try:
            self.client.publish("nave/sensores/temperatura", json.dumps({
                "value": self.temperature,
                "timestamp": ts
            }))
        except: pass
        
        # Humedad ambiente
        try:
            self.client.publish("nave/sensores/ambiente", json.dumps({
                "value": self.humidity,
                "timestamp": ts
            }))
        except: pass
        
        # Humedad suelo
        try:
            self.client.publish("nave/sensores/humedad", json.dumps({
                "value": "DRY" if self.soil_moisture else "WET",
                "raw": self.soil_moisture,
                "timestamp": ts
            }))
        except: pass
        
        # Gas
        try:
            self.client.publish("nave/sensores/gas", json.dumps({
                "value": self.gas_level,
                "status": "FIRE" if self.fire_detected else "SAFE",
                "timestamp": ts
            }))
        except: pass
    
    # ==================== MÉTODOS PARA LCD ====================
    def get_env_status(self):
        """Obtener estado ambiental formateado para LCD"""
        soil_status = "DRY" if self.soil_moisture else "WET"
        return f"T:{self.temperature:.0f}C H:{self.humidity:.0f}% S:{soil_status}"
    
    def get_fire_status(self):
        """Obtener estado de incendio"""
        return "FIRE!" if self.fire_detected else "SAFE"
    
    # ==================== START/STOP ====================
    def start(self):
        print("ESP32 Interface iniciada")
        threading.Thread(target=self.sensor_loop, daemon=True).start()
    
    def stop(self):
        print("ESP32 Interface detenida")
        self.stop_event.set()
        # Apagar todos los actuadores
        self.set_buzzer_general(False)
        self.set_buzzer_meteor_pattern(0)
        self.set_laser(False)
        self.set_led_yellow_meteor(False)
        self.set_led_blue_camo(False)
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except: pass