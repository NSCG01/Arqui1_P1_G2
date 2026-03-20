"""
Gestor centralizado de MongoDB para todos los sensores
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo import ASCENDING

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "Arqui1_G2"

class MongoDBManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance.client = MongoClient(MONGODB_URI)
            cls._instance.db = cls._instance.client[DB_NAME]
            cls._instance._initialize_collections()
        return cls._instance
    
    def _initialize_collections(self):
        """Crea las colecciones si no existen"""
        
        collections = {
            "sensor_readings": "timestamp",
            "events": "timestamp",
            "commands": "timestamp",
            "messages": "timestamp"
        }
        
        for collection_name, index_field in collections.items():
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                self.db[collection_name].create_index([(index_field, ASCENDING)])
                print(f"✓ Colección '{collection_name}' creada")
    
    # ========== SENSOR READINGS ==========
    def save_sensor_reading(self, sensor_type, data):
        """Guarda lecturas de sensores"""
        document = {
            "sensor_type": sensor_type,
            "timestamp": datetime.now(),
            **data
        }
        
        result = self.db.sensor_readings.insert_one(document)
        print(f"📊 {sensor_type}: Guardado")
        return result.inserted_id
    
    # ========== EVENTS ==========
    def save_event(self, event_type, description, severity="INFO"):
        """Guarda eventos del sistema"""
        document = {
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now()
        }
        
        result = self.db.events.insert_one(document)
        print(f"⚠️ Evento: {event_type}")
        return result.inserted_id
    
    # ========== COMMANDS ==========
    def save_command(self, command_type, status, details=None):
        """Guarda comandos ejecutados"""
        document = {
            "command_type": command_type,
            "status": status,
            "timestamp": datetime.now(),
            "details": details or {}
        }
        
        result = self.db.commands.insert_one(document)
        print(f"🎮 Comando: {command_type}")
        return result.inserted_id
    
    # ========== MESSAGES ==========
    def save_message(self, message, room="CONTROL_ROOM", sender="SYSTEM"):
        """Guarda mensajes"""
        document = {
            "message": message,
            "room": room,
            "sender": sender,
            "timestamp": datetime.now()
        }
        
        result = self.db.messages.insert_one(document)
        print(f"💬 Mensaje: {sender}")
        return result.inserted_id
    
    def close(self):
        """Cierra la conexión"""
        self.client.close()
        print("MongoDB desconectado")

# Instancia global
db_manager = MongoDBManager()