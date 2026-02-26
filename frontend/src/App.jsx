import { useState } from "react";
import nave from "./assets/nave.png";
import "./styles/dashboard.css";
import { useEffect } from "react";
export default function App() {

  //QUEMADOS PARA PRUEBAS :)
  const [estado] = useState("OPERATIVA");
  const [gas] = useState(65);
  const [temp] = useState(40);
  const [humedad] = useState(25);
  const [distancia] = useState(500);
  const [angulo, setAngulo] = useState(120);
  const [mensaje, setMensaje] = useState("");
  const [animacion, setAnimacion] = useState("");
  const [mensajeEnviado, setMensajeEnviado] = useState(false);
  const [alertaGeneral, setAlertaGeneral] = useState(false);
  const [anguloAnim, setAnguloAnim] = useState(false);


  useEffect(() => {
   if (estado !== "OPERATIVA") {
     setAlertaGeneral(true);
   } else {
     setAlertaGeneral(false);
   }
}, [estado]);

  // ANIMACIONES DISPARAR
  function triggerAnim(tipo) {
    setAnimacion(tipo);

    setTimeout(() => {
      setAnimacion("");
    }, 800);
  }

  return (
    <div className="dashboard">

      <h1 className="titulo-nave">HALCÓN MILENARIO</h1>

      <div className="grid-container">

        {/* PANEL IZQUIERDO */}
        <div className="panel left">

          <SectionTitle title="ESTADO GENERAL" />
          <EstadoNave estado={estado} />

          <SectionTitle title="SENSORES" />
          <StatusBar label="Gas" value={gas} />
          <StatusBar label="Temperatura" value={temp} />
          <StatusBar label="Humedad" value={humedad} />
          <Proximidad distancia={distancia} />

          <SectionTitle title="INDICADORES LED" />
          <Led color="green" active />
          <Led color="yellow" />
          <Led color="red" />
          <Led color="blue" />

        </div>

        {/* CENTRO - NAVE */}
        <div className="panel center">
        <div className="nave-container">

        <div className="nombre-nave">
            G-2
        </div>

       <img 
         src={nave} 
           alt="Nave" 
              className={`nave ${animacion}`} 
                 />

               </div>
            </div>

        {/* PANEL DERECHO */}
        <div className="panel right">

          <SectionTitle title="CONTROL TORRETA" />
          <input
         type="range"
           min="0"
         max="360"
        value={angulo}
          onChange={(e) => {
          setAngulo(e.target.value);
          setAnguloAnim(true);
         setTimeout(() => setAnguloAnim(false), 500);
          }}
            className={anguloAnim ? "angulo-activo" : ""}
          />
          <p>Ángulo: {angulo}°</p>

          <button 
            className="btn"
            onClick={() => triggerAnim("disparo")}
          >
            Disparar
          </button>

          <SectionTitle title="COMPUERTAS" />
          <button 
            className="btn"
            onClick={() => triggerAnim("mover")}
          >
            Abrir
          </button>

          <button 
            className="btn"
            onClick={() => triggerAnim("mover")}
          >
            Cerrar
          </button>

          <SectionTitle title="CAMUFLAJE" />
          <button 
            className="btn blue"
            onClick={() => triggerAnim("camuflaje")}
          >
            Activar
          </button>

          <SectionTitle title="MENSAJE LCD" />
          <input
          className={mensajeEnviado ? "mensaje-enviado" : ""}
          type="text"
          maxLength="64"
          value={mensaje}
           onChange={(e) => setMensaje(e.target.value)}
            placeholder="Enviar mensaje..."
          />
          <button 
          className="btn"
           onClick={() => {
            setMensajeEnviado(true);
           setTimeout(() => setMensajeEnviado(false), 800);
            }}
              >
              Enviar
              </button>

          <SectionTitle title="ESTADÍSTICAS" />
          <StatItem label="Disparos" value="12" />
          <StatItem label="Tiempo camuflaje" value="02:15:32" />
          <StatItem label="Alertas gas" value="3" />
          <StatItem label="Alertas meteorito" value="5" />

        </div>

      </div>
    </div>
  );
}

/* COMPONENTES */

function SectionTitle({ title }) {
  return <h3 className="section-title">{title}</h3>;
}

function EstadoNave({ estado }) {
  const alerta = estado !== "OPERATIVA";

  return (
    <div className={`estado ${estado.toLowerCase()} ${alerta ? "alerta-general" : ""}`}>
      {estado}
    </div>
  );
}

function StatusBar({ label, value }) {

  const critico = value >= 70;

  const getColor = () => {
    if (value < 40) return "#00ff88";
    if (value < 70) return "#ffaa00";
    return "#ff0033";
  };

  return (
    <div className={`status-bar ${critico ? "sensor-critico" : ""}`}>
      <span>{label} - {value}%</span>
      <div className="bar-background">
        <div
          className="bar-fill"
          style={{
            width: `${value}%`,
            backgroundColor: getColor()
          }}
        />
      </div>
    </div>
  );
}

function Proximidad({ distancia }) {
  const nivel =
    distancia > 50 ? "LEJANO" :
    distancia > 20 ? "CERCANO" :
    "CRÍTICO";

  const color =
    distancia > 50 ? "#00ff88" :
    distancia > 20 ? "#ffaa00" :
    "#ff0033";

  return (
    <div className="proximidad" style={{ borderColor: color }}>
      <strong style={{ color }}>{nivel}</strong>
      <div>Distancia: {distancia} cm</div>
    </div>
  );
}

function Led({ color, active }) {
  return (
    <div className={`led ${color} ${active ? "active" : ""}`} />
  );
}

function StatItem({ label, value }) {
  return (
    <div className="stat-item">
      {label}: {value}
    </div>
  );

 
}