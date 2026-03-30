import { useEffect, useState } from "react";
import { getInitialTelemetry, simulateTelemetryStep, getStatusLabel, getStatusColor } from "../telemetrySimulation";

const REFRESH_INTERVAL_MS = 5000;

function TelemetryCard({ item }) {
  return (
    <article
      style={{
        border: "1px solid #d1d5db",
        borderRadius: 12,
        padding: 18,
        background: "#ffffff",
        boxShadow: "0 4px 12px rgba(15, 23, 42, 0.04)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem" }}>{item.rhino_id}</h3>
          <p style={{ margin: "4px 0 0", color: "#4b5563" }}>Last update: {new Date(item.timestamp).toLocaleString()}</p>
        </div>
        <span
          style={{
            padding: "6px 10px",
            borderRadius: 999,
            background: getStatusColor(item.flags),
            color: "#111827",
            fontWeight: 600,
            fontSize: "0.9rem",
          }}
        >
          {getStatusLabel(item.flags)}
        </span>
      </div>

      <div style={{ marginTop: 16, lineHeight: 1.65, color: "#374151" }}>
        <p style={{ margin: 0 }}><strong>Latitude:</strong> {item.latitude}</p>
        <p style={{ margin: 0 }}><strong>Longitude:</strong> {item.longitude}</p>
        <p style={{ margin: 0 }}><strong>Battery:</strong> {item.battery}%</p>
      </div>

      <div style={{ marginTop: 14, height: 10, background: "#e5e7eb", borderRadius: 999, overflow: "hidden" }}>
        <div
          style={{
            width: `${item.battery}%`,
            height: "100%",
            background: item.battery > 50 ? "#34d399" : item.battery > 20 ? "#fbbf24" : "#f87171",
            transition: "width 0.5s ease",
          }}
        />
      </div>
    </article>
  );
}

export default function LatestTelemetry() {
  const [data, setData] = useState([]);

  useEffect(() => {
    setData(getInitialTelemetry());
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setData((current) => {
        if (!current || current.length === 0) {
          return getInitialTelemetry();
        }
        return simulateTelemetryStep(current);
      });
    }, REFRESH_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 16, flexWrap: "wrap" }}>
          <div>
            <h2 style={{ margin: 0 }}>Telemetry Simulator</h2>
            <p style={{ margin: "8px 0 0", color: "#6b7280" }}>
              Simulated telemetry updates every {REFRESH_INTERVAL_MS / 1000} seconds.
            </p>
          </div>
          <div style={{ color: "#374151", fontWeight: 600 }}>
            {data.length} rhinos tracked
          </div>
        </div>
      </section>

      <section>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          {data.map((item) => (
            <TelemetryCard key={item.id} item={item} />
          ))}
        </div>
      </section>

      <section style={{ padding: 18, border: "1px solid #e5e7eb", borderRadius: 12, background: "#f9fafb" }}>
        <h3 style={{ marginTop: 0 }}>Rhino Overview</h3>
        <ul style={{ margin: 0, paddingLeft: 20, color: "#374151" }}>
          {data.map((item) => (
            <li key={`${item.id}-list`} style={{ marginBottom: 6 }}>
              <strong>{item.rhino_id}</strong> — {getStatusLabel(item.flags)} — {item.battery}% battery
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
