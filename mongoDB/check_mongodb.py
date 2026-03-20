"""
Script para verificar datos en MongoDB
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

try:
    client = MongoClient(MONGODB_URI)
    db = client["Arqui1_G2"]
    
    print("\n📊 === DATOS EN MONGODB ===\n")
    
    # Sensor readings
    count = db.sensor_readings.count_documents({})
    print(f"📈 sensor_readings: {count} documentos")
    
    last = db.sensor_readings.find_one({}, sort=[("_id", -1)])
    if last:
        print(f"   Último: {last}\n")
    
    # Events
    count = db.events.count_documents({})
    print(f"⚠️ events: {count} documentos")
    
    last = db.events.find_one({}, sort=[("_id", -1)])
    if last:
        print(f"   Último: {last}\n")
    
    # Commands
    count = db.commands.count_documents({})
    print(f"🎮 commands: {count} documentos")
    
    last = db.commands.find_one({}, sort=[("_id", -1)])
    if last:
        print(f"   Último: {last}\n")
    
    # Messages
    count = db.messages.count_documents({})
    print(f"💬 messages: {count} documentos")
    
    last = db.messages.find_one({}, sort=[("_id", -1)])
    if last:
        print(f"   Último: {last}\n")
    
except Exception as e:
    print(f"❌ Error: {e}")