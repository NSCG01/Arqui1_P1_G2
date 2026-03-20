const mqtt = require("mqtt");
const SensorReading = require("../models/sensorReading");

const client = mqtt.connect("mqtt://localhost:1883");

client.on("connect", () => {
  console.log("Conectado a MQTT");
  client.subscribe("nave/sensores/#");
});

client.on("message", async (topic, message) => {
  try {
    const text = message.toString();
    console.log("Mensaje recibido:", topic, text);

    let doc = {
      sensor: topic,
      timestamp: new Date(),
    };

    if (topic === "nave/sensores/color") {
      const payload = JSON.parse(text);

      doc.value = 1; 
      doc.color = payload.color || "UNKNOWN";
      doc.sequence = payload.sequence || [];
      doc.camouflage = Boolean(payload.camouflage);
      doc.raw = payload;
      if (payload.timestamp) {
        doc.timestamp = new Date(payload.timestamp);
      }
    } else {
      const numericValue = parseFloat(text);
      doc.value = Number.isNaN(numericValue) ? 0 : numericValue;
    }

    const data = new SensorReading(doc);
    await data.save();
  } catch (error) {
    console.error("Error procesando mensaje MQTT:", error.message);
  }
});

module.exports = client;