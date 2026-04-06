async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof data === "object" && data !== null
        ? data.error || data.message || `Request failed (${response.status})`
        : `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

export function getRhinos() {
  return requestJson("/api/rhinos");
}

export function getLatestLocations() {
  return requestJson("/api/locations/latest");
}

export function getAlerts() {
  return requestJson("/api/alerts");
}

export function resolveAlert(alertId) {
  return requestJson(`/api/alerts/${alertId}/resolve`, {
    method: "PUT",
  });
}