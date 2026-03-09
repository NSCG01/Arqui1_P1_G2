import { useEffect, useMemo, useState } from "react";
import nave from "./assets/nave.png";
import "./styles/dashboard.css";
import {
  deriveStatus,
  getSensors,
  getStats,
  mapSensorData,
  normalizeStats,
  sendCommand,
  sendMessage,
} from "./services/api";

export default function App() {
  const [gas, setGas] = useState(0);
  const [temp, setTemp] = useState(0);
  const [humedad, setHumedad] = useState(0);
  const [distancia, setDistancia] = useState(0);
  const [angulo, setAngulo] = useState(120);
  const [mensaje, setMensaje] = useState("");
  const [animacion, setAnimacion] = useState("");
  const [mensajeEnviado, setMensajeEnviado] = useState(false);
  const [alertaGeneral, setAlertaGeneral] = useState(false);
  const [anguloAnim, setAnguloAnim] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({
    disparos: 0,
    tiempoCamuflaje: "00:00:00",
    alertasGas: 0,
    alertasMeteorito: 0,
    totalLecturas: 0,
  });

  const estado = useMemo(() => {
    return deriveStatus({ gas, distancia });
  }, [gas, distancia]);

  useEffect(() => {
    setAlertaGeneral(estado !== "OPERATIVA");
  }, [estado]);

  useEffect(() => {
    let activo = true;

    const loadDashboard = async () => {
      try {
        if (!activo) return;
        setError("");

        const [sensorData, statsData] = await Promise.all([
          getSensors(),
          getStats(),
        ]);

        if (!activo) return;

        const sensores = mapSensorData(sensorData);
        const estadisticas = normalizeStats(statsData);

        setGas(sensores.gas);
        setTemp(sensores.temp);
        setHumedad(sensores.humedad);
        setDistancia(sensores.distancia);
        setStats(estadisticas);
      } catch (err) {
        if (!activo) return;
        setError(err.message || "No se pudo cargar el dashboard");
      } finally {
        if (activo) {
          setCargando(false);
        }
      }
    };

    loadDashboard();
    const interval = setInterval(loadDashboard, 3000);

    return () => {
      activo = false;
      clearInterval(interval);
    };
  }, []);

  function triggerAnim(tipo) {
    setAnimacion(tipo);

    setTimeout(() => {
      setAnimacion("");
    }, 800);
  }

  const handleAngleChange = async (value) => {
    setAngulo(value);
    setAnguloAnim(true);
    setTimeout(() => setAnguloAnim(false), 500);

    try {
      await sendCommand({
        topic: "nave/actuadores/torreta",
        command: "rotar",
        value: Number(value),
      });
    } catch (err) {
      setError(err.message || "No se pudo mover la torreta");
    }
  };

  const handleShoot = async () => {
    triggerAnim("disparo");

    try {
      await sendCommand({
        topic: "nave/actuadores/torreta",
        command: "disparar",
        value: true,
      });

      setStats((prev) => ({
        ...prev,
        disparos: prev.disparos + 1,
      }));
    } catch (err) {
      setError(err.message || "No se pudo enviar el disparo");
    }
  };

  const handleGate = async (action) => {
    triggerAnim("mover");

    try {
      await sendCommand({
        topic: "nave/actuadores/compuertas",
        command: action,
        value: action,
      });
    } catch (err) {
      setError(err.message || `No se pudo ${action} la compuerta`);
    }
  };

  const handleCamouflage = async () => {
    triggerAnim("camuflaje");

    try {
      await sendCommand({
        topic: "nave/actuadores/camuflaje",
        command: "activar",
        value: true,
      });
    } catch (err) {
      setError(err.message || "No se pudo activar el camuflaje");
    }
  };

  const handleSendMessage = async () => {
    const text = mensaje.trim();
    if (!text) return;

    try {
      await sendMessage(text);
      setMensajeEnviado(true);
      setTimeout(() => setMensajeEnviado(false), 800);
      setMensaje("");
    } catch (err) {
      setError(err.message || "No se pudo enviar el mensaje");
    }
  };

  return (
    <div className={`dashboard ${alertaGeneral ? "alerta-general" : ""}`}>
      <h1 className="titulo-nave">HALCÓN MILENARIO</h1>

      {cargando && <p>Cargando datos...</p>}
      {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}

      <div className="grid-container">
        {/* PANEL IZQUIERDO */}
        <div className="panel left">
          <SectionTitle title="ESTADO GENERAL" />
          <EstadoNave estado={estado} />

          <SectionTitle title="SENSORES" />
          <StatusBar label="Gas" value={gas} unit="%" />
          <StatusBar label="Temperatura" value={temp} unit="°C" />
          <StatusBar label="Humedad" value={humedad} unit="%" />
          <Proximidad distancia={distancia} />

          <SectionTitle title="INDICADORES LED" />
          <Led color="green" active={estado === "OPERATIVA"} />
          <Led color="yellow" active={estado === "ALERTA"} />
          <Led color="red" active={estado === "EMERGENCIA"} />
          <Led color="blue" active={animacion === "camuflaje"} />
        </div>

        {/* CENTRO */}
        <div className="panel center">
          <div className="nave-container">
            <div className="nombre-nave">G-2</div>

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
            onChange={(e) => handleAngleChange(e.target.value)}
            className={anguloAnim ? "angulo-activo" : ""}
          />
          <p>Ángulo: {angulo}°</p>

          <button className="btn" onClick={handleShoot}>
            Disparar
          </button>

          <SectionTitle title="COMPUERTAS" />
          <button className="btn" onClick={() => handleGate("abrir")}>
            Abrir
          </button>

          <button className="btn" onClick={() => handleGate("cerrar")}>
            Cerrar
          </button>

          <SectionTitle title="CAMUFLAJE" />
          <button className="btn blue" onClick={handleCamouflage}>
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
          <button className="btn" onClick={handleSendMessage}>
            Enviar
          </button>

          <SectionTitle title="ESTADÍSTICAS" />
          <StatItem label="Disparos" value={stats.disparos} />
          <StatItem label="Tiempo camuflaje" value={stats.tiempoCamuflaje} />
          <StatItem label="Alertas gas" value={stats.alertasGas} />
          <StatItem label="Alertas meteorito" value={stats.alertasMeteorito} />
          <StatItem label="Total lecturas" value={stats.totalLecturas} />
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

function StatusBar({ label, value, unit = "%" }) {
  const numericValue = Number(value) || 0;
  const critico = numericValue >= 70;

  const getColor = () => {
    if (numericValue < 40) return "#00ff88";
    if (numericValue < 70) return "#ffaa00";
    return "#ff0033";
  };

  const widthValue = Math.max(0, Math.min(numericValue, 100));

  return (
    <div className={`status-bar ${critico ? "sensor-critico" : ""}`}>
      <span>
        {label} - {numericValue}
        {unit}
      </span>

      <div className="bar-background">
        <div
          className="bar-fill"
          style={{
            width: `${widthValue}%`,
            backgroundColor: getColor(),
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