
import math
import time

from src.geohash import get_cells_for_radius, get_prefix_length

def haversine_km(lat1, lon1, lat2, lon2):
    """Calcula a distância em linha reta sobre a superfície terrestre."""
    raio_terra = 6371.0088

    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return 2 * raio_terra * math.asin(
        min(1.0, math.sqrt(a))
    )



def buscar_candidatos(trie, lat, lon, radius_km):
    """
    Recupera candidatos usando todas as células Geohash
    que intersectam o retângulo delimitador da busca.
    """
    precision = get_prefix_length(radius_km)

    celulas = get_cells_for_radius(
        lat,
        lon,
        radius_km,
        precision=precision,
    )

    candidatos = {}

    for celula in celulas:
        resultados = trie.search_prefix(celula)

        for entregador in resultados:
            identificador = entregador["id"]
            candidatos[identificador] = entregador

    return list(candidatos.values())


def filtrar_entregadores(
    trie,
    lat_restaurante,
    lon_restaurante,
    radius_km=2.0,
    velocidade_kmh=20.0,
):
    """
    Retorna candidatos, elegíveis, descartados e métricas da consulta.
    """
    inicio = time.perf_counter()

    candidatos = buscar_candidatos(
        trie,
        lat_restaurante,
        lon_restaurante,
        radius_km,
    )

    elegiveis = []
    descartados = []

    for entregador in candidatos:
        distancia = haversine_km(
            lat_restaurante,
            lon_restaurante,
            entregador["lat"],
            entregador["lon"],
        )

        resultado = {
            **entregador,
            "distancia_km": distancia,
            "eta_min": (
                distancia / velocidade_kmh * 60
                if velocidade_kmh > 0
                else None
            ),
        }

        if distancia <= radius_km:
            elegiveis.append(resultado)
        else:
            descartados.append(resultado)

    elegiveis.sort(key=lambda item: item["distancia_km"])

    tempo_ms = (time.perf_counter() - inicio) * 1000

    return {
        "candidatos": candidatos,
        "elegiveis": elegiveis,
        "descartados": descartados,
        "total_candidatos": len(candidatos),
        "total_elegiveis": len(elegiveis),
        "tempo_ms": tempo_ms,
    }
