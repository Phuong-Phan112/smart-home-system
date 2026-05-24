import paho.mqtt.client as mqtt

# Globale Variablen
temperature = 0
light = 0

# Call Back
# Verbindung hergestellt
def on_connect(client, userdata, flags, rc):
    print("Verbunden mit Broker")
    client.subscribe("home/temperature")
    client.subscribe("home/light")

# Nachricht erhalten
def on_message(client, userdata, msg):
    global temperature, light
    
    if msg.topic == "home/temperature":
        temperature = int(msg.payload.decode())
        
    elif msg.topic == "home/light":
        light = int(msg.payload.decode())

    # Entscheidung treffen
    decide()  # der aktuellen Werte den Systemstatus berechnen und anzeigen

# Logik fuer Entscheidung treffen
def decide():
    # Temperatur-Logik
    if temperature < 5:
         heating = "AN"
    elif temperature > 25:
        heating = "AUS (Kühlung AN)"
    else:
        heating = "OK "
         
     # Licht-Logik
    if light == 1:
        light_status = "AN "
    else:
        light_status = "AUS "
        
     # Ausgabe
    print("------- SYSTEM STATUS -------")
    print(f"Temperatur: {temperature}°C")
    print(f"Licht: {light_status}")
    print(f"Heizung/Klima: {heating}")
    print("-----------------------------\n")

# MQTT Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.loop_forever()