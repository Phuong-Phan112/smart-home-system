#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include "MQTTClient.h"

#define ADDRESS     "tcp://localhost:1883"
#define CLIENTID    "SmartHomeSensor"
#define TOPIC_TEMP  "home/temperature"
#define TOPIC_LIGHT "home/light"
#define QOS         1

int main() {
    MQTTClient client;
    MQTTClient_connectOptions conn_opts = MQTTClient_connectOptions_initializer;

    //client erstellen
    MQTTClient_create(&client, ADDRESS, CLIENTID, MQTTCLIENT_PERSISTENCE_NONE, NULL);
    //Speicherort des clients, Broker-Adresse, Name des clients, nicht speichern, keine extra Daten

    //Verbindung zum Broker
    int rc = MQTTClient_connect(client, &conn_opts);

    //Fehler pruefen
    if (rc != MQTTCLIENT_SUCCESS) {
        printf("Fehler: Verbindung fehlgeschlagen (%d)\n", rc);
        return -1;
    }
    //Wenn die Verbindung fehlschlägt, Fehlermeldung ausgeben und Programm stoppen

    //Zufallszahlen vorbereiten, ohne das waeren die Werte immer gleich
    srand(time(NULL));

    //Startmeldung
    printf("Sensor läuft...\n");

    while (1) {
        int temp = -10 + rand() % 50;  //Sensordaten von Tempearatur erzeugen, erzeugt Wert von -10 bis 39
        int light = rand() % 2; //Sensordaten von Licht erzeugen, 0 = aus, 1= an

        //Zahlen in Text umwandeln
        char temp_msg[10];
        char light_msg[10];
        //wahdelt Zahlen in Strings um. MQTT sendet Daten als Text/Bytes
        sprintf(temp_msg, "%d", temp);
        sprintf(light_msg, "%d", light);

        //MQTT-Nachricht vorbereiten
        MQTTClient_message msg = MQTTClient_message_initializer;
        msg.qos = QOS;

        //Temperatur senden, Inhalt und Laenge der Nachricht setzen
        msg.payload = temp_msg;
        msg.payloadlen = strlen(temp_msg);
        MQTTClient_publish(client, TOPIC_TEMP, msg.payloadlen, msg.payload, QOS, 0, NULL);

        //Licht senden
        msg.payload = light_msg;
        msg.payloadlen = strlen(light_msg);
        MQTTClient_publish(client, TOPIC_LIGHT, msg.payloadlen, msg.payload, QOS, 0, NULL);

        //Werte anzeigen
        printf("Temp: %d | Light: %d\n", temp, light);
        sleep(5);  //5s neu Dateien senden
    }

    //Verbindung trennen und Speicher freigeben
    MQTTClient_disconnect(client, 1000);
    MQTTClient_destroy(&client);
    return 0;
}