const express = require("express");
const router = express.Router();
const Event = require("../models/Event");

router.get("/", async (req, res) => {
  try {
    const events = await Event.find().sort({ timestamp: -1 }).limit(100);
    res.json(events);
  } catch (error) {
    console.error("Error al obtener eventos:", error.message);
    res.status(500).json({
      error: "Error al obtener eventos",
    });
  }
});

router.post("/", async (req, res) => {
  try {
    const { type, description, severity, source, data } = req.body;

    if (!type) {
      return res.status(400).json({
        error: "El campo 'type' es obligatorio",
      });
    }

    const newEvent = new Event({
      type,
      description,
      severity,
      source,
      data,
    });

    await newEvent.save();

    res.status(201).json({
      message: "Evento guardado correctamente",
      event: newEvent,
    });
  } catch (error) {
    console.error("Error al guardar evento:", error.message);
    res.status(500).json({
      error: "Error al guardar evento",
    });
  }
});

module.exports = router;