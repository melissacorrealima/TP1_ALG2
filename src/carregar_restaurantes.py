
from pathlib import Path

import pandas as pd


PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
CAMINHO_CSV = PASTA_DADOS / "bares.csv"
CAMINHO_GEO = PASTA_DADOS / "bares_geocodificados.csv"


def carregar_restaurantes():
    """Carrega e organiza os restaurantes do CSV."""

    df = pd.read_csv(CAMINHO_CSV)

    df = df.dropna(
        subset=["NOME_LOGRADOURO", "NOME_BAIRRO"]
    ).copy()

    for coluna in [
        "NOME_LOGRADOURO",
        "NOME_BAIRRO",
        "NOME",
        "NOME_FANTASIA",
    ]:
        df[coluna] = df[coluna].fillna("").astype(str).str.strip()

    df["eh_restaurante"] = (
        df["DESCRICAO_CNAE_PRINCIPAL"]
        .str.contains("RESTAURANTES", case=False, na=False)
    )

    df = df[df["eh_restaurante"]].copy()

    df["nome_exibicao"] = df["NOME_FANTASIA"].where(
        df["NOME_FANTASIA"] != "",
        df["NOME"],
    )

    df = df[df["nome_exibicao"] != ""]

    df["endereco"] = (
        df["DESC_LOGRADOURO"].fillna("").astype(str).str.strip()
        + " "
        + df["NOME_LOGRADOURO"]
        + ", "
        + df["NUMERO_IMOVEL"].fillna("").astype(str)
        + ", "
        + df["NOME_BAIRRO"]
        + ", Belo Horizonte, MG, Brasil"
    )

    return df


def carregar_restaurantes_geocodificados():
    """Retorna restaurantes com coordenadas válidas."""

    restaurantes = carregar_restaurantes()
    coordenadas = pd.read_csv(CAMINHO_GEO)

    coordenadas["lat"] = pd.to_numeric(
        coordenadas["lat"], errors="coerce"
    )
    coordenadas["lon"] = pd.to_numeric(
        coordenadas["lon"], errors="coerce"
    )

    coordenadas = coordenadas.dropna(subset=["lat", "lon"])
    coordenadas = coordenadas[
        coordenadas["lat"].between(-90, 90)
        & coordenadas["lon"].between(-180, 180)
    ]
    coordenadas = coordenadas.drop_duplicates(subset=["_id"])

    dados = restaurantes.merge(
        coordenadas[["_id", "lat", "lon"]],
        on="_id",
        how="inner",
    )

    dados = dados.drop_duplicates(subset=["_id"])

    return [
        {
            "id": int(row["_id"]),
            "name": row["nome_exibicao"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        }
        for _, row in dados.iterrows()
    ]
