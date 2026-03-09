const express = require("express");
const router = express.Router();
const mqttClient = require("../config/mqtt");
const Message = require("../models/Message");

router.post("/", async (req, res) => {
  try {
    const { message } = req.body;

    if (!message || !message.trim()) {
      return res.status(400).json({
        error: "El campo 'message' es obligatorio",
      });
    }

    const cleanMessage = message.trim();
    const topic = "nave/control/mensajes";

    mqttClient.publish(topic, cleanMessage);

    const newMessage = new Message({
      message: cleanMessage,
      topic,
    });

    await newMessage.save();

    res.json({
      message: "Mensaje enviado y guardado correctamente",
      data: newMessage,
    });
  } catch (error) {
    console.error("Error al enviar mensaje:", error.message);
    res.status(500).json({
      error: "Error al enviar el mensaje",
    });
  }
});

router.get("/", async (req, res) => {
  try {
    const messages = await Message.find().sort({ timestamp: -1 }).limit(50);
    res.json(messages);
  } catch (error) {
    console.error("Error al obtener mensajes:", error.message);
    res.status(500).json({
      error: "Error al obtener mensajes",
    });
  }
});

module.exports = router;