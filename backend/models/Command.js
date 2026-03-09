const mongoose = require("mongoose");

const commandSchema = new mongoose.Schema({
  topic: {
    type: String,
    required: true,
    trim: true,
  },
  command: {
    type: String,
    required: true,
    trim: true,
  },
  value: {
    type: mongoose.Schema.Types.Mixed,
    default: null,
  },
  timestamp: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.model("Command", commandSchema);