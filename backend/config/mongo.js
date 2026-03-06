const mongoose = require("mongoose")

const connectMongo = async () => {
    await mongoose.connect("mongodb://localhost:27017/nave")
    console.log("MongoDB conectado")
}

module.exports = connectMongo