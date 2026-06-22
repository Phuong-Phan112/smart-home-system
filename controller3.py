from flask import Flask, jsonify    #Erstellen Webserver, wandeln Python-Dict in JSON-Antwort um
import paho.mqtt.client as mqtt
import threading  #thread-sicheren Zugriff auf gemeinsame Daten

app = Flask(__name__)

# Zustand + Lock
state = {
    "Temperature": 0,
    "Light": 0,
    "Heating": "OFF",
    "Cooling": "OFF"
}
state_lock = threading.Lock() # sicher stellen, dass nie 2 Threads gleichzeitig (Race Condition)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:        # Fehlerprüfung
        print("Verbunden mit Broker")
        client.subscribe([("home/temperature", 1), ("home/light", 1)])  # ein Aufruf statt zwei
    else:
        print("Verbindungsfehler, rc =", rc)

def on_message(client, userdata, msg):
    try:  #Absturz bei ungültiger Payload verhindern
        val = int(msg.payload.decode().strip())
    except ValueError:
        print(f"Warnung: ungültige Payload auf {msg.topic}: {msg.payload}")
        return

    with state_lock:     # Sperren state für anderen Threads beim Schreiben
        if msg.topic == "home/temperature":
            state["Temperature"] = val
        elif msg.topic == "home/light":
            state["Light"] = val
        decide()                                      

def decide():
    temp = state["Temperature"]
    if temp < 5:
        state["Heating"] = "ON"
        state["Cooling"] = "OFF"
    elif temp > 25:
        state["Heating"] = "OFF"
        state["Cooling"] = "ON"
    else:
        state["Heating"] = "OFF"
        state["Cooling"] = "OFF"

# REST API
@app.route("/status") #registrieren die URL
def get_status():
    with state_lock:       #Sperren state beim Lesen, damit kein halbfertiger Zustand ausgelesen wird
        snapshot = dict(state) #Kopie erstellen, dann Lock freigeben
    return jsonify(snapshot)

# MQTT starten
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:       #Fehlerbehandlung
    client.connect("localhost", 1883, 60)
except Exception as e:
    print("MQTT-Verbindungsfehler:", e)

client.loop_start()

# Dashboard

# Dashboard
@app.route("/")
def dashboard():
    html = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Smart Home Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Arial, sans-serif;
      background: #f0f2f5;
      padding: 2rem 1rem;
      min-height: 100vh;
    }
    h1 {
      text-align: center;
      font-size: 1.5rem;
      font-weight: 600;
      color: #1a1d27;
      margin-bottom: 1.5rem;
      letter-spacing: 0.05em;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      max-width: 800px;
      margin: 0 auto 1.5rem;
    }
    .card {
      background: white;
      border-radius: 14px;
      padding: 1.25rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .card-label {
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #888;
    }
    .card-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .card-icon {
      font-size: 2rem;
      line-height: 1;
    }
    .card-value {
      font-size: 2rem;
      font-weight: 700;
      color: #1a1d27;
      line-height: 1;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 0.3rem 0.9rem;
      border-radius: 99px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    .badge-on  { background: #d1fae5; color: #065f46; }
    .badge-off { background: #f3f4f6; color: #6b7280; }
    .badge-light-on  { background: #fef9c3; color: #854d0e; }
    .badge-light-off { background: #f3f4f6; color: #6b7280; }

    .chart-card {
      background: white;
      border-radius: 14px;
      padding: 1.25rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      max-width: 800px;
      margin: 0 auto;
    }
    .chart-title {
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #888;
      margin-bottom: 1rem;
    }
    footer {
      text-align: center;
      margin-top: 1.5rem;
      font-size: 0.75rem;
      color: #aaa;
    }
    #last-update { color: #3b82f6; }
  </style>
</head>
<body>

<h1><i class="ti ti-home-2" aria-hidden="true"></i> Smart Home Dashboard</h1>

<div class="grid">

  <!-- Temperatur -->
  <div class="card">
    <span class="card-label">Temperatur</span>
    <div class="card-row">
      <i class="ti ti-temperature card-icon" style="color:#ef4444" aria-hidden="true"></i>
      <span class="card-value" id="temp-val">—</span>
      <span style="font-size:1rem; color:#888; align-self:flex-end; padding-bottom:4px">°C</span>
    </div>
  </div>

  <!-- Licht -->
  <div class="card">
    <span class="card-label">Licht</span>
    <div class="card-row">
      <i class="ti ti-bulb card-icon" id="light-icon" style="color:#d97706" aria-hidden="true"></i>
      <span class="badge badge-light-off" id="light-badge">AUS</span>
    </div>
  </div>

  <!-- Heizung -->
  <div class="card">
    <span class="card-label">Heizung</span>
    <div class="card-row">
      <i class="ti ti-flame card-icon" id="heating-icon" style="color:#f97316" aria-hidden="true"></i>
      <span class="badge badge-off" id="heating-badge">OFF</span>
    </div>
  </div>

  <!-- Kühlung -->
  <div class="card">
    <span class="card-label">Kühlung</span>
    <div class="card-row">
      <i class="ti ti-snowflake card-icon" id="cooling-icon" style="color:#3b82f6" aria-hidden="true"></i>
      <span class="badge badge-off" id="cooling-badge">OFF</span>
    </div>
  </div>

</div>

<!-- Temperatur-Diagramm -->
<div class="chart-card">
  <div class="chart-title"><i class="ti ti-chart-line" aria-hidden="true"></i> Temperaturverlauf</div>
  <canvas id="tempChart" height="100"></canvas>
</div>

<footer>Letzte Aktualisierung: <span id="last-update">—</span></footer>

<script>
  const MAX_POINTS = 20;
  const labels = [];
  const tempData = [];

  const ctx = document.getElementById("tempChart").getContext("2d");
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Temperatur (°C)",
        data: tempData,
        borderColor: "#ef4444",
        backgroundColor: "rgba(239,68,68,0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: "#ef4444"
      }]
    },
    options: {
      animation: false,
      scales: {
        y: { beginAtZero: false, grid: { color: "#f0f0f0" } },
        x: { grid: { display: false } }
      },
      plugins: { legend: { display: false } }
    }
  });

  function setBadge(id, isOn, labelOn, labelOff, classOn, classOff) {
    const el = document.getElementById(id);
    el.textContent = isOn ? labelOn : labelOff;
    el.className = "badge " + (isOn ? classOn : classOff);
  }

  async function fetchStatus() {
    try {
      const res  = await fetch("/status");
      const data = await res.json();

      // Temperatur
      const t = data.Temperature;
      document.getElementById("temp-val").textContent = t;

      // Diagramm aktualisieren
      const now = new Date().toLocaleTimeString("de-DE", {hour:"2-digit", minute:"2-digit", second:"2-digit"});
      if (labels.length >= MAX_POINTS) { labels.shift(); tempData.shift(); }
      labels.push(now);
      tempData.push(t);
      chart.update();

      // Licht
      const lightOn = data.Light === 1;
      setBadge("light-badge", lightOn, "AN", "AUS", "badge-light-on", "badge-light-off");
      document.getElementById("light-icon").style.color = lightOn ? "#f59e0b" : "#d1d5db";

      // Heizung
      const heatOn = data.Heating === "ON";
      setBadge("heating-badge", heatOn, "ON", "OFF", "badge-on", "badge-off");
      document.getElementById("heating-icon").style.color = heatOn ? "#f97316" : "#d1d5db";

      // Kühlung
      const coolOn = data.Cooling === "ON";
      setBadge("cooling-badge", coolOn, "ON", "OFF", "badge-on", "badge-off");
      document.getElementById("cooling-icon").style.color = coolOn ? "#3b82f6" : "#d1d5db";

      document.getElementById("last-update").textContent = now;
    } catch(e) {
      console.error("Fehler:", e);
    }
  }

  fetchStatus();
  setInterval(fetchStatus, 2000);
</script>
</body>
</html>
    """
    return html

# Server starten
if __name__ == "__main__":   #sicher stellen, der Server nur startet wenn die Datei direkt ausgeführt wird
    app.run(host="0.0.0.0", port=5000, debug=False)
    # 0.0.0.0 den Server im Netzwerk erreichbar
    # debug: verhindern den MQTT-Thread duplizieren würde, da Flask im Debug-Modus eien zweiten Prozess startet.

