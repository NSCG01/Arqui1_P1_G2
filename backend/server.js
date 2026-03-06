const express = require("express")
const cors = require("cors")
const connectMongo = require("./config/mongo")

require("./config/mqtt")

const sensorsRoutes = require("./routes/sensors")
const commandsRoutes = require("./routes/commands")
const statsRoutes = require("./routes/stats")

const app = express()

app.use(cors())
app.use(express.json())   // MUY IMPORTANTE

connectMongo()

app.use("/sensors", sensorsRoutes)
app.use("/commands", commandsRoutes)
app.use("/stats", statsRoutes)

app.get("/", (req,res)=>{
    res.send("Backend nave activo")
})

app.listen(3000, ()=>{
    console.log("Servidor corriendo en puerto 3000")
})