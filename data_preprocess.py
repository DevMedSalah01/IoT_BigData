from confluent_kafka import Consumer, KafkaError
import json
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType
from cassandra.cluster import Cluster

class Cassandra:
    def __init__(self, create_keyspace_query, keyspace_name, table_name):
        self.cluster = Cluster(['127.0.0.1'])  # Mettez l'IP appropriée ici
        self.session = self.cluster.connect()
        self.session.execute(create_keyspace_query)
        self.session.set_keyspace(keyspace_name)
        self.table_name = table_name
        self._create_table()

    def _create_table(self):
        check_table_query = f"SELECT table_name FROM system_schema.tables WHERE keyspace_name = '{self.session.keyspace}' AND table_name = '{self.table_name}'"
        clear_table_query = f"TRUNCATE TABLE {self.table_name};"
        table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            Time DOUBLE,
            L1 DOUBLE, L2 DOUBLE, L3 DOUBLE, L4 DOUBLE, L5 DOUBLE, L6 DOUBLE, L7 DOUBLE, L8 DOUBLE,
            R1 DOUBLE, R2 DOUBLE, R3 DOUBLE, R4 DOUBLE, R5 DOUBLE, R6 DOUBLE, R7 DOUBLE, R8 DOUBLE,
            L DOUBLE, R DOUBLE,
            Class INT,file_name TEXT,
            PRIMARY KEY (file_name, Time)
        );  
        """

        try:
            result = self.session.execute(check_table_query)
            table_exists = any(row.table_name == self.table_name for row in result)

            if table_exists:
                print(f"La table {self.table_name} existe. Suppression de toutes les entrées...")
                self.session.execute(clear_table_query)

            print(f"Création ou vérification de la table {self.table_name}...")
            self.session.execute(table_query)
            print(f"Table {self.table_name} mise à jour avec succès.")

        except Exception as e:
            print(f"Erreur lors de la création ou de l'actualisation de la table : {e}")

    def insert_data(self, data):
        # Vérification du type de données
        print(f"Type de 'data': {type(data)}")
        print(f"Contenu de 'data': {data}")
        
        # Requête d'insertion
        insert_query = f"""
        INSERT INTO {self.table_name} (
            Time, L1, L2, L3, L4, L5, L6, L7, L8, R1, R2, R3, R4, R5, R6, R7, R8, L, R, Class,file_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Préparation de la requête
        prepared = self.session.prepare(insert_query)
        print(f"Insertion de {len(data)} lignes de données dans Cassandra")
        
        # Itération sur chaque ligne de données dans `data` (assumant que `data` est une liste de Row)
        for row in data:
            # Vérification de la validité de la ligne : doit avoir 21 éléments
            if len(row) != 21:
                print(f"Ligne invalide : {len(row)} éléments. Ligne : {row}")
                continue
            
            # Préparation des valeurs à insérer : convertir la Row en tuple (ordre des colonnes respecté)
            row_values = tuple(row)  # Si `row` est un objet Row, cette opération fonctionnera normalement
            
            # Essayer d'exécuter l'insertion
            try:
                print(f"Insertion de la ligne : {row_values}")
                self.session.execute(prepared, row_values)
            except Exception as e:
                print(f"Erreur lors de l'insertion de la ligne {row_values} : {e}")


    def query_data(self):
        query = f"SELECT * FROM {self.table_name} LIMIT 10;"
        rows = self.session.execute(query)
        print("Données récupérées de la table Cassandra :")
        for row in rows:
            print(row)

    def close(self):
        self.cluster.shutdown()


def retrieve_data(consumer, topic):
    consumer.subscribe([topic])
    patient_data = dict()
    print("En attente de messages...")
    first_message = False

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            if first_message:
                break
            else:
                continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(msg.error())
                break

        try:
            first_message = True
            data = json.loads(msg.value())
            print(f"Message reçu : {msg.value()}")

            if isinstance(data["content"], str):
                row = data["content"].split(";")
                if len(row) == 19:
                    row = [float(x) for x in row]
                    row.append(0 if data["group"] == "Co" else 1)  # Class
                    row.append(data["file_name"])  # file_name

                    if data["file_name"] not in patient_data:
                        patient_data[data["file_name"]] = []
                    patient_data[data["file_name"]].append(row)

        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON : {e}")
        except KeyError as e:
            print(f"Clé manquante dans le JSON : {e}")
        except ValueError as e:
            print(f"Erreur de conversion des données : {e}")

    consumer.close()
    print("Terminé")
    return patient_data


def preprocess_data(patient_data):
    spark = SparkSession.builder.appName('PatientData').getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    schema = StructType([
        StructField("Time", FloatType(), True),
        StructField("L1", FloatType(), True), StructField("L2", FloatType(), True),
        StructField("L3", FloatType(), True), StructField("L4", FloatType(), True),
        StructField("L5", FloatType(), True), StructField("L6", FloatType(), True),
        StructField("L7", FloatType(), True), StructField("L8", FloatType(), True),
        StructField("R1", FloatType(), True), StructField("R2", FloatType(), True),
        StructField("R3", FloatType(), True), StructField("R4", FloatType(), True),
        StructField("R5", FloatType(), True), StructField("R6", FloatType(), True),
        StructField("R7", FloatType(), True), StructField("R8", FloatType(), True),
        StructField("L", FloatType(), True), StructField("R", FloatType(), True),
        StructField("Class", IntegerType(), True),
        StructField("file_name", StringType(), True),
    ])

    all_data = []

    for file_name, data in patient_data.items():
        spark_df = spark.createDataFrame(data, schema=schema)
        print(f"Preprocessed data for file: {file_name}")
        all_data.extend(spark_df.collect())

    return all_data

# Configuration du consommateur Kafka
consumer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'python-consumer',
    'auto.offset.reset': 'earliest'
}

# Création de l'instance du consommateur Kafka
consumer = Consumer(consumer_conf)

patient_data = retrieve_data(consumer, "sensor_data")

# Affichage des données récupérées
#print(f"Retrieved patient data: {patient_data}")

preprocessed_data = preprocess_data(patient_data)

# Affichage des données prétraitées
#print(f"Preprocessed patient data: {preprocessed_data}")

# Définition des paramètres de l'espace de clés Cassandra
keyspace_name = 'parkinson'
replication_strategy = 'SimpleStrategy'
replication_factor = 3

# Création de la requête de création de l'espace de clés
create_keyspace_query = f"""
    CREATE KEYSPACE IF NOT EXISTS {keyspace_name}
    WITH replication = {{'class': '{replication_strategy}', 'replication_factor': {replication_factor}}};
"""

# Initialisation de l'instance Cassandra et insertion des données
cassandra = Cassandra(create_keyspace_query, keyspace_name, table_name='data')
cassandra.insert_data(preprocessed_data)
# Tester et afficher le contenu de la table
cassandra.query_data()

cassandra.close()
