from pyspark.sql import SparkSession
from pyspark.sql.functions import split, explode, count as spark_count
from pyspark.conf import SparkConf
from kafka import KafkaProducer
import json

# Set up the SparkSession
spark_conf = SparkConf() \
    .set("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .setAppName("NamedEntityCounter")

spark = SparkSession.builder \
    .appName("NamedEntityCounter") \
    .config(conf=spark_conf) \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
bootstrapServer = 'localhost:9092'

# Kafka producer setup using localhost bootstrap server and 
# value_serializer specifies how the values of the records sent by the producer should be serialized before being sent to Kafka. 
# Lambda function takes the value x, converts it to a JSON string using json.dumps(x), and then encodes it to bytes using UTF-8 encoding.
# The values sent to Kafka are JSON-encoded bytes which provides a convenient and standardized way to represent structured data.

kafProducer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda x: json.dumps(x).encode('utf-8'))

# Read from topic 1
df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "localhost:9092") \
  .option("subscribe", "news_tesla") \
  .option("failOnDataLoss", "false") \
  .load() \
  .selectExpr("CAST(value AS STRING)")


# Split all the words with each word taking up a row
words = df.select(
    explode(
      split(df.value, ' ')
    ).alias('word')
)

# This function will send named entities and their counts to topic 2
def produceToKafka(wordsDf, itr):
    namedEntCount = wordsDf \
        .groupBy("word").agg(spark_count("word").alias("count")) \
        .orderBy("count", ascending=False) \
        .limit(10)

    for row in namedEntCount.collect():
        kafProducer.send('named_ent_count', value=row.asDict())

    namedEntCount.show(truncate=False)

# Write the named entities and their counts to topic 2
namedEntitiesCountWrite = words \
    .writeStream \
    .foreachBatch(produceToKafka) \
    .outputMode("update") \
    .trigger(processingTime='15 minutes') \
    .option("topic", "named_ent_count") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("checkpointLocation", "./checkpoint") \
    .start()

# Starting the streaming query
namedEntitiesCountWrite.awaitTermination()
