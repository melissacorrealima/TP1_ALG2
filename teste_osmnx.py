
from src.carregar_restaurantes import carregar_restaurantes_geocodificados
from src.gerador_de_frota import gerar_frota
from src.geohash import encode

restaurantes = carregar_restaurantes_geocodificados()

frota = gerar_frota(
    quantidade=10,
    restaurantes=restaurantes,
    corrigir_para_ruas=True,
    seed=42,
)

assert len(frota) == 10

ids = [e["id"] for e in frota]
assert len(ids) == len(set(ids))

for e in frota:
    assert -90 <= e["lat"] <= 90
    assert -180 <= e["lon"] <= 180
    assert e["geohash"] == encode(e["lat"], e["lon"], precision=8)

print("Quantidade:", len(frota))
print("IDs únicos:", len(set(ids)))
print("Geohashes: OK")
print("Projeção OSMnx executada com sucesso!")
