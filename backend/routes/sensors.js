const express = require("express");
const router = express.Router();

const SensorReading = require("../models/sensorReading");

/**
 *  lecturas recientes 
 */
router.get("/", async (req, res) => {
  try {
    const limit = Number(req.query.limit) || 50;

    const data = await SensorReading.find()
      .sort({ timestamp: -1 })
      .limit(limit);

    res.json(data);
  } catch (error) {
    console.error("Error al obtener sensores:", error.message);
    res.status(500).json({
      error: "Error al obtener lecturas de sensores",
    });
  }
});

/**
 * Devuelve el último valor detectado por cada sensor/topic
 */
router.get("/latest", async (req, res) => {
  try {
    const latestReadings = await SensorReading.aggregate([
      { $sort: { timestamp: -1 } },
      {
        $group: {
          _id: "$sensor",
          sensor: { $first: "$sensor" },
          value: { $first: "$value" },
          timestamp: { $first: "$timestamp" },
        },
      },
      { $sort: { sensor: 1 } },
    ]);

    res.json(latestReadings);
  } catch (error) {
    console.error("Error al obtener últimos sensores:", error.message);
    res.status(500).json({
      error: "Error al obtener últimos valores de sensores",
    });
  }
});

/**

 * Devuelve histórico por sensor
 */
router.get("/history/:sensor", async (req, res) => {
  try {
    const { sensor } = req.params;
    const limit = Number(req.query.limit) || 100;
    const hours = Number(req.query.hours) || 24;

    const since = new Date(Date.now() - hours * 60 * 60 * 1000);

    const data = await SensorReading.find({
      sensor: { $regex: sensor, $options: "i" },
      timestamp: { $gte: since },
    })
      .sort({ timestamp: -1 })
      .limit(limit);

    res.json(data);
  } catch (error) {
    console.error("Error al obtener historial:", error.message);
    res.status(500).json({
      error: "Error al obtener historial del sensor",
    });
  }
});

module.exports = router;