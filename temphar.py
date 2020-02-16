import os, sys, time, datetime
import paho.mqtt.client as mqtt
import requests, json

sensoren = {
    'Wasserleitung': '28-020792457c00',
    'Decke': '28-020992451c19',
    'Onboard': '28-00000887bf60'}
oberwinter = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/b45359df-c020-4314-adb1-d1921db642da.json?includeTimeseries=true&includeCurrentMeasurement=true"

# sensoren = {"Wasserleitung": wasserleitung, "Decke": decke, "Onboard": onboard}
def aktuelleTemperatur(sensor):
    # 1-wire Slave Datei lesen
    try:
        datei = '/sys/bus/w1/devices/'+sensor+'/w1_slave'
        file = open(datei)
        filecontent = file.read()
        file.close()
    except FileNotFoundError:
        print('Datei '+datei+'nicht gefunden')
        return None

    # Temperaturwert auslesen und konvertieren
    stringvalue = filecontent.split("\n")[1].split(" ")[9]
    temperatur = float(stringvalue[2:])/1000
    return temperatur

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    return rc

def mqttVerbindungsaufbau():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.username_pw_set("openhab", password="openhab")
    client.connect("192.168.1.36", 1883, 60)
    client.loop_start()
    return client


def messen(client):
    print("Temperaturabfrage")
    for name in sensoren:
        sensor = sensoren[name]
        messdaten = aktuelleTemperatur(sensor)
        zeitstempel = datetime.datetime.now().timestamp()
        if messdaten != None:
            protokoll = str(zeitstempel) + ": " + name + ": " + str(messdaten)
            print(protokoll)
            with open("messdaten.log", "a") as file:
                file.write(protokoll + "\n")
            client.publish("haus/har/temperatur/"+name, messdaten)
        else:
            print(name + ': Messfehler')
    print("finished")

def pegel(url):
    my_pegel_request = requests.get(url)
    my_pegel_text = my_pegel_request.text
    my_pegel_json = json.loads(my_pegel_text)
    my_pegel = float(my_pegel_json["timeseries"][0]["currentMeasurement"]["value"])
    return my_pegel


mqtt = mqttVerbindungsaufbau()

while True:
    messen(mqtt)
    mqtt.publish("haus/pegel/oberwinter", pegel(oberwinter))
    time.sleep(900)

mqtt.loop_stop()
mqtt.disconnect()
