# новый маршрут /graph/<name>, который принимает ФИО в качестве параметра. Затем мы получаем вершину с помощью запроса fetchFirstExample и все связанные с ней ребра. Затем мы создаем новый граф, который содержит только эту вершину и ее связи, и возвращаем данные графа в выбранном формате. Если формат не указан или указан неверно, мы возвращаем сообщение об ошибке.

# Чтобы использовать этот маршрут, нужно отправить GET-запрос на /graph/<name>?format=<format>, где <name> - ФИО вершины, а <format> - формат, в котором нужно вернуть данные (по умолчанию GraphML). Если вы хотите получить данные в формате JSON, укажите format=json в запросе.


# Создаем новый маршрут для получения данных графа по ФИО
@app.route('/graph/<name>')
def get_graph(name):
    # Получаем вершину по ФИО
    vertex = my_graph.my_collection.fetchFirstExample({'name': name})
    if not vertex:
        return f'No vertex found with name {name}'
    else:
        vertex = vertex[0]

    # Получаем все ребра, связанные с этой вершиной
    edges = my_graph.my_edge_collection.fetchAll()
    vertex_edges = [e for e in edges if e['_from'] == vertex['_id']]

    # Создаем новый граф, содержащий только вершину и ее связи
    new_graph = MyGraph('new_graph')
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

    # Возвращаем данные графа в выбранном формате
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
        return 'Invalid format specified'
