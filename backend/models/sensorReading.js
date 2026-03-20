const mongoose = require("mongoose");

const sensorSchema = new mongoose.Schema({
  sensor: String,
  value: Number,
  color: String,
  sequence: [String],
  camouflage: Boolean,
  raw: mongoose.Schema.Types.Mixed,
  timestamp: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.model("SensorReading", sensorSchema);