const express = require("express")
const router = express.Router()

const SensorReading = require("../models/sensorReading")

router.get("/", async (req, res) => {
    
    const data = await SensorReading
        .find()
        .sort({timestamp:-1})
        .limit(50)
    res.json(data)
})

module.exports = router