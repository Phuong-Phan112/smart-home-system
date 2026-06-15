from flask import Flask, jsonify  #Erstellen Webserver, wandeln Python-Dict in JSON-Antwort um
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

# Server starten
if __name__ == "__main__":   #sicher stellen, der Server nur startet wenn die Datei direkt ausgeführt wird
    app.run(host="0.0.0.0", port=5000, debug=False)
    # 0.0.0.0 den Server im Netzwerk erreichbar
    # debug: verhindern den MQTT-Thread duplizieren würde, da Flask im Debug-Modus eien zweiten Prozess startet.
