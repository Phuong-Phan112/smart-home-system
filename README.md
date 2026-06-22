# Smart Home System
Smart-Home Dashboard mit automatischer Steuerung
## Idee
Ein Smartes Haus wird simuliert durch:
-Sensoren senden Daten: Temperatur, Licht
-Steuerung reagiert automatisch
-Visualisierung zeigt Status

## Architektur
Sensor (sendet Temperatur und Licht) -> MQTT Broker (verteilt Nachrichten) -> Controller (entscheidet was passiert) -> Anzeige

## Ziel
Das System verarbeitet mehrere Sensordaten gleichzeitig, darunter Temperatur und Lichtstatus. Diese werden über verschiedene MQTT‑Topics übertragen und von einem zentralen Controller verarbeitet, der entsprechende Aktionen ausführt

# Starten
## MQTT 
Das System verarbeitet mehrere Sensordaten gleichzeitig, die über separate MQTT‑Topics übertragen werden
## Sensor mit C
Temperatur und Licht erzeugen, beide Wert über MQTT senden, alle 2s wiederholen

sensor.c
## Controller mit Python
Empfängt MQTT Daten -> verarbeitet sie -> entscheidet Heizung/Licht -> zeigt Ergebnis im Terminal

controller.py
## Daten strukturieren und vorbereiten für Dashboard
- Ziel: Daten werden gespeichert; aktueller Systemzustand bleibt erhalten; Vorbereitung für Web‑Dashboard;sauberer Output
- Idee: Statt nur zu gucken, speichern jetzt alles in einer Datenstruktur

controller2.py
## REST API
Eine Schnittstelle, über die man Daten über eine URL abfragen kann
Testen im Browser: http://localhost:5000/status 

## Dashboard aufbauen
Jetzt hinfügen die Dashboard-Route -> Dashboard wird gezeigt