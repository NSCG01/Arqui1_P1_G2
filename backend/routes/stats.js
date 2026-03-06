const express = require("express")
const router = express.Router()

const SensorReading = require("../models/sensorReading")

router.get("/", async (req,res)=>{

    const total = await SensorReading.countDocuments()

    res.json({
        totalLecturas: total
    })
})

module.exports = router