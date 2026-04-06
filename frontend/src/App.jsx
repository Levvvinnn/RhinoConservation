import { useEffect, useMemo, useState } from "react";
import {
  getAlerts,
  getLatestLocations,
  getRhinos,
  resolveAlert,
} from "./lib/api";

const statusStyles = {
  active: "bg-green-100 text-green-700 border-green-200",
  inactive: "bg-gray-100 text-gray-700 border-gray-200",
  injured: "bg-yellow-100 text-yellow-800 border-yellow-200",
  missing: "bg-red-100 text-red-700 border-red-200",
};

function formatTime(value) {
  if (!value) return "No update yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function formatCoord(value) {
  if (typeof value !== "number") return "—";
  return value.toFixed(5);
}

export default function App() {
  const [rhinos, setRhinos] = useState([]);
  const [locations, setLocations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setError("");
      const [rhinosRes, locationsRes, alertsRes] = await Promise.all([
        getRhinos(),
        getLatestLocations(),
        getAlerts(),
      ]);

      setRhinos(rhinosRes.data || []);
      setLocations(locationsRes.data || []);
      setAlerts(alertsRes.data || []);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const latestByRhino = useMemo(() => {
    const map = {};
    for (const loc of locations) {
      map[loc.rhino_id] = loc;
    }
    return map;
  }, [locations]);

  const activeRhinos = rhinos.filter((r) => r.status === "active").length;
  const unresolvedAlerts = alerts.filter((a) => !a.resolved).length;
  const totalLocations = locations.length;

  const handleResolveAlert = async (alertId) => {
    try {
      await resolveAlert(alertId);
      await loadData();
    } catch (err) {
      setError(err.message || "Could not resolve alert");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-600">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-2xl bg-white shadow-sm border border-slate-200 p-6">
          <h1 className="text-3xl font-bold">Rhino Tracker Dashboard</h1>
          <p className="text-slate-600 mt-1">
            Live view of rhino telemetry, location history, and alerts.
          </p>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
            <p className="text-sm text-slate-500">Total Rhinos</p>
            <p className="text-3xl font-semibold mt-2">{rhinos.length}</p>
          </div>

          <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
            <p className="text-sm text-slate-500">Active Rhinos</p>
            <p className="text-3xl font-semibold mt-2">{activeRhinos}</p>
          </div>

          <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
            <p className="text-sm text-slate-500">Unresolved Alerts</p>
            <p className="text-3xl font-semibold mt-2">{unresolvedAlerts}</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-semibold">Rhino Telemetry</h2>

            <div className="grid gap-4 md:grid-cols-2">
              {rhinos.map((rhino) => {
                const loc = latestByRhino[rhino.id];

                return (
                  <div
                    key={rhino.id}
                    className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold">{rhino.name}</h3>
                        <p className="text-sm text-slate-500">
                          ID: {rhino.id} • Collar: {rhino.collar_id}
                        </p>
                      </div>

                      <span
                        className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${
                          statusStyles[rhino.status] || statusStyles.inactive
                        }`}
                      >
                        {rhino.status}
                      </span>
                    </div>

                    <div className="mt-4 space-y-2 text-sm">
                      <p>
                        <span className="font-medium">Species:</span> {rhino.species}
                      </p>
                      <p>
                        <span className="font-medium">Latitude:</span>{" "}
                        {loc ? formatCoord(loc.latitude) : "No location yet"}
                      </p>
                      <p>
                        <span className="font-medium">Longitude:</span>{" "}
                        {loc ? formatCoord(loc.longitude) : "No location yet"}
                      </p>
                      <p>
                        <span className="font-medium">Last Update:</span>{" "}
                        {loc ? formatTime(loc.timestamp) : "No update yet"}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Alerts</h2>

            <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm space-y-3">
              {alerts.length === 0 ? (
                <p className="text-sm text-slate-500">No alerts right now.</p>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="rounded-xl border border-slate-200 p-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">
                        {alert.alert_type || "alert"}
                      </p>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          alert.resolved ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        }`}
                      >
                        {alert.resolved ? "resolved" : "open"}
                      </span>
                    </div>

                    <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {formatTime(alert.created_at)}
                    </p>

                    {!alert.resolved && (
                      <button
                        onClick={() => handleResolveAlert(alert.id)}
                        className="mt-3 rounded-lg bg-slate-900 px-3 py-2 text-sm text-white"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
              <h3 className="font-semibold mb-2">Latest Location Count</h3>
              <p className="text-sm text-slate-600">
                {totalLocations} latest location records loaded from the backend.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}