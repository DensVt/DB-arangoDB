# код является Python приложением, использующим несколько библиотек, включая Pandas, Requests, NetworkX и pyArango, для загрузки данных из удаленного источника, создания графа, конвертации его в формат GraphML, сохранения в базе данных ArangoDB и предоставления API для получения данных о графе.


import pandas as pd
import requests
import io
import networkx as nx
from pyArango.connection import Connection
from pyArango.collection import Collection, Field
from flask import Flask, request, jsonify
import json


# Создаем соединение с базой данных
conn = Connection(username='root', password='password',
                  arangoURL='http://localhost:8529')
db = conn['_system']

# Загрузка данных из источника
url = 'https://disk.yandex.ru/d/s6wWqd8Ol_5IvQ'
response = requests.get(url)
df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

# Создаем граф
G = nx.Graph()

# Добавляем вершины
for index, row in df.iterrows():
    G.add_node(row['id'], name=row['name'],
               age=row['age'], gender=row['gender'])

# Добавляем ребра
for index, row in df.iterrows():
    for target_vertex_id in df[df['id'] != row['id']]['id']:
        G.add_edge(row['id'], target_vertex_id)

# Конвертируем граф в формат GraphML
graphml_string = nx.readwrite.graphml.generate_graphml(G)

# Создаем коллекцию для хранения GraphML


class MyGraphML(Collection):
    _fields = {
        'name': Field(),
        'graphml': Field()
    }


# Добавляем данные в коллекцию GraphML
graphml_collection = db.createCollection('graphml_collection')
graphml_doc = MyGraphML(graphml_collection)
graphml_doc['name'] = 'example'
graphml_doc['graphml'] = graphml_string
graphml_doc.save()

app = Flask(__name__)

# Получаем коллекцию GraphML
graphml_collection = db['graphml_collection']


@app.route('/graph', methods=['GET'])
def get_graph():
    name = request.args.get('name')

    # Извлекаем GraphML из базы данных
    graphml_doc = graphml_collection.fetchFirstExample({'name': name})
    if len(graphml_doc) == 0:
        return jsonify({'error': 'Graph not found.'}), 404
    else:
        graphml_string = graphml_doc[0]['graphml']

        # Конвертируем GraphML в граф
        G = nx.readwrite.graphml.parse_graphml(graphml_string)

        # Преобразуем граф в JSON-формат
        data = {'nodes': [], 'edges': []}
        for node_id in G.nodes():
            data['nodes'].append({
                'id': node_id,
                'name': G.nodes[node_id]['name'],
                'age': G.nodes[node_id]['age'],
                'gender': G.nodes[node_id]['gender']
            })
        for edge in G.edges():
            data['edges'].append({
                'source': edge[0],
                'target': edge[1]
            })

        # Возвращаем результат в зависимости от указанного формата
        format = request.args.get('format', 'json')
        if format == 'graphml':
            return Response(graphml_string, mimetype='text/xml'), 200
        else:
            return jsonify(data), 200


@app.route('/graph/fio', methods=['GET'])
def get_node_by_fio():
    name = request.args.get('name')
    surname = request.args.get('surname')
    # Извлекаем GraphML из базы данных
    graphml_doc = graphml_collection.fetchFirstExample({'name': 'example'})
    if len(graphml_doc) == 0:
        return jsonify({'error': 'Graph not found.'}), 404
    else:
        graphml_string = graphml_doc[0]['graphml']

        # Конвертируем GraphML в граф
        G = nx.readwrite.graphml.parse_graphml(graphml_string)

        # Ищем вершину по заданным ФИО
        node_id = None
        for n in G.nodes(data=True):
            if n[1]['name'] == name and n[1]['surname'] == surname:
                node_id = n[0]
                break

        # Если вершина найдена, возвращаем ее
        if node_id:
            data = {
                'id': node_id,
                'name': G.nodes[node_id]['name'],
                'surname': G.nodes[node_id]['surname'],
                'age': G.nodes[node_id]['age'],
                'gender': G.nodes[node_id]['gender']
            }
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Node not found.'}), 404


if __name__ == '__main__':
    app.run()
