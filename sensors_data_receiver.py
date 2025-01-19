import paho.mqtt.client as mqtt
import time
import json
import ast
import os
from hdfs import InsecureClient

def on_connect(client, userdata, flags, rc):
    """
    Fonction de rappel pour gérer la connexion au courtier MQTT.
    """
    if rc == 0:
         print("Connecté au broker")
         global Connected                
         Connected = True               
    else:
         print("Échec de la connexion")

def on_message(client, userdata, message):
    """
    Fonction de rappel pour gérer les messages MQTT.
    """
    print(message.payload)
    m = ast.literal_eval(str(message.payload.decode("utf-8").replace("np.float64", "")))
    json_object = json.loads(json.dumps(m))
    print(json_object)

    # Stocker les valeurs de données du message dans une chaîne
    data_values = ""
    for key, value in json_object.items():
        if key != "Patient":
            data_values += str(value) + ";"
    data_values = data_values[:-1]
    
    # Enregistrer les données dans un fichier CSV local
    local_file = json_object["Patient"] + '.csv'
    local_file_path = f"csv_data/{local_file}"
    
    # Vérifier si le fichier existe, sinon créer l'entête
    if not os.path.exists(local_file_path):
        with open(local_file_path, 'w') as file:
            file.write(";".join([k for k in json_object.keys() if k != "Patient"]) + "\n")
    
    # Ajouter les données
    with open(local_file_path, 'a') as file:
        file.write(data_values + "\n")
    
    # Charger le fichier dans HDFS
    hdfs_file_path = f"{data_lake_path}/{local_file}"
    if not hdfs_client.status(hdfs_file_path, strict=False):  # Si le fichier n'existe pas dans HDFS
        hdfs_client.upload(hdfs_file_path, local_file_path)  # Charger le fichier complet
    else:
        # Ajouter les nouvelles lignes au fichier HDFS
        with hdfs_client.write(hdfs_file_path, append=True) as hdfs_file:
            hdfs_file.write((data_values + "\n").encode('utf-8'))
    
    print("Données enregistrées dans le datalake HDFS")


Connected = False
 
broker_address = "broker.hivemq.com"
port = 1883                   
 
#hdfs_url = "http://localhost:9870"
#hdfs_client = InsecureClient(hdfs_url)
# Connexion à HDFS
hdfs_client = InsecureClient('http://localhost:50070', user='hdfs')
hdfs_dir = '/data_lake/parkinson_data/'  # Répertoire HDFS où les fichiers seront créés
data_lake_path = "/data_lake/parkinson_data/"
if not hdfs_client.status(data_lake_path, strict=False): # Si le répertoire n'existe pas dans HDFS on le crée
    hdfs_client.makedirs(data_lake_path)
 
print("Création d'une nouvelle instance")
client = mqtt.Client(client_id="python_test")
client.on_message = on_message          # Attacher la fonction au rappel
client.on_connect = on_connect
print("Connexion au broker")
client.connect(broker_address, port)  # Connexion au broker
client.loop_start()                   # Démarrer la boucle
 
while not Connected:                  # Attendre la connexion
    time.sleep(0.1)
 
print("Abonnement au sujet", "test/parkinson")
client.subscribe("test/parkinson")
 
try:
    while True: 
        time.sleep(1)

except KeyboardInterrupt:
    print("Sortie")
    client.disconnect()
    client.loop_stop()
