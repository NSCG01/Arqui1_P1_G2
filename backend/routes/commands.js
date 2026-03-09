const express = require("express");
const router = express.Router();
const mqttClient = require("../config/mqtt");
const Command = require("../models/Command");

router.post("/", async (req, res) => {
  try {
    const { topic, command, value } = req.body;

    if (!topic || !command) {
      return res.status(400).json({
        error: "Los campos 'topic' y 'command' son obligatorios",
      });
    }

    const payload = JSON.stringify({
      command,
      value,
      timestamp: new Date().toISOString(),
    });

    mqttClient.publish(topic, payload);

    const newCommand = new Command({
      topic,
      command,
      value,
    });

    await newCommand.save();

    res.json({
      message: "Comando enviado y guardado correctamente",
      command: newCommand,
    });
  } catch (error) {
    console.error("Error al enviar comando:", error.message);
    res.status(500).json({
      error: "Error al enviar el comando",
    });
  }
});

router.get("/", async (req, res) => {
  try {
    const commands = await Command.find().sort({ timestamp: -1 }).limit(50);
    res.json(commands);
  } catch (error) {
    console.error("Error al obtener comandos:", error.message);
    res.status(500).json({
      error: "Error al obtener comandos",
    });
  }
});

module.exports = router;