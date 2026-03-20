const API_BASE_URL = "http://localhost:3000";

const handleResponse = async (response) => {
  const text = await response.text();

  if (!response.ok) {
    try {
      const data = JSON.parse(text);
      throw new Error(data?.error || data?.message || "Error en la petición");
    } catch {
      throw new Error(`Respuesta no JSON (${response.status}): ${text.slice(0, 120)}`);
    }
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`La respuesta no es JSON: ${text.slice(0, 120)}`);
  }
};

export const getSensors = async () => {
  const response = await fetch(`${API_BASE_URL}/sensors`);
  return handleResponse(response);
};

export const getLatestSensors = async () => {
  const response = await fetch(`${API_BASE_URL}/sensors/latest`);
  return handleResponse(response);
};

export const getSensorHistory = async (sensor, hours = 24, limit = 100) => {
  const response = await fetch(
    `${API_BASE_URL}/sensors/history/${sensor}?hours=${hours}&limit=${limit}`
  );
  return handleResponse(response);
};

export const getStats = async () => {
  const response = await fetch(`${API_BASE_URL}/stats`);
  return handleResponse(response);
};

export const sendCommand = async ({ topic, command, value }) => {
  const response = await fetch(`${API_BASE_URL}/commands`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic,
      command,
      value,
    }),
  });

  return handleResponse(response);
};

export const sendMessage = async (message) => {
  const response = await fetch(`${API_BASE_URL}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
    }),
  });

  return handleResponse(response);
};

export const mapSensorData = (readings = []) => {
  const mapped = {
    gas: 0,
    temp: 0,
    humedad: 0,
    distancia: 0,
    color: "N/D",
    ambiente: null,
  };

  for (const item of readings) {
    const sensor = item?.sensor || "";
    const value = item?.value;

    if (sensor.includes("gas")) {
      mapped.gas = Number(value) || 0;
    } else if (sensor.includes("proximidad")) {
      mapped.distancia = Number(value) || 0;
    } else if (sensor.includes("temperatura") || sensor.includes("temp")) {
      mapped.temp = Number(value) || 0;
    } else if (sensor.includes("ambiente")) {
      mapped.humedad = Number(value) || 0;
      mapped.ambiente = Number(value) || 0;
    } else if (sensor.includes("humedad")) {
      mapped.humedad = Number(value) || 0;
    } else if (sensor.includes("color")) {
      mapped.color = String(value ?? "N/D");
    }
  }

  return mapped;
};

export const deriveStatus = ({ gas, distancia }) => {
  if (gas >= 70 || distancia <= 20) return "EMERGENCIA";
  if (gas >= 40 || distancia <= 50) return "ALERTA";
  return "OPERATIVA";
};

export const normalizeStats = (stats) => {
  return {
    disparos: stats?.disparos ?? stats?.shots ?? 0,
    tiempoCamuflaje: stats?.tiempoCamuflaje ?? "00:00:00",
    alertasGas: stats?.alertasGas ?? 0,
    alertasMeteorito: stats?.alertasMeteorito ?? 0,
    totalLecturas: stats?.totalLecturas ?? 0,
  };
};