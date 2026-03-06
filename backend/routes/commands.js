const express = require("express")
const router = express.Router()

const mqttClient = require("../config/mqtt")

router.post("/", (req,res)=>{

    const { topic, value } = req.body

    console.log("Comando recibido:", topic, value)

    mqttClient.publish(topic, String(value))

    res.json({
        status:"comando enviado"
    })

})

module.exports = router