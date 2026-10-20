
import csv
import statistics
import time
from pathlib import Path

from src.carregar_restaurantes import carregar_restaurantes_geocodificados
from src.gerador_de_frota import gerar_frota
from src.trie_compacta import CompactTrie
from src.filtros_espaciais import haversine_km, filtrar_entregadores


TAMANHOS_FROTA = [100, 250, 500, 1000, 2000, 3000]
RAIOS_KM = [0.5, 1.0, 2.0, 5.0, 10.0]
REPETICOES = 30
SEED = 42

ARQUIVO_SAIDA = Path("resultados_benchmark.csv")


def construir_trie(frota):
    inicio = time.perf_counter()

    trie = CompactTrie()

    for entregador in frota:
        trie.insert(entregador["geohash"], entregador)

    tempo_ms = (time.perf_counter() - inicio) * 1000

    return trie, tempo_ms


def busca_exaustiva(frota, lat, lon, raio_km):
    encontrados = []

    for entregador in frota:
        distancia = haversine_km(
            lat,
            lon,
            entregador["lat"],
            entregador["lon"],
        )

        if distancia <= raio_km:
            encontrados.append(entregador["id"])

    return set(encontrados)


def medir_consulta(frota, trie, restaurante, raio_km):
    lat = restaurante["lat"]
    lon = restaurante["lon"]

    tempos_exaustiva = []
    tempos_trie = []

    ids_exaustiva = set()
    ids_trie = set()
    candidatos = 0

    # Aquecimento: evita medir apenas a primeira execução.
    busca_exaustiva(frota, lat, lon, raio_km)
    filtrar_entregadores(trie, lat, lon, radius_km=raio_km)

    for _ in range(REPETICOES):
        inicio = time.perf_counter()

        ids_exaustiva = busca_exaustiva(
            frota, lat, lon, raio_km
        )

        tempo_exaustiva = (
            time.perf_counter() - inicio
        ) * 1000

        resultado = filtrar_entregadores(
            trie,
            lat,
            lon,
            radius_km=raio_km,
        )

        ids_trie = {
            entregador["id"]
            for entregador in resultado["elegiveis"]
        }

        tempos_exaustiva.append(tempo_exaustiva)
        tempos_trie.append(resultado["tempo_ms"])

        candidatos = resultado["total_candidatos"]

    tempo_medio_exaustiva = statistics.mean(tempos_exaustiva)
    tempo_medio_trie = statistics.mean(tempos_trie)

    speedup = (
        tempo_medio_exaustiva / tempo_medio_trie
        if tempo_medio_trie > 0
        else None
    )

    return {
        "tempo_exaustiva_ms": tempo_medio_exaustiva,
        "tempo_trie_ms": tempo_medio_trie,
        "desvio_exaustiva_ms": statistics.stdev(tempos_exaustiva),
        "desvio_trie_ms": statistics.stdev(tempos_trie),
        "speedup": speedup,
        "total_exaustiva": len(ids_exaustiva),
        "total_trie": len(ids_trie),
        "total_candidatos": candidatos,
        "correto": ids_exaustiva == ids_trie,
    }


def executar_benchmark():
    restaurantes = carregar_restaurantes_geocodificados()

    if not restaurantes:
        print("Nenhum restaurante encontrado.")
        return

    resultados = []

    print("=" * 75)
    print("BENCHMARK - TRIE COMPACTA VS BUSCA EXAUSTIVA")
    print("=" * 75)
    print(f"Restaurantes: {len(restaurantes)}")
    print(f"Tamanhos de frota: {TAMANHOS_FROTA}")
    print(f"Raios: {RAIOS_KM}")
    print(f"Repetições por consulta: {REPETICOES}")
    print("=" * 75)

    for quantidade in TAMANHOS_FROTA:
        print(f"\nGerando frota com {quantidade} entregadores...")

        frota = gerar_frota(
            quantidade,
            restaurantes,
            corrigir_para_ruas=False,
            seed=SEED,
        )

        trie, tempo_construcao = construir_trie(frota)

        print(
            f"Trie construída em {tempo_construcao:.3f} ms"
        )

        for restaurante in restaurantes:
            for raio in RAIOS_KM:
                metricas = medir_consulta(
                    frota,
                    trie,
                    restaurante,
                    raio,
                )

                status = (
                    "OK" if metricas["correto"] else "FALHA"
                )

                speedup = metricas["speedup"]

                print(
                    f"Frota={quantidade:4d} | "
                    f"Raio={raio:4.1f} km | "
                    f"Trie={metricas['tempo_trie_ms']:.4f} ms | "
                    f"Exaustiva={metricas['tempo_exaustiva_ms']:.4f} ms | "
                    f"Status={status}"
                )

                resultados.append({
                    "frota": quantidade,
                    "restaurante_id": restaurante["id"],
                    "restaurante": restaurante["name"],
                    "raio_km": raio,
                    "repeticoes": REPETICOES,
                    "tempo_construcao_ms": round(
                        tempo_construcao, 6
                    ),
                    "tempo_trie_ms": round(
                        metricas["tempo_trie_ms"], 6
                    ),
                    "tempo_exaustiva_ms": round(
                        metricas["tempo_exaustiva_ms"], 6
                    ),
                    "desvio_trie_ms": round(
                        metricas["desvio_trie_ms"], 6
                    ),
                    "desvio_exaustiva_ms": round(
                        metricas["desvio_exaustiva_ms"], 6
                    ),
                    "speedup": (
                        round(speedup, 4)
                        if speedup is not None
                        else ""
                    ),
                    "total_candidatos": metricas["total_candidatos"],
                    "total_trie": metricas["total_trie"],
                    "total_exaustiva": metricas["total_exaustiva"],
                    "correto": metricas["correto"],
                })

    if resultados:
        with ARQUIVO_SAIDA.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=resultados[0].keys(),
            )
            escritor.writeheader()
            escritor.writerows(resultados)

    aprovados = sum(r["correto"] for r in resultados)
    reprovados = len(resultados) - aprovados

    print("\n" + "=" * 75)
    print("RESUMO DO BENCHMARK")
    print("=" * 75)
    print(f"Total de cenários: {len(resultados)}")
    print(f"Cenários corretos: {aprovados}")
    print(f"Cenários com falha: {reprovados}")
    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")

    if reprovados:
        print(
            "\nATENÇÃO: Algumas consultas da Trie "
            "não coincidiram com a busca exaustiva."
        )


if __name__ == "__main__":
    executar_benchmark()
