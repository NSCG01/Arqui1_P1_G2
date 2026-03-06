const mongoose = require("mongoose")

const sensorSchema = new mongoose.Schema({
    sensor: String,
    value: Number,
    timestamp: {
        type: Date,
        default: Date.now
    }
})

module.exports = mongoose.model("SensorReading", sensorSchema)