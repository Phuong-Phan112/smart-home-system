from flask import Flask, jsonify  # Webserver + JSON-Antwort
import paho.mqtt.client as mqtt
import threading                  # thread-sicheren Zugriff auf gemeinsame Daten

app = Flask(__name__)

# Zustand + Lock
state = {
    "Temperature": 0,
    "Light": 0,
    "Heating": "OFF",
    "Cooling": "OFF"
}
state_lock = threading.Lock()  # sicherstellen, dass nie 2 Threads gleichzeitig 

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:        # Fehlerprüfung
        print("Verbunden mit Broker")
        client.subscribe([("home/temperature", 1), ("home/light", 1)])  # ein Aufruf statt zwei
    else:
        print("Verbindungsfehler, rc =", rc)

def on_message(client, userdata, msg):
    try:  # Absturz bei ungültiger Payload verhindern
        val = int(msg.payload.decode().strip())
    except ValueError:
        print(f"Warnung: ungültige Payload auf {msg.topic}: {msg.payload}")
        return

    with state_lock:   # state sperren beim Schreiben
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
@app.route("/status")  # URL registrieren
def get_status():
    with state_lock:           # state sperren beim Lesen
        snapshot = dict(state) # Kopie erstellen, dann Lock freigeben
    return jsonify(snapshot)

# Dashboard
@app.route("/")
def dashboard():
    html = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Smart Home Dashboard</title>
</head>
<body>
  <h1>Smart Home Dashboard</h1>

  <p><b>Temperatur:</b> <span id="temp-val">—</span> °C</p>
  <p><b>Licht:</b> <span id="light-val">—</span></p>
  <p><b>Heizung:</b> <span id="heating-val">—</span></p>
  <p><b>Kühlung:</b> <span id="cooling-val">—</span></p>

  <p>Letzte Aktualisierung: <span id="last-update">—</span></p>

  <script>
    async function fetchStatus() {
      const res  = await fetch("/status");
      const data = await res.json();

      document.getElementById("temp-val").textContent    = data.Temperature;
      document.getElementById("light-val").textContent   = data.Light === 1 ? "AN" : "AUS";
      document.getElementById("heating-val").textContent = data.Heating;
      document.getElementById("cooling-val").textContent = data.Cooling;
      document.getElementById("last-update").textContent = new Date().toLocaleTimeString("de-DE");
    }

    fetchStatus();
    setInterval(fetchStatus, 2000);  // alle 2 Sekunden aktualisieren
  </script>
</body>
</html>
    """
    return html

# MQTT starten
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:  # Fehlerbehandlung
    client.connect("localhost", 1883, 60)
except Exception as e:
    print("MQTT-Verbindungsfehler:", e)

client.loop_start()

# Server starten
if __name__ == "__main__":   # Server startet nur wenn Datei direkt ausgeführt wird
    app.run(host="0.0.0.0", port=5000, debug=False)
    # host="0.0.0.0" → Server im ganzen Netzwerk erreichbar
    # debug=False    → verhindert dass Flask den MQTT-Thread dupliziert