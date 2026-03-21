#include <Wire.h>
#include <DHT.h>

// ==================== CONFIGURACIÓN I2C ====================
#define I2C_ADDRESS 0x08

// ==================== PINES ====================
// Sensores
#define DHT_PIN 4
#define YL69_PIN 5
#define MQ135_PIN 34  // Analógico

// Actuadores
#define FAN_PIN 12
#define BUZZER_GENERAL 13
#define BUZZER_METEOR 14
#define LASER_PIN 15
#define LED_YELLOW_METEOR 16
#define LED_RED_FIRE 17
#define LED_BLUE_CAMO 18

// ==================== TIPOS DE DATOS PARA I2C ====================
#define TYPE_DHT11 1
#define TYPE_YL69 2
#define TYPE_MQ135 3
#define TYPE_FIRE_STATUS 4
#define TYPE_METEOR_STATUS 5

// ==================== VARIABLES GLOBALES ====================
DHT dht(DHT_PIN, DHT11);

// Datos de sensores
float temperature = 0;
float humidity = 0;
int soil_moisture = 0;  // 0=WET, 1=DRY
int gas_level = 0;
bool fire_detected = false;

// Estados
bool meteor_alert_active = false;
bool camouflage_active = false;

// Timers
unsigned long last_sensor_read = 0;
const unsigned long SENSOR_INTERVAL = 3000;  // 3 segundos

// Variables para patrón de buzzer de meteorito
int current_buzzer_pattern = 0;  // 0=OFF, 1=FAR, 2=NEAR, 3=CRITICAL
unsigned long last_buzzer_update = 0;
int near_beep_count = 0;
bool buzzer_state = false;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 I2C Slave iniciando...");
  
  // Inicializar I2C
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  
  // Inicializar sensores
  dht.begin();
  
  // Configurar pines
  pinMode(YL69_PIN, INPUT);
  pinMode(MQ135_PIN, INPUT);
  
  pinMode(FAN_PIN, OUTPUT);
  pinMode(BUZZER_GENERAL, OUTPUT);
  pinMode(BUZZER_METEOR, OUTPUT);
  pinMode(LASER_PIN, OUTPUT);
  pinMode(LED_YELLOW_METEOR, OUTPUT);
  pinMode(LED_RED_FIRE, OUTPUT);
  pinMode(LED_BLUE_CAMO, OUTPUT);
  
  // Estado inicial
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(BUZZER_GENERAL, LOW);
  digitalWrite(BUZZER_METEOR, LOW);
  digitalWrite(LASER_PIN, LOW);
  digitalWrite(LED_YELLOW_METEOR, LOW);
  digitalWrite(LED_RED_FIRE, LOW);
  digitalWrite(LED_BLUE_CAMO, LOW);
  
  Serial.println("ESP32 I2C Slave listo");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  // Leer sensores periódicamente
  unsigned long now = millis();
  if (now - last_sensor_read >= SENSOR_INTERVAL) {
    readSensors();
    last_sensor_read = now;
  }
  
  // Actualizar patrón de buzzer de meteorito
  updateMeteorBuzzer();
  
  delay(10);
}

// ==================== LECTURA DE SENSORES ====================
void readSensors() {
  // Leer DHT11
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  if (!isnan(h) && !isnan(t)) {
    humidity = h;
    temperature = t;
    Serial.printf("DHT: T=%.1f C, H=%.1f %%\n", temperature, humidity);
  } else {
    Serial.println("Error DHT11");
  }
  
  // Leer YL-69 (digital)
  soil_moisture = digitalRead(YL69_PIN);
  Serial.printf("Suelo: %s\n", soil_moisture == 0 ? "WET" : "DRY");
  
  // Leer MQ-135 (analógico)
  gas_level = analogRead(MQ135_PIN);
  
  // Umbral ajustable para detección de incendio (0-4095)
  int fire_threshold = 800;
  fire_detected = (gas_level > fire_threshold);
  
  Serial.printf("Gas: %d, FIRE: %s\n", gas_level, fire_detected ? "YES" : "NO");
  
  // Controlar ventiladores y LED rojo según detección de fuego
  digitalWrite(FAN_PIN, fire_detected ? HIGH : LOW);
  digitalWrite(LED_RED_FIRE, fire_detected ? HIGH : LOW);
}

// ==================== MANEJAR PATRONES DE BUZZER METEOR ====================
void handleMeteorBuzzer(int pattern) {
  current_buzzer_pattern = pattern;
  
  // Si es CRITICAL (3), activar continuo
  if (pattern == 3) {
    digitalWrite(BUZZER_METEOR, HIGH);
  }
  // Si es OFF (0), apagar
  else if (pattern == 0) {
    digitalWrite(BUZZER_METEOR, LOW);
    near_beep_count = 0;
    buzzer_state = false;
  }
  // Para otros patrones, se manejan en updateMeteorBuzzer()
  else {
    digitalWrite(BUZZER_METEOR, LOW);
    near_beep_count = 0;
    buzzer_state = false;
    last_buzzer_update = millis();
  }
}

void updateMeteorBuzzer() {
  unsigned long now = millis();
  
  switch(current_buzzer_pattern) {
    case 1:  // FAR: 1 beep cada 2 segundos (beep de 200ms)
      if (now - last_buzzer_update >= 2000) {
        // Beep de 200ms
        digitalWrite(BUZZER_METEOR, HIGH);
        delay(200);
        digitalWrite(BUZZER_METEOR, LOW);
        last_buzzer_update = now;
      }
      break;
      
    case 2:  // NEAR: 3 beeps rápidos cada segundo
      if (now - last_buzzer_update >= 1000) {
        near_beep_count = 0;
        last_buzzer_update = now;
      }
      
      if (near_beep_count < 3) {
        unsigned long beep_start = last_buzzer_update + (near_beep_count * 200);
        
        if (now - beep_start < 80) {
          digitalWrite(BUZZER_METEOR, HIGH);
        } else if (now - beep_start < 150) {
          digitalWrite(BUZZER_METEOR, LOW);
        } else {
          near_beep_count++;
        }
      }
      break;
      
    case 3:  // CRITICAL: ya está siempre HIGH en handleMeteorBuzzer
      // Mantener encendido
      break;
      
    default:  // OFF
      digitalWrite(BUZZER_METEOR, LOW);
      break;
  }
}

// ==================== RECIBIR COMANDOS DE RPi ====================
void receiveEvent(int howMany) {
  while (Wire.available()) {
    char cmd = Wire.read();
    
    switch(cmd) {
      case 'B':  // Buzzer general control (emergencia, disparo)
        if (Wire.available()) {
          int state = Wire.read();
          digitalWrite(BUZZER_GENERAL, state);
          Serial.printf("Buzzer General: %s\n", state ? "ON" : "OFF");
        }
        break;
        
      case 'Z':  // Buzzer meteor (patrones)
        if (Wire.available()) {
          int pattern = Wire.read();
          handleMeteorBuzzer(pattern);
          Serial.printf("Buzzer Meteor Pattern: %d\n", pattern);
        }
        break;
        
      case 'L':  // Laser control (torreta)
        if (Wire.available()) {
          int state = Wire.read();
          digitalWrite(LASER_PIN, state);
          Serial.printf("Laser: %s\n", state ? "ON" : "OFF");
        }
        break;
        
      case 'Y':  // LED Amarillo Meteorito
        if (Wire.available()) {
          int state = Wire.read();
          digitalWrite(LED_YELLOW_METEOR, state);
          meteor_alert_active = state;
          Serial.printf("LED Amarillo Meteor: %s\n", state ? "ON" : "OFF");
        }
        break;
        
      case 'C':  // LED Azul Camuflaje
        if (Wire.available()) {
          int state = Wire.read();
          digitalWrite(LED_BLUE_CAMO, state);
          camouflage_active = state;
          Serial.printf("LED Azul Camuflaje: %s\n", state ? "ON" : "OFF");
        }
        break;
        
      default:
        Serial.printf("Comando desconocido: %c\n", cmd);
        break;
    }
  }
}

// ==================== ENVIAR DATOS A RPi ====================
void requestEvent() {
  byte buffer[32];
  int idx = 0;
  
  // Datos DHT11 (temperatura y humedad)
  buffer[idx++] = TYPE_DHT11;
  buffer[idx++] = (int)(temperature * 10);  // Enviar como entero *10
  buffer[idx++] = (int)(humidity * 10);
  
  // Datos YL-69 (humedad suelo)
  buffer[idx++] = TYPE_YL69;
  buffer[idx++] = soil_moisture;
  
  // Datos MQ-135 (nivel de gas)
  buffer[idx++] = TYPE_MQ135;
  buffer[idx++] = (gas_level >> 8) & 0xFF;  // High byte
  buffer[idx++] = gas_level & 0xFF;         // Low byte
  
  // Estado de incendio
  buffer[idx++] = TYPE_FIRE_STATUS;
  buffer[idx++] = fire_detected ? 1 : 0;
  
  // Estado de alerta meteorito (para feedback)
  buffer[idx++] = TYPE_METEOR_STATUS;
  buffer[idx++] = meteor_alert_active ? 1 : 0;
  
  Wire.write(buffer, idx);
  
  // Debug opcional (comentar si causa problemas)
  // Serial.printf("Enviados %d bytes\n", idx);
}
