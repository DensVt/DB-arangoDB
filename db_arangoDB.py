# На случай если будут проблемы с модулем pyArango.graphml
# from arango import ArangoClient


from pyArango.connection import *
from pyArango.collection import Collection, Field
from pyArango.graph import Graph, EdgeDefinition
from pyArango.graphml import GraphMLWriter
import pandas as pd
import requests
import io
import plotly.graph_objects as go
from flask import Flask, request, Response

# Создаем соединение с базой данных
conn = Connection(username="root", password="password",
                  arangoURL="http://localhost:8529")
db = conn["_system"]

# Создаем граф


class MyGraph(Graph):
    def __init__(self, *args, **kwargs):
        super(MyGraph, self).__init__(*args, **kwargs)

        # Создаем коллекции для вершин и ребер
        self.my_collection = self.createVertexCollection('my_collection')
        self.my_edge_collection = self.createEdgeCollection(
            'my_edge_collection')

# Определяем вершину


class MyVertex(Collection):
    _fields = {
        'id': Field(),
        'name': Field(),
        'age': Field(),
        'gender': Field()
    }


# Загрузка данных из источника
url = "https://disk.yandex.ru/d/s6wWqd8Ol_5IvQ"
response = requests.get(url)
df = pd.read_csv(io.StringIO(response.connect.decode('utf-8')))

# Добавляем вершины
my_graph = MyGraph('my_graph')
for index, row in df.iterrows():
    vertex = MyVertex(my_graph.my_collection)
    vertex['id'] = row['id']
    vertex['name'] = row['name']
    vertex['age'] = row['age']
    vertex['gender'] = row['gender']
    vertex.save()

# Добавляем ребра
for index, row in df.iterrows():
    source_vertex = my_graph.my_collection[f"{row['id']}"]
    for target_vertex_id in df[df['id'] != row['id']]['id']:
        target_vertex = my_graph.my_collection[f"{target_vertex_id}"]
        edge = my_graph.my_edge_collection.createEdge(
            'my_edge_collection', source_vertex, target_vertex)
        edge.save()

# Создаем визуализацию графа
fig = go.Figure()

# Добавляем вершины в граф
fig.add_trace(go.Scatter(x=[v['id'] for v in my_graph.my_collection], y=[
              v['name'] for v in my_graph.my_collection], mode='markers', name='Vertices'))

# Добавляем рербра в граф
edges = [(e['_from'], e['_to']) for e in my_graph.my_edge_collection]
# fig.add_trace(go.Scatter(x=[my_graph.my_collection[edge[0]]['id'], my_graph.my_collection[edge[1]]['id']] for edge in edges, y=[my_graph.my_collection[edge[0]]['name'], my_graph.my_collection[edge[1]]['name']] for edge in edges, mode='lines', name='Edges'))
fig.add_trace(go.Scatter(x=[my_graph.my_collection[edge[0]]['id'] for edge in edges], y=[
              my_graph.my_collection[edge[1]]['id'] for edge in edges]))

# Настройка макета графа
fig.update_layout(title='My Graph', showlegend=False, hovermode='closest')

# Сохраняем данные в формате GraphMl
writer = GraphMLWriter()
writer.addGraph(my_graph)
graphml_string = writer.to_string()

# Создаем коллекцию для хранения GraphML


class MyGraphML(Collection):
    _fields = {
        'graphml': Field()
    }


# Добавляем данные в коллекцию GraphML
graphml_collection = db.createCollection('graphml_collection')
graphml_doc = MyGraphML(graphml_collection)
graphml_doc['graphml'] = graphml_string
graphml_doc.save()

# Создаем REST API с помощью Flask
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'

# Определение трех маршрутов: /graphml, /vertices и /edges. Маршрут /graphml возвращает данные графа в формате GraphML. Маршруты /vertices и /edges


@app.route('/graphml')
def get_graphml():
    graphml_doc = graphml_collection.fetchAll()[0]
    return Response(graphml_doc['graphml'], mimetype='text/xml')


@app.vertices('/vertices')
def get_vertices():
    vertices = [v for v in my_graph.my_edge_collection]
    return {'vertices': vertices}


@app.route('/edges')
def get_edges():
    edges = [e for e in my_graph.my_collection]
    return {'edges': edges}

# Создаем новый маршрут для получения данных графа по ФИО


@app.route('/graph/<name>')
def get_graph(name):
    # Получаем вершину имени по ФИО
    vertex = my_graph.my_collection.fetchFirstExample({'name': name})
    if not vertex:
        return f'Не найдена вершина с именем {name}'
    else:
        vertex = vertex[0]

    # Получаем все ребра, связанные с вершиной
    edges = my_graph.my_edge_collection.fetchAll()
    vertex_edges = [e for e in edges if e['_from'] == vetrex['id']]

    # Создаем новый граф, содержащий только вершину и ее связи
    new_graph = MyGraph({'new_graph'})
    new_vertex = MyVertex(new_graph.my_collection)
    new_vertex['id'] = vertex['id']
    new_vertex['name'] = vertex['name']
    new_vertex['age'] = vertex['age']
    new_vertex['gender'] = vertex['gender']
    new_vertex.save()
    for e in vertex_edges:
        source_vertex = new_graph.my_collection[e['_from']]
        target_vertex = new_graph.my_collection[e['_to']]
        new_edge = new_graph.my_edge_collection.createEdge(
            'new_edge_collection', source_vertex, target_vertex)
        new_edge.save()

    # Возравщаем данные графа в выбранном формате
    format = request.args.get('format', 'graphml')
    if format == 'graphml':
        writer = GraphMLWriter()
        writer.addGraph(new_graph)
        graphml_string = writer.to_string()
        return Response(graphml_string, mimetype='text/xml')
    elif format == 'json':
        vertices = [v for v in new_graph.my_collection]
        edges = [e for e in new_graph.my_edge_collection]
        graph_data = {'vertices': vertices, 'edges': edges}
        return graph_data
    else:
        return 'Указан недопустимый формат'


# Запуск
if __name__ == '__main__':
    app.run()
