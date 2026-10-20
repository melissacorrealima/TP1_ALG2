
import time

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.carregar_restaurantes import carregar_restaurantes_geocodificados
from src.gerador_de_frota import gerar_frota
from src.trie_compacta import CompactTrie
from src.filtros_espaciais import buscar_candidatos, haversine_km
from src.geohash import encode, get_prefix_length


st.set_page_config(page_title="GeoEntrega BH", layout="wide")

st.markdown("""
<style>
    .stApp { background: #081D30; color: #E6F0F7; }
    [data-testid="stSidebar"] { background: #102B43; }
    [data-testid="stMetric"] {
        background: #102B43;
        border: 1px solid #24445C;
        padding: 12px;
        border-radius: 5px;
    }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar_restaurantes():
    return carregar_restaurantes_geocodificados()


@st.cache_resource
def criar_indice(frota):
    trie = CompactTrie()
    for id_, geohash, lat, lon in frota:
        trie.insert(geohash, {
            "id": id_, "geohash": geohash,
            "lat": lat, "lon": lon
        })
    return trie


@st.cache_data
def criar_mapa(frota, restaurante, raio, candidatos, elegiveis):
    lat, lon, nome = restaurante
    mapa = folium.Map(
        location=[lat, lon],
        zoom_start=13,
        tiles="OpenStreetMap",
        prefer_canvas=True
    )

    folium.Circle(
        [lat, lon], radius=raio * 1000,
        color="#66B8D9", fill=True, fill_opacity=0.1
    ).add_to(mapa)

    for id_, _, y, x in frota:
        cor = ("#20C997" if id_ in elegiveis else
               "#F2B34B" if id_ in candidatos else "#8B9CAB")

        folium.CircleMarker(
            [y, x], radius=4, color=cor,
            fill=True, fill_opacity=0.85,
            tooltip=f"Entregador {id_}"
        ).add_to(mapa)

    folium.Marker(
        [lat, lon], tooltip=nome,
        icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
    ).add_to(mapa)

    return mapa.get_root().render()


restaurantes = carregar_restaurantes()

if not restaurantes:
    st.error("Não foi possível carregar os restaurantes.")
    st.stop()

if "frota" not in st.session_state:
    st.session_state.frota = []

with st.sidebar:
    st.header("Parâmetros")
    st.subheader("Frota")

    quantidade = st.number_input(
        "Número de entregadores", 10, 3000, 250, step=10
    )
    ajustar_ruas = st.checkbox("Ajustar à malha viária")
    gerar = st.button("Gerar frota", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Consulta espacial")

    indice = st.selectbox(
        "Restaurante", range(len(restaurantes)),
        format_func=lambda i: restaurantes[i]["name"]
    )
    raio = st.slider("Raio de busca (km)", 0.25, 10.0, 2.0, 0.25)
    velocidade = st.slider("Velocidade média (km/h)", 8, 35, 20)

if gerar:
    with st.spinner("Gerando frota..."):
        st.session_state.frota = gerar_frota(
            quantidade=int(quantidade),
            restaurantes=restaurantes,
            corrigir_para_ruas=ajustar_ruas,
            seed=None
        )

st.title("GeoEntrega BH")
st.caption("Sistema de busca geoespacial de entregadores | Algoritmos II")
st.divider()

if not st.session_state.frota:
    st.info("Gere uma frota para iniciar a consulta.")
    st.stop()

frota = tuple(
    (e["id"], e["geohash"], e["lat"], e["lon"])
    for e in st.session_state.frota
)

restaurante = restaurantes[indice]
lat, lon = restaurante["lat"], restaurante["lon"]
trie = criar_indice(frota)

inicio = time.perf_counter()
candidatos = buscar_candidatos(trie, lat, lon, raio)

resultados = []
for e in candidatos:
    distancia = haversine_km(lat, lon, e["lat"], e["lon"])
    if distancia <= raio:
        resultados.append({
            "ID": e["id"],
            "Distância (km)": distancia,
            "ETA (min)": distancia / velocidade * 60,
            "Latitude": e["lat"],
            "Longitude": e["lon"]
        })

tempo_ms = (time.perf_counter() - inicio) * 1000
resultados.sort(key=lambda e: e["Distância (km)"])

ids_candidatos = frozenset(e["id"] for e in candidatos)
ids_elegiveis = frozenset(e["ID"] for e in resultados)



# Compara a Trie com uma busca por força bruta
esperados = {}

for e in st.session_state.frota:
    distancia = haversine_km(lat, lon, e["lat"], e["lon"])

    if distancia <= raio:
        esperados[e["id"]] = distancia

encontrados = {
    e["ID"]: e["Distância (km)"]
    for e in resultados
}

faltantes = set(esperados) - set(encontrados)
extras = set(encontrados) - set(esperados)

distancias_corretas = all(
    abs(esperados[id_] - encontrados[id_]) < 1e-9
    for id_ in set(esperados) & set(encontrados)
)

if not faltantes and not extras and distancias_corretas:
    st.success(
        f"Consulta validada: {len(encontrados)} entregadores "
        "encontrados corretamente."
    )
else:
    st.error(
        f"Erro na consulta: {len(faltantes)} faltantes, "
        f"{len(extras)} indevidos. "
        f"Distâncias corretas: {distancias_corretas}"
    )


a, b, c, d = st.columns(4)
a.metric("Total da frota", len(frota))
b.metric("Candidatos", len(candidatos))
c.metric("Dentro do raio", len(resultados))
d.metric("Tempo da consulta", f"{tempo_ms:.2f} ms")

geohash = encode(lat, lon, precision=8)
st.caption(
    f"Restaurante: {restaurante['name']} | "
    f"Raio: {raio:g} km | Geohash: {geohash} | "
    f"Prefixo: {get_prefix_length(raio)} caracteres"
)

col_mapa, col_tabela = st.columns([1.6, 1], gap="large")

with col_mapa:
    st.subheader("Distribuição espacial")

    html_mapa = criar_mapa(
        frota, (lat, lon, restaurante["name"]),
        raio, ids_candidatos, ids_elegiveis
    )
    components.html(html_mapa, height=550)

    st.caption(
        "🟢 Dentro do raio  |  🟠 Candidato fora do raio  "
        "|  ⚪ Não recuperado"
    )

with col_tabela:
    st.subheader("Resultado da consulta")
    st.caption(f"{len(resultados)} entregadores elegíveis.")

    tabela = pd.DataFrame(resultados, columns=[
        "ID", "Distância (km)", "ETA (min)", "Latitude", "Longitude"
    ])

    st.dataframe(
        tabela.round(3),
        hide_index=True,
        use_container_width=True,
        height=450
    )

    st.download_button(
        "Exportar CSV",
        tabela.to_csv(index=False).encode("utf-8-sig"),
        "entregadores.csv",
        "text/csv",
        use_container_width=True
    )
