const handleResponse = async (response) => {
  if (!response.ok) {
    let message = "Error en la petición";
    try {
      const data = await response.json();
      message = data?.error || data?.message || message;
    } catch {
     
    }
    throw new Error(message);
  }

  return response.json();
};

export const getSensors = async () => {
  const response = await fetch("/sensors");
  return handleResponse(response);
};

export const getStats = async () => {
  const response = await fetch("/stats");
  return handleResponse(response);
};

export const sendCommand = async ({ topic, command, value }) => {
  const response = await fetch("/commands", {
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
  const response = await fetch("/messages", {
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

/**
 * Espera datos con forma:
 * [{ sensor: "nave/sensores/gas", value: 55, timestamp: "..." }, ...]
 */
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
    } else if (sensor.includes("humedad")) {
      mapped.humedad = Number(value) || 0;
    } else if (sensor.includes("color")) {
      mapped.color = String(value ?? "N/D");
    } else if (sensor.includes("ambiente")) {
      mapped.ambiente = value;

      if (typeof value === "object" && value !== null) {
        if (value.temp != null) mapped.temp = Number(value.temp) || 0;
        if (value.temperatura != null) mapped.temp = Number(value.temperatura) || 0;
        if (value.humedad != null) mapped.humedad = Number(value.humedad) || 0;
      }
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