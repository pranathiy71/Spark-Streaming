All the steps given below are run on Mac:

1. Pip install pyspark, nltk, kafka-python

2. Open two terminals and cd into kafka directory. In one terminal run zookeeper service, bin/zookeeper-server-start.sh config/zookeeper.properties. In another terminal run kafka broker service, bin/kafka-server-start.sh config/server.properties.

3. Open three more terminals and cd into kafka directory.
3(a). In terminal 1, create two topics by running these commands -
        bin/kafka-topics.sh --create --topic news_tesla --bootstrap-server localhost:9092
        bin/kafka-topics.sh --create --topic named_ent_count --bootstrap-server localhost:9092
3(b). Run python3 newsTopicOne.py "YOUR API KEY" localhost:9092 news_tesla. this code reads news API, and extracts named entities and sent to kafka topic 1 through KafkaProducer
3(c). In terminal 2, run bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic named_ent_count --from-beginning which consumes data from the 2nd topic named_ent_count
3(d). In terminal 3, run python3 writeTopicTwo.py localhost:9092 news_tesla named_ent_count. This code reads from topic 1, counts named entities and writes to 2nd topic every 15 mins.

4. Download elasticsearch, from https://www.elastic.co/downloads/
4(a). Open a new terminal, and cd into elasticsearch folder and run bin/elasticsearch

5. Download kibana, from https://www.elastic.co/downloads/kibana
5(a). Open a new terminal, and cd into kibana folder and run bin/kibana
5(b). To configure kibana on localhost:5601, we get enrollment token and password for username "elastic" in the elastic terminal after we run bin/elasticsearch

6. Download logstash, and cd into that folder and run curl -k -u elastic https://localhost:9200 to check if we are getting a positive response.
6(a). Write logstash configuration file "elasticsearch.conf". My configuration is given below -
input {
  kafka {
      bootstrap_servers => ["localhost:9092"]
      topics => ["named_ent_count"]
      codec => json
      group_id => "logstash-consumer-group"
      auto_offset_reset => "earliest"
  }
}

output {
  elasticsearch {
    hosts => ["https://localhost:9200"]
    index => "named_ent_count"
    ssl_certificate_verification => false
    user => "elastic"
    password => "5M83QjSj0MfMhQpYVVW="
  }
  stdout {}
}
Note: I have used https for elasticsearch hosts due to security reasons(http was not producing output as it was not secure.)

7. In localhost:5601, go to Discover under Analytics and select the index you have set in your logstash config. Choose the available field to be word(word.keyword) and select visualize button in the bottom and choose bar graph. Top right corner, you have the option to select the visualizations for customized amount of time which we have done for 15, 30, 45, 60 mins.
