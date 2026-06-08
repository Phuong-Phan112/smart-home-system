import json         #fuer optionale JSON Nachrichten
import signal       #Beenden
import sys
from typing import Optional #Typ-Hinweise fuer Funktionen, die None zurueckgeben koennen
import paho.mqtt.client as mqtt
BROKER_HOST = 'localhost'
BROKER_PORT = 1883
QOS = 1 # mindesten 1

#Gemeinsamer Zustand
state = {
    "temperature" : 0,
    "light" : 0,
    "heating" : "OFF",
    "cooling" : "OFF"
}

#Hilffunktion: Payload zu int
def parse_int(payload) -> Optional[int]:
#Robuste Umwandlung: Byte -> int, liefert None bei Fehler.
    try:
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode().strip()
        return int(payload)
    except Exception:
        return None
    
#Logik fuer Entscheidung treffen
def decide():
#Entscheidet laut der Temperatur fuer die Heizung/Kühlung
    temp = state["temperature"]
    if temp < 5:
        state["heating"] = "ON"
        state["cooling"] = "OFF"
    elif temp > 25:
        state["heating"] = "OFF"
        state["cooling"] = "ON"
    else:
        state["heating"] = "OFF"
        state["cooling"] = "OFF"

#Ausgabeformatierung
def print_status():
    light_status = "AN" if state["light"] == 1 else "AUS"
    print("------- SMART HOME -------")
    print(f"Temperatur: {state['temperature']}°C")
    print(f"Licht: {light_status}")
    print(f"Heizung: {state['heating']}")
    print(f"Kühlung: {state['cooling']}")
    print("-----------------------------\n")

# Call Back
# Verbindung hergestellt
def on_connect(client, userdata, flags, rc):
    if rc == 0:     #Erfolg
        print("Verbindung mit Broker")
        client.subscribe([("home/temperature", QOS), ("home/light", QOS)]) #Abonniert beide Topics in einem Schritt
        #client.subscribe(("home/sensors", QOS)) #fuer JSON-Topic
    else: 
        print("Verbindungsfehler, rc =", rc)

# Nachricht erhalten
def on_message(client, userdata, msg):
    topic = msg.topic
    if topic == "home/temperature":
        val = parse_int(msg.payload)
        if val is None:
            print("Warnung: ungülltige Temperatur-Payload")
            return
        state["temperature"] = val
        decide()
        print_status()
    elif topic == "home/light":
        val = parse_int(msg.payload)
        if val is None:
            print("Warnung: ungülltige Licht-Payload")
            return
        state["light"] = val
        print_status()

#Beenden
def shutdown(client):
    try:
        client.disconnect()
    finally:
        sys.exit(0)

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        rc = client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        if rc != 0:
            print("Fehler beim Verbinden", rc)
    except Exception as e:
        print("Verbindungsfehler:", e)
        sys.exit(1)
    signal.signal(signal.SIGINT, lambda s, f: shutdown(client))
    signal.signal(signal.SIGTERM, lambda s, f: shutdown(client))
    client.loop_forever() #Endlos Schleife
if __name__ == "__main__":
    main()
