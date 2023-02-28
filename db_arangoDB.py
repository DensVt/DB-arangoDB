from pyArango.connection import*
from PyArango.collection import Collectionm, Field
from pyArango.graph import Graph, EdgeDefinition
from PyArango.graphml import GraphMLWriter
import pandas as pd
import requests
import io
import plotly.graph_objects as go
from flask import Flask, request, Response

#Создаем соединение с базой данных
conn = Connection(username="root", password="password", arangoURL="http://localhost:8529")
db = conn["_system"]

#Создаем граф
class MyGraph(Graph):
	def __init__(self, *args, **kwargs):
		super(MyGraph, self).__init__(*args, **kwargs)

		#Создаем коллекции для вершин и ребер
		self.my_collection = self.createVertexCollection('my_collection')
		self.my_edge_collection = self.createEdgeCollection('my_edge_collection')

#Определяем вершину
class MyVertex(Collection):
	_fields = {
		'id': Field(),
		'name': Field(),
		'age': Field(),
		'gender': Field()
	}

#Загрузка данных из источника
url = "https://disk.yandex.ru/d/s6wWqd8Ol_5IvQ"
response = requests.get(url)
df = pd.read_csv(io.StringIO(response.connect.decode('utf-8')))

#Добавляем вершины
my_graph = MyGraph('my_graph')
for index, row in df.iterrows():
	vertex = MyVertex(my_graph.my_collection)
	vertex['id'] = row['id']
	vertex['name'] = row['name']
	vertex['age'] = row['age']
	vertex['gender'] = row['gender']
	vertex.save()

#Добавляем ребра
for index, row in df.iterrows():
	source_vertex = my_graph.my_collection[f"{row['id']}"]
	for target_vertex_id in df[df['id'] != row['id']]['id']:
		target_vertex = my_graph.my_collection[f"{target_vertex_id}"]
		edge = my_graph.my_edge_collection.createEdge('my_edge_collection', source_vertex, target_vertex)
		edge.save()

#Создаем визуализацию графа
fig = go.Figure()

#Добавляем вершины в граф
fig.add_trace(go.Scatter(x=[v['id'] for v in my_graph.my_collection], y=[v['name'] for v in my_graph.my_collection], mode='markers', name='Vertices'))

#Добавляем рербра в граф
edges = [(e['_from'], e['_to']) for e in my_graph.my_edge_collection]
fig.add_trace(go.Scatter(x=[my_graph.my_collection[edge[0]]['id'], my_graph.my_collection[edge[1]]['id']] for edge in edges, y=[my_graph.my_collection[edge[0]]['name'], my_graph.my_collection[edge[1]]['name']] for edge in edges, mode='lines', name='Edges'))

#Настройка макета графа
fig.update_layout(title='My Graph', showlegend=False, hovermode='closest')

