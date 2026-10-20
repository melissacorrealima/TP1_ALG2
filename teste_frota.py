
from collections import Counter

from src.carregar_restaurantes import carregar_restaurantes_geocodificados
from src.gerador_de_frota import gerar_frota
from src.geohash import encode


restaurantes = carregar_restaurantes_geocodificados()

frota = gerar_frota(
    quantidade=250,
    restaurantes=restaurantes,
    corrigir_para_ruas=False,
    seed=42,
)

print("TESTES DA GERAÇÃO DA FROTA")

assert len(frota) == 250, "Quantidade incorreta"

ids = [e["id"] for e in frota]
assert len(ids) == len(set(ids)), "IDs duplicados"

for e in frota:
    assert -90 <= e["lat"] <= 90
    assert -180 <= e["lon"] <= 180

    assert e["geohash"] == encode(
        e["lat"], e["lon"], precision=8
    ), "Geohash incompatível com as coordenadas"

distribuicao = Counter(
    e["restaurante_centro"] for e in frota
)

assert max(distribuicao.values()) - min(distribuicao.values()) <= 1

frota_repetida = gerar_frota(
    quantidade=250,
    restaurantes=restaurantes,
    corrigir_para_ruas=False,
    seed=42,
)

assert frota == frota_repetida, "Semente não reproduz a frota"

print(f"Quantidade: {len(frota)}")
print(f"IDs únicos: {len(set(ids))}")
print(f"Distribuição: {dict(distribuicao)}")
print("Coordenadas: OK")
print("Geohashes: OK")
print("Reprodutibilidade: OK")
print("Todos os testes passaram!")
