# testes para incluir no relatório (runtime)

import csv
import time
from pathlib import Path

from src.carregar_restaurantes import carregar_restaurantes_geocodificados
from src.gerador_de_frota import gerar_frota
from src.trie_compacta import CompactTrie
from src.filtros_espaciais import haversine_km, filtrar_entregadores


# Configurações dos experimentos
QUANTIDADE_ENTREGADORES = 250
SEED = 42
RAIOS_KM = [0.5, 1.0, 2.0, 5.0, 10.0]
ARQUIVO_SAIDA = Path("resultados_validacao.csv")


def construir_trie(frota):
    """Insere os entregadores na Trie compacta."""
    trie = CompactTrie()

    for entregador in frota:
        trie.insert(entregador["geohash"], entregador)

    return trie


def busca_exaustiva(frota, lat, lon, raio_km):
    """Busca todos os entregadores dentro do raio, sem usar índice."""
    inicio = time.perf_counter()

    encontrados = []

    for entregador in frota:
        distancia = haversine_km(
            lat,
            lon,
            entregador["lat"],
            entregador["lon"],
        )

        if distancia <= raio_km:
            encontrados.append(entregador)

    tempo_ms = (time.perf_counter() - inicio) * 1000

    return encontrados, tempo_ms


def executar_validacao():
    restaurantes = carregar_restaurantes_geocodificados()

    if not restaurantes:
        print("Nenhum restaurante geocodificado encontrado.")
        return

    print("Gerando frota...")
    frota = gerar_frota(
        QUANTIDADE_ENTREGADORES,
        restaurantes,
        corrigir_para_ruas=False,
        seed=SEED,
    )

    print("Construindo Trie compacta...")
    trie = construir_trie(frota)

    resultados = []
    total_testes = 0
    testes_aprovados = 0
    testes_reprovados = 0

    print("\n" + "=" * 75)
    print("VALIDAÇÃO: TRIE COMPACTA VS BUSCA EXAUSTIVA")
    print("=" * 75)
    print(f"Restaurantes: {len(restaurantes)}")
    print(f"Entregadores: {len(frota)}")
    print(f"Raios (km): {RAIOS_KM}")
    print(f"Semente aleatória: {SEED}")
    print("=" * 75)

    for restaurante in restaurantes:
        lat = restaurante["lat"]
        lon = restaurante["lon"]
        nome = restaurante["name"]

        print(f"\nRestaurante: {nome}")

        for raio in RAIOS_KM:
            total_testes += 1

            # Busca exaustiva
            exaustivos, tempo_exaustiva = busca_exaustiva(
                frota, lat, lon, raio
            )

            # Busca indexada pela Trie
            resultado_trie = filtrar_entregadores(
                trie,
                lat,
                lon,
                radius_km=raio,
            )

            elegiveis_trie = resultado_trie["elegiveis"]

            # Compara identificadores, não apenas quantidades
            ids_exaustiva = {
                entregador["id"] for entregador in exaustivos
            }

            ids_trie = {
                entregador["id"] for entregador in elegiveis_trie
            }

            ids_ausentes = sorted(ids_exaustiva - ids_trie)
            ids_extras = sorted(ids_trie - ids_exaustiva)

            aprovado = ids_exaustiva == ids_trie

            if aprovado:
                testes_aprovados += 1
                status = "OK"
            else:
                testes_reprovados += 1
                status = "FALHA"

            tempo_trie = resultado_trie["tempo_ms"]

            print(
                f"  Raio: {raio:>4.1f} km | "
                f"Exaustiva: {len(ids_exaustiva):>3} | "
                f"Trie: {len(ids_trie):>3} | "
                f"Candidatos: {resultado_trie['total_candidatos']:>3} | "
                f"Status: {status}"
            )

            if not aprovado:
                print(f"    IDs ausentes: {ids_ausentes}")
                print(f"    IDs extras: {ids_extras}")

            resultados.append({
                "restaurante_id": restaurante["id"],
                "restaurante": nome,
                "raio_km": raio,
                "quantidade_frota": len(frota),
                "total_exaustiva": len(ids_exaustiva),
                "total_trie": len(ids_trie),
                "total_candidatos": resultado_trie["total_candidatos"],
                "ids_ausentes": str(ids_ausentes),
                "ids_extras": str(ids_extras),
                "tempo_exaustiva_ms": round(tempo_exaustiva, 6),
                "tempo_trie_ms": round(tempo_trie, 6),
                "aprovado": aprovado,
            })

    # Salvar resultados em CSV
    if resultados:
        with ARQUIVO_SAIDA.open(
            "w", newline="", encoding="utf-8-sig"
        ) as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=resultados[0].keys(),
            )
            escritor.writeheader()
            escritor.writerows(resultados)

    print("\n" + "=" * 75)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 75)
    print(f"Total de testes: {total_testes}")
    print(f"Testes aprovados: {testes_aprovados}")
    print(f"Testes reprovados: {testes_reprovados}")
    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")

    if testes_reprovados == 0:
        print("\nSUCESSO: Todos os cenários testados passaram!")
    else:
        print(
            "\nATENÇÃO: Foram encontradas divergências entre "
            "a Trie e a busca exaustiva."
        )
        print(
            "Verifique a cobertura das células Geohash "
            "nos cenários reprovados."
        )


if __name__ == "__main__":
    executar_validacao()
