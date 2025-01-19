from hdfs import InsecureClient
from confluent_kafka import Producer
import json
import pandas as pd

def delivery_report(err, msg):
    """
    Fonction de rappel pour gérer les retours de livraison des messages Kafka.
    """
    if err is not None:
        print(f'Échec de livraison du message pour {msg.key()}: {err}')
    else:
        print(f'Message livré pour {msg.key()}')

def produce_sensor_data(producer, topic, file_name, file_content):
    """
    Fonction pour produire des données de capteur vers Kafka.
    """
    group = file_name[2:4]

    message = {
        "file_name": file_name,
        "content": file_content,
        "group": group
    }
   
    producer.produce(topic, key=file_name, value=json.dumps(message), callback=delivery_report)
    producer.poll(0)  # Poll pour envoyer les messages en attente
    producer.flush()  # Force la livraison des messages

# Remplacez avec les détails de votre cluster HDFS
hdfs_url = "http://localhost:50070"
data_lake_path = "/data_lake/parkinson_data"

client = InsecureClient(hdfs_url)

# Liste des fichiers dans le répertoire Data Lake
files_in_data_lake = client.list(data_lake_path)

# Configuration du producteur Kafka
producer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'python-producer'
}

# Création de l'instance du producteur Kafka
producer = Producer(producer_conf)

# Lire le contenu de chaque fichier
for file_name in files_in_data_lake:
    print(f"Traitement du fichier: {file_name}")
    hdfs_file_path = f"{data_lake_path}/{file_name}"
    
    with client.read(hdfs_file_path, encoding='utf-8') as reader:
        file_content = reader.read()
    
    # Envoi de chaque ligne de fichier comme message Kafka
    for line in file_content.split("\n"):
        if line.strip():  # Ignore les lignes vides
            print(f"Envoi de la ligne: {line}")
            produce_sensor_data(producer, "sensor_data", file_name.split(".")[0], line)
    
    # Optionnel : Afficher la taille du contenu pour débogage
    print(f"Taille du contenu du fichier {file_name}: {len(file_content)}")

# Si vous avez encore des fichiers non envoyés en raison des buffers Kafka, vous pouvez les envoyer ici.
producer.flush()
