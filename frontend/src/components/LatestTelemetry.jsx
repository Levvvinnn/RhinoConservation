import { useEffect, useState } from "react";

export default function LatestTelemetry() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("/api/locations/latest")
      .then((res) => res.json())
      .then((json) => setData(json.data || []));
  }, []);

  return (
    <div>
      <h2>Latest Rhino Telemetry</h2>
      {data.map((item) => (
        <div key={item.id} style={{ border: "1px solid #ccc", margin: "8px", padding: "8px" }}>
          <p><strong>Rhino:</strong> {item.rhino_id}</p>
          <p><strong>Lat:</strong> {item.latitude}</p>
          <p><strong>Lon:</strong> {item.longitude}</p>
          <p><strong>Battery:</strong> {item.battery ?? "N/A"}</p>
        </div>
      ))}
    </div>
  );
}
