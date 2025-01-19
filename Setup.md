# Setup Guide

This document provides a step-by-step walkthrough to configure the tools required for the Big Data Pipeline. Follow each stage to set up the pipeline, from data collection to dashboard visualization.

---

## 1. Configuring Data Collection

### Install MQTT Broker
1. Install an MQTT broker such as **Mosquitto**:
   ```bash
   sudo apt update
   sudo apt install mosquitto mosquitto-clients
   ```
2. Start the Mosquitto service:
   ```bash
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```
3. Configure the MQTT broker to accept connections from the sensors by editing the configuration file:
   ```bash
   sudo nano /etc/mosquitto/mosquitto.conf
   ```
   Add:
   ```
   allow_anonymous true
   listener 1883
   ```
4. Restart the Mosquitto service:
   ```bash
   sudo systemctl restart mosquitto
   ```

---

## 2. Setting Up the Hadoop Data Lake

### Install Hadoop
1. Download and extract Hadoop:
   ```bash
   wget https://downloads.apache.org/hadoop/common/hadoop-x.x.x/hadoop-x.x.x.tar.gz
   tar -xzf hadoop-x.x.x.tar.gz
   ```
2. Configure Hadoop environment variables by editing `.bashrc`:
   ```bash
   export HADOOP_HOME=/path/to/hadoop
   export PATH=$PATH:$HADOOP_HOME/bin
   ```
3. Format the Hadoop namenode:
   ```bash
   hdfs namenode -format
   ```
4. Start Hadoop services:
   ```bash
   start-dfs.sh
   start-yarn.sh
   ```

---

## 3. Configuring Kafka Streaming

### Install Kafka
1. Download Kafka:
   ```bash
   wget https://downloads.apache.org/kafka/x.x.x/kafka_2.x-x.x.x.tgz
   tar -xzf kafka_2.x-x.x.x.tgz
   ```
2. Start the Zookeeper service:
   ```bash
   bin/zookeeper-server-start.sh config/zookeeper.properties
   ```
3. Start the Kafka broker:
   ```bash
   bin/kafka-server-start.sh config/server.properties
   ```
4. Create a Kafka topic:
   ```bash
   bin/kafka-topics.sh --create --topic sensor-data --bootstrap-server localhost:9092
   ```

---

## 4. Configuring Apache Spark

### Install Spark
1. Download Spark:
   ```bash
   wget https://downloads.apache.org/spark/spark-x.x.x/spark-x.x.x-bin-hadoopx.tgz
   tar -xzf spark-x.x.x-bin-hadoopx.tgz
   ```
2. Configure Spark environment variables in `.bashrc`:
   ```bash
   export SPARK_HOME=/path/to/spark
   export PATH=$PATH:$SPARK_HOME/bin
   ```
3. Start the Spark shell to verify installation:
   ```bash
   spark-shell
   ```

---

## 5. Setting Up Cassandra Database

### Install Cassandra
1. Add the Cassandra repository:
   ```bash
   echo "deb http://www.apache.org/dist/cassandra/debian 311x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
   ```
2. Install Cassandra:
   ```bash
   sudo apt update
   sudo apt install cassandra
   ```
3. Start the Cassandra service:
   ```bash
   sudo systemctl start cassandra
   sudo systemctl enable cassandra
   ```
4. Verify the installation:
   ```bash
   cqlsh
   ```

---

## 6. Setting Up Flask API with Scikit-learn

### Install Flask
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install Flask and Scikit-learn:
   ```bash
   pip install flask scikit-learn
   ```
3. Create a Flask app:
   ```bash
   touch app.py
   ```
   Example `app.py`:
   ```python
   from flask import Flask
   app = Flask(__name__)

   @app.route('/')
   def home():
       return "Big Data Pipeline API"

   if __name__ == '__main__':
       app.run(debug=True)
   ```
4. Run the Flask app:
   ```bash
   python app.py
   ```

---

## 7. Configuring MongoDB Atlas Visualization

### Set Up MongoDB Atlas
1. Create a MongoDB Atlas account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a new cluster and database.
3. Connect to the cluster using the connection string.
4. Install the MongoDB Python driver:
   ```bash
   pip install pymongo
   ```
5. Use MongoDB Atlas dashboards to create visualizations for:
   - Real-time pressure distributions.
   - Historical trends.
   - Detected anomalies.

---

## Final Steps
1. Verify that all components are running:
   - Sensors are transmitting data via MQTT.
   - Hadoop, Kafka, Spark, Cassandra, and Flask are operational.
   - Dashboards in MongoDB Atlas display expected data.
2. Add screenshots of each stage to complete the documentation.

---

Your pipeline is now ready to process and visualize real-time data!
