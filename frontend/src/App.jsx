import { useEffect, useState } from "react";
import LatestTelemetry from "./components/LatestTelemetry";

const initialRhinoForm = {
  id: "",
  name: "",
  species: "",
  collar_id: "",
};

const initialLocationForm = {
  rhino_id: "",
  latitude: "",
  longitude: "",
  altitude: "",
  accuracy: "",
  sats: "",
};

export default function App() {
  const [rhinos, setRhinos] = useState([]);
  const [rhinoForm, setRhinoForm] = useState(initialRhinoForm);
  const [locationForm, setLocationForm] = useState(initialLocationForm);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ email: "", password: "", phone: "" });
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    checkLoginStatus();
  }, []);

  async function checkLoginStatus() {
    try {
      const response = await fetch("/api/login-status");
      const data = await response.json();
      setIsLoggedIn(data.logged_in);
      if (data.logged_in) {
        loadRhinos();
      }
    } catch (error) {
      setIsLoggedIn(false);
    }
  }

  async function loadRhinos() {
    try {
      const response = await fetch("/api/rhinos");
      const data = await response.json();
      if (data.success) {
        setRhinos(data.data);
      } else {
        setStatus({ type: "error", message: data.error || "Unable to load rhinos." });
      }
    } catch (error) {
      setStatus({ type: "error", message: "Backend unreachable. Start the Flask server first." });
    }
  }

  async function handleRhinoSubmit(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });

    const payload = {
      id: rhinoForm.id.trim(),
      name: rhinoForm.name.trim(),
      species: rhinoForm.species.trim(),
      collar_id: rhinoForm.collar_id.trim(),
    };

    try {
      const response = await fetch("/api/rhinos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (data.success) {
        setStatus({ type: "success", message: "Rhino saved successfully." });
        setRhinoForm(initialRhinoForm);
        loadRhinos();
      } else {
        setStatus({ type: "error", message: data.error || "Failed to save rhino." });
      }
    } catch (error) {
      setStatus({ type: "error", message: "Unable to reach backend." });
    }
  }

  async function handleLocationSubmit(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });

    if (!locationForm.rhino_id) {
      setStatus({ type: "error", message: "Select a rhino first." });
      return;
    }

    const payload = {
      latitude: parseFloat(locationForm.latitude),
      longitude: parseFloat(locationForm.longitude),
      altitude: locationForm.altitude ? parseFloat(locationForm.altitude) : undefined,
      accuracy: locationForm.accuracy ? parseFloat(locationForm.accuracy) : undefined,
      sats: locationForm.sats ? parseInt(locationForm.sats, 10) : undefined,
    };

    try {
      const response = await fetch(`/api/rhinos/${locationForm.rhino_id}/location`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (data.success) {
        setStatus({ type: "success", message: "Location saved successfully." });
        setLocationForm({ ...locationForm, latitude: "", longitude: "", altitude: "", accuracy: "", sats: "" });
      } else {
        setStatus({ type: "error", message: data.error || "Failed to save location." });
      }
    } catch (error) {
      setStatus({ type: "error", message: "Unable to reach backend." });
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams(loginForm),
      });
      if (response.redirected && response.url.includes("/")) {
        setIsLoggedIn(true);
        setStatus({ type: "success", message: "Logged in successfully." });
      } else {
        const text = await response.text();
        setStatus({ type: "error", message: "Login failed." });
      }
    } catch (error) {
      setStatus({ type: "error", message: "Unable to reach backend." });
    }
  }

  async function handleRegister(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });

    try {
      const response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams(registerForm),
      });
      if (response.redirected && response.url.includes("/login")) {
        setStatus({ type: "success", message: "Account created. Please log in." });
        setShowRegister(false);
      } else {
        const text = await response.text();
        setStatus({ type: "error", message: "Registration failed." });
      }
    } catch (error) {
      setStatus({ type: "error", message: "Unable to reach backend." });
    }
  }

  function updateRhinoField(field, value) {
    setRhinoForm((current) => ({ ...current, [field]: value }));
  }

  function updateLocationField(field, value) {
    setLocationForm((current) => ({ ...current, [field]: value }));
  }

  function updateLoginField(field, value) {
    setLoginForm((current) => ({ ...current, [field]: value }));
  }

  function updateRegisterField(field, value) {
    setRegisterForm((current) => ({ ...current, [field]: value }));
  }

  if (!isLoggedIn) {
    return (
      <main style={{ padding: "24px", fontFamily: "Inter, system-ui, sans-serif", maxWidth: 400, margin: "0 auto" }}>
        <h1>Rhino Conservation Login</h1>
        {status.message ? (
          <section style={{ padding: 18, borderRadius: 12, background: status.type === "success" ? "#ecfdf5" : "#fef3c7", border: status.type === "success" ? "1px solid #10b981" : "1px solid #f59e0b" }}>
            <strong>{status.type === "success" ? "Success" : "Notice"}:</strong> {status.message}
          </section>
        ) : null}
        {showRegister ? (
          <form onSubmit={handleRegister} style={{ display: "grid", gap: 14 }}>
            <h2>Register</h2>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontWeight: 600 }}>Email</span>
              <input
                value={registerForm.email}
                required
                type="email"
                onChange={(event) => updateRegisterField("email", event.target.value)}
                style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
              />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontWeight: 600 }}>Password</span>
              <input
                value={registerForm.password}
                required
                type="password"
                onChange={(event) => updateRegisterField("password", event.target.value)}
                style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
              />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontWeight: 600 }}>Phone (optional)</span>
              <input
                value={registerForm.phone}
                onChange={(event) => updateRegisterField("phone", event.target.value)}
                style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
              />
            </label>
            <button type="submit" style={{ padding: "12px 18px", background: "#2563eb", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
              Register
            </button>
            <button type="button" onClick={() => setShowRegister(false)} style={{ padding: "12px 18px", background: "#6b7280", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
              Back to Login
            </button>
          </form>
        ) : (
          <form onSubmit={handleLogin} style={{ display: "grid", gap: 14 }}>
            <h2>Login</h2>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontWeight: 600 }}>Email</span>
              <input
                value={loginForm.email}
                required
                type="email"
                onChange={(event) => updateLoginField("email", event.target.value)}
                style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
              />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontWeight: 600 }}>Password</span>
              <input
                value={loginForm.password}
                required
                type="password"
                onChange={(event) => updateLoginField("password", event.target.value)}
                style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
              />
            </label>
            <button type="submit" style={{ padding: "12px 18px", background: "#2563eb", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
              Login
            </button>
            <button type="button" onClick={() => setShowRegister(true)} style={{ padding: "12px 18px", background: "#6b7280", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
              Register
            </button>
          </form>
        )}
      </main>
    );
  }

  return (
    <main style={{ padding: "24px", fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ maxWidth: 980, margin: "0 auto", display: "grid", gap: 24 }}>
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h1>Rhino Conservation Prototype</h1>
            <button onClick={() => setIsLoggedIn(false)} style={{ padding: "8px 16px", background: "#dc2626", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
              Logout
            </button>
          </div>
          <p style={{ color: "#4b5563" }}>
            Enter a new rhino or save GPS location data. The backend stores the data in SQLite.
          </p>
        </section>

        {status.message ? (
          <section style={{ padding: 18, borderRadius: 12, background: status.type === "success" ? "#ecfdf5" : "#fef3c7", border: status.type === "success" ? "1px solid #10b981" : "1px solid #f59e0b" }}>
            <strong>{status.type === "success" ? "Success" : "Notice"}:</strong> {status.message}
          </section>
        ) : null}

        <section style={{ display: "grid", gap: 24 }}>
          <div style={{ padding: 18, border: "1px solid #e5e7eb", borderRadius: 12, background: "#ffffff" }}>
            <h2 style={{ marginTop: 0 }}>Create a new rhino</h2>
            <form onSubmit={handleRhinoSubmit} style={{ display: "grid", gap: 14 }}>
              {[
                { label: "Rhino ID", name: "id", placeholder: "RHINO001" },
                { label: "Name", name: "name", placeholder: "Nandi" },
                { label: "Species", name: "species", placeholder: "white" },
                { label: "Collar ID", name: "collar_id", placeholder: "COLLAR123" },
              ].map(({ label, name, placeholder }) => (
                <label key={name} style={{ display: "grid", gap: 6 }}>
                  <span style={{ fontWeight: 600 }}>{label}</span>
                  <input
                    value={rhinoForm[name]}
                    required
                    placeholder={placeholder}
                    onChange={(event) => updateRhinoField(name, event.target.value)}
                    style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
                  />
                </label>
              ))}
              <button type="submit" style={{ padding: "12px 18px", background: "#2563eb", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
                Save Rhino
              </button>
            </form>
          </div>

          <div style={{ padding: 18, border: "1px solid #e5e7eb", borderRadius: 12, background: "#ffffff" }}>
            <h2 style={{ marginTop: 0 }}>Save a location</h2>
            <form onSubmit={handleLocationSubmit} style={{ display: "grid", gap: 14 }}>
              <label style={{ display: "grid", gap: 6 }}>
                <span style={{ fontWeight: 600 }}>Rhino</span>
                <select
                  value={locationForm.rhino_id}
                  onChange={(event) => updateLocationField("rhino_id", event.target.value)}
                  required
                  style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
                >
                  <option value="">Select a rhino</option>
                  {rhinos.map((rhino) => (
                    <option key={rhino.id} value={rhino.id}>
                      {rhino.id} — {rhino.name}
                    </option>
                  ))}
                </select>
              </label>
              {[
                { label: "Latitude", name: "latitude" },
                { label: "Longitude", name: "longitude" },
                { label: "Altitude", name: "altitude" },
                { label: "Accuracy", name: "accuracy" },
                { label: "Satellites", name: "sats" },
              ].map(({ label, name }) => (
                <label key={name} style={{ display: "grid", gap: 6 }}>
                  <span style={{ fontWeight: 600 }}>{label}</span>
                  <input
                    value={locationForm[name]}
                    required={name === "latitude" || name === "longitude"}
                    placeholder={name === "sats" ? "12" : name === "latitude" ? "-1.2345" : name === "longitude" ? "36.7890" : "Optional"}
                    onChange={(event) => updateLocationField(name, event.target.value)}
                    style={{ padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, width: "100%" }}
                  />
                </label>
              ))}
              <button
                type="submit"
                disabled={!rhinos.length}
                style={{ padding: "12px 18px", background: rhinos.length ? "#16a34a" : "#94a3b8", color: "white", border: "none", borderRadius: 8, cursor: rhinos.length ? "pointer" : "not-allowed" }}
              >
                Save Location
              </button>
            </form>
          </div>
        </section>

        <section style={{ padding: 18, border: "1px solid #e5e7eb", borderRadius: 12, background: "#ffffff" }}>
          <h2 style={{ marginTop: 0 }}>Saved rhinos</h2>
          {rhinos.length ? (
            <div style={{ display: "grid", gap: 12 }}>
              {rhinos.map((rhino) => (
                <div key={rhino.id} style={{ padding: 14, border: "1px solid #e5e7eb", borderRadius: 10, background: "#f8fafc" }}>
                  <strong>{rhino.id}</strong> — {rhino.name}
                  <div style={{ color: "#475569", marginTop: 6 }}>
                    Species: {rhino.species} · Collar: {rhino.collar_id} · Status: {rhino.status}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "#6b7280", margin: 0 }}>No saved rhinos yet. Add one above to store it in SQLite.</p>
          )}
        </section>
      </div>
    </main>
  );
}
