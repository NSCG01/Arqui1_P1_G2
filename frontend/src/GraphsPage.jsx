import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { getLatestSensors, getSensorHistory } from "./services/api.js";
import "./graphs.css";

const slides = [
  { key: "temperatura", title: "Temperatura - últimas 24 horas" },
  { key: "ambiente", title: "Ambiente / humedad - últimas 24 horas" },
  { key: "gas", title: "Gas - histórico reciente" },
  { key: "proximidad", title: "Proximidad - histórico reciente" },
  { key: "color", title: "Color detectado" },
];

export default function GraphsPage() {
  const [index, setIndex] = useState(0);
  const [temperaturaData, setTemperaturaData] = useState([]);
  const [ambienteData, setAmbienteData] = useState([]);
  const [gasData, setGasData] = useState([]);
  const [proximidadData, setProximidadData] = useState([]);
  const [colorDocs, setColorDocs] = useState([]);
  const [latest, setLatest] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadGraphs = async () => {
      try {
        const [
          temperatura,
          ambiente,
          gas,
          proximidad,
          color,
          latestSensors,
        ] = await Promise.all([
          getSensorHistory("temperatura", 24, 300),
          getSensorHistory("ambiente", 24, 300),
          getSensorHistory("gas", 24, 300),
          getSensorHistory("proximidad", 24, 300),
          getSensorHistory("color", 24, 100),
          getLatestSensors(),
        ]);

        setTemperaturaData(formatNumericChartData(temperatura));
        setAmbienteData(formatNumericChartData(ambiente));
        setGasData(formatNumericChartData(gas));
        setProximidadData(formatNumericChartData(proximidad));
        setColorDocs(Array.isArray(color) ? color : []);
        setLatest(Array.isArray(latestSensors) ? latestSensors : []);
      } catch (error) {
        console.error("Error al cargar gráficas:", error);
      } finally {
        setLoading(false);
      }
    };

    loadGraphs();
  }, []);

  const current = slides[index];

  const latestGas = useMemo(() => {
    const gas = latest.find((item) => String(item.sensor || "").includes("gas"));
    return Number(gas?.value) || 0;
  }, [latest]);

  const latestDistance = useMemo(() => {
    const prox = latest.find((item) =>
      String(item.sensor || "").includes("proximidad")
    );
    return Number(prox?.value) || 0;
  }, [latest]);

  const latestColorDoc = useMemo(() => {
    if (!colorDocs.length) return null;

    const sorted = [...colorDocs].sort(
      (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
    );

    return sorted[0] || null;
  }, [colorDocs]);

  const latestColor = useMemo(() => {
    if (!latestColorDoc) return "Sin datos";
    return latestColorDoc.color || latestColorDoc.raw?.color || "UNKNOWN";
  }, [latestColorDoc]);

  const latestSequence = useMemo(() => {
    if (!latestColorDoc) return [];
    return latestColorDoc.sequence || latestColorDoc.raw?.sequence || [];
  }, [latestColorDoc]);

  const latestCamouflage = useMemo(() => {
    if (!latestColorDoc) return false;
    return Boolean(
      latestColorDoc.camouflage ?? latestColorDoc.raw?.camouflage ?? false
    );
  }, [latestColorDoc]);

  const colorFrequencyData = useMemo(() => {
    const counts = {};

    colorDocs.forEach((item) => {
      const color = item?.color || item?.raw?.color;
      if (!color) return;
      counts[color] = (counts[color] || 0) + 1;
    });

    const order = ["RED", "YELLOW", "BLUE", "GREEN", "UNKNOWN"];

    return order
      .filter((name) => counts[name] != null)
      .map((name) => ({
        colorName: name,
        count: counts[name],
        fill: mapColorToHex(name),
      }));
  }, [colorDocs]);

  const colorTimelineData = useMemo(() => {
    return [...colorDocs]
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      .slice(-12)
      .map((item) => ({
        time: new Date(item.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        colorName: item?.color || item?.raw?.color || "UNKNOWN",
        value: 1,
        fill: mapColorToHex(item?.color || item?.raw?.color || "UNKNOWN"),
      }));
  }, [colorDocs]);

  const next = () => setIndex((prev) => (prev + 1) % slides.length);
  const prev = () => setIndex((prev) => (prev - 1 + slides.length) % slides.length);

  return (
    <div className="graphs-page">
      <h1 className="graphs-title">Panel de gráficas</h1>

      <div className="graphs-nav">
        <button className="nav-btn" onClick={prev}>
          ⬅ Izquierda
        </button>

        <h2>{current.title}</h2>

        <button className="nav-btn" onClick={next}>
          Derecha ➡
        </button>
      </div>

      {loading ? (
        <p>Cargando gráficas...</p>
      ) : (
        <div className="graph-card">
          {current.key === "temperatura" && (
            <ChartSection
              title="Temperatura"
              data={temperaturaData}
              unit="°C"
              emptyMessage="Sin lecturas de temperatura"
            />
          )}

          {current.key === "ambiente" && (
            <ChartSection
              title="Ambiente / humedad"
              data={ambienteData}
              unit="%"
              emptyMessage="Sin lecturas de ambiente"
            />
          )}

          {current.key === "gas" && (
            <>
              <InfoBox
                title="Gas actual"
                value={`${latestGas}`}
                status={
                  latestGas >= 70
                    ? "CRÍTICO"
                    : latestGas >= 40
                    ? "ALERTA"
                    : "NORMAL"
                }
              />
              <ChartSection
                title="Histórico de gas"
                data={gasData}
                unit=""
                emptyMessage="Sin lecturas de gas"
              />
            </>
          )}

          {current.key === "proximidad" && (
            <>
              <InfoBox
                title="Distancia actual"
                value={`${latestDistance} cm`}
                status={
                  latestDistance <= 20
                    ? "CRÍTICO"
                    : latestDistance <= 50
                    ? "CERCANO"
                    : "LEJANO"
                }
              />
              <ChartSection
                title="Histórico de proximidad"
                data={proximidadData}
                unit=" cm"
                emptyMessage="Sin lecturas de proximidad"
              />
            </>
          )}

          {current.key === "color" && (
            <>
              <div className="color-summary-grid">
                <ColorInfoBox
                  title="Último color detectado"
                  value={latestColor}
                  colorName={latestColor}
                  status={latestCamouflage ? "Camuflaje ACTIVO" : "Camuflaje INACTIVO"}
                />

                <InfoBox
                  title="Última secuencia"
                  value={
                    latestSequence.length > 0
                      ? latestSequence.join(" → ")
                      : "Sin secuencia"
                  }
                  status="Secuencia reciente del sensor RGB"
                />
              </div>

              {colorFrequencyData.length === 0 ? (
                <div className="info-box">
                  <h3>Color detectado</h3>
                  <p>Sin datos de color</p>
                  <span>
                    La vista se llenará cuando existan lecturas en
                    nave/sensores/color.
                  </span>
                </div>
              ) : (
                <>
                  <div className="chart-section">
                    <h3>Frecuencia de colores detectados</h3>
                    <div style={{ width: "100%", height: 320 }}>
                      <ResponsiveContainer>
                        <BarChart data={colorFrequencyData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="colorName" />
                          <YAxis allowDecimals={false} />
                          <Tooltip />
                          <Bar dataKey="count">
                            {colorFrequencyData.map((entry, idx) => (
                              <Cell key={idx} fill={entry.fill} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="chart-section">
                    <h3>Timeline reciente de colores</h3>
                    <div style={{ width: "100%", height: 320 }}>
                      <ResponsiveContainer>
                        <BarChart data={colorTimelineData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="time" />
                          <YAxis hide domain={[0, 1]} />
                          <Tooltip
                            formatter={(_, __, item) => [
                              item?.payload?.colorName || "UNKNOWN",
                              "Color",
                            ]}
                          />
                          <Bar dataKey="value">
                            {colorTimelineData.map((entry, idx) => (
                              <Cell key={idx} fill={entry.fill} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function ChartSection({ title, data, unit, emptyMessage }) {
  if (!data || data.length === 0) {
    return (
      <div className="info-box">
        <h3>{title}</h3>
        <p>{emptyMessage}</p>
        <span>La gráfica se llenará cuando existan lecturas en MongoDB.</span>
      </div>
    );
  }

  return (
    <div className="chart-section">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 420 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip formatter={(value) => [`${value}${unit}`, title]} />
            <Line type="monotone" dataKey="value" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function InfoBox({ title, value, status }) {
  return (
    <div className="info-box">
      <h3>{title}</h3>
      <p>{value}</p>
      <span>{status}</span>
    </div>
  );
}

function ColorInfoBox({ title, value, status, colorName }) {
  return (
    <div className="info-box">
      <h3>{title}</h3>
      <p style={{ color: mapColorToHex(colorName), fontWeight: "bold" }}>
        {value}
      </p>
      <span>{status}</span>
    </div>
  );
}

function formatNumericChartData(items = []) {
  return items
    .filter((item) => item?.value != null && !Number.isNaN(Number(item.value)))
    .map((item) => ({
      time: new Date(item.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      value: Number(item.value),
      timestamp: item.timestamp,
      sensor: item.sensor,
    }));
}

function mapColorToHex(colorName) {
  switch (String(colorName || "").toUpperCase()) {
    case "RED":
      return "#ff4d4f";
    case "YELLOW":
      return "#fadb14";
    case "BLUE":
      return "#1677ff";
    case "GREEN":
      return "#52c41a";
    default:
      return "#8c8c8c";
  }
}