import numpy as np

from src.geohash import encode


def gerar_frota(
    quantidade,
    restaurantes,
    corrigir_para_ruas=False,
    seed=None,
):
    """
    Gera entregadores em torno dos restaurantes.

    restaurantes: lista de dicionários no formato:
        {"id": 1, "nome": "Restaurante A",
         "lat": -19.93, "lon": -43.94}

    Retorna uma lista de dicionários.
    """
    if quantidade < 0:
        raise ValueError("A quantidade não pode ser negativa.")

    if not restaurantes:
        raise ValueError("Informe pelo menos um restaurante.")

    rng = np.random.default_rng(seed)

    # Distribuição equilibrada dos entregadores entre os centros.
    centros = np.arange(quantidade) % len(restaurantes)
    rng.shuffle(centros)

    entregadores = []

    for i, indice_centro in enumerate(centros):
        restaurante = restaurantes[indice_centro]

        # Desvios-padrão aproximados em graus.
        # 0,006 grau de latitude equivale a cerca de 0,67 km.
        lat = rng.normal(restaurante["lat"], 0.006)
        lon = rng.normal(restaurante["lon"], 0.008)

        entregadores.append({
            "id": i + 1,
            "lat": float(lat),
            "lon": float(lon),
            "restaurante_centro": restaurante["id"],
        })

    if corrigir_para_ruas and entregadores:
        entregadores = projetar_para_ruas(entregadores)

    # Geohash com precisão 8 para cada posição.
    for entregador in entregadores:
        entregador["geohash"] = encode(
            entregador["lat"],
            entregador["lon"],
            precision=8,
        )

    return entregadores


def projetar_para_ruas(entregadores):
    """
    Substitui posições sintéticas pelas coordenadas dos nós
    viários mais próximos da malha de ruas do OpenStreetMap.
    """
    import osmnx as ox

    latitudes = [e["lat"] for e in entregadores]
    longitudes = [e["lon"] for e in entregadores]

    # Baixa a malha viária dirigível em torno de Belo Horizonte.
    norte, sul = -19.80, -20.05
    leste, oeste = -43.85, -44.05

    try:
        grafo = ox.graph_from_bbox(
            (oeste, sul, leste, norte),
            network_type="drive",
        )
    except Exception as erro:
        raise RuntimeError(
            "Não foi possível obter a malha viária do OpenStreetMap."
        ) from erro

    nos = ox.distance.nearest_nodes(
        grafo,
        X=longitudes,
        Y=latitudes,
    )

    for entregador, no in zip(entregadores, nos):
        entregador["lat"] = float(grafo.nodes[no]["y"])
        entregador["lon"] = float(grafo.nodes[no]["x"])

    return entregadores
