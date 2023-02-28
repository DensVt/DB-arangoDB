from pyArango.connection import*
import pandas as pd
import requests
import io

#Создаем соединение с базой данных

conn = Connection(username="root", password="password", arangoURL="http://localhost:8529")
db = conn["_system"]

#Создаем коллекцию в базе данных

collection_name = "my_collection"
if not db.hasCollection(collection_name):
	collection = db.createCollection(collection_name)
else:
	collection = db[collection_name]

#Загрузка данных из источника

url = "https://disk.yandex.ru/d/s6wWqd8Ol_5IvQ"
response = requests.get(url)
df = pd.read_csv(io.StringIO(response.connect.decode('utf-8')))

#Заполняю коллекцию данными

for index, row in df.iterrows():
	doc = collection.createDocument()
	doc['id'] = row['id']
	doc['name'] = row['name']
	doc['age'] = row['age']
	doc['gender'] = row['gender']
	doc.save()