from kafka import KafkaProducer
import requests
import time
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# API endpoint and parameters for News articles on Tesla
apiEndpoint = 'https://newsapi.org/v2/everything'
queryParams = {
    'q': 'tesla',
    'from': '2024-03-14',
    'sortBy': 'publishedAt',
    'apiKey': '2cb949194e494e57a58e34929fb89df0'
}
bootstrapServer = ['localhost:9092']

# Kafka producer setup using localhost bootstrap server
kafProducer = KafkaProducer(bootstrap_servers=bootstrapServer)
stopWords = set(stopwords.words('english'))
regPattern = '[a-zA-Z]'

# Get named entities from the API response by removing stopwords and alphanumeric words
while(True):
    response = requests.get(apiEndpoint, params=queryParams)
    data = response.json()
    teslaArticles = data['articles']
    
    result = []
    for article in teslaArticles:
        if 'description' in article and article['description']:
            result.append(article['description'])

    dataFiltered = []
    for text in result:
        words = word_tokenize(text)
        words_filtered = [item for item in words if re.search(regPattern, item)]
        
        for word in words_filtered:
            if (word.lower() not in stopWords and len(word) > 3):
                dataFiltered.append(word)
    
    text = " ".join(dataFiltered)
    textFinal = bytes(text, 'utf-8')
    kafProducer.send('news_tesla', textFinal)
    
    time.sleep(60)
