const mqtt = require("mqtt")
const SensorReading = require("../models/sensorReading")

const client = mqtt.connect("mqtt://localhost:1883")

client.on("connect", () => {
    console.log("Conectado a MQTT")

    client.subscribe("nave/sensores/#")
})

client.on("message", async (topic, message) => {
    console.log("Mensaje recibido:",topic, message.toString())

    const data = new SensorReading({
        sensor: topic,
        value: parseFloat(message.toString())
    })

    await data.save()
})

module.exports = client