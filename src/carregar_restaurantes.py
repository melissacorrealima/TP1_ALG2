
from pathlib import Path

import pandas as pd


CAMINHO_CSV = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "bares.csv"
)


def carregar_restaurantes():
    """Carrega e organiza os estabelecimentos do CSV."""

    df = pd.read_csv(CAMINHO_CSV)

    # Remove registros sem endereço ou bairro.
    df = df.dropna(
        subset=["NOME_LOGRADOURO", "NOME_BAIRRO"]
    ).copy()

    # Normaliza os campos textuais.
    for coluna in [
        "NOME_LOGRADOURO",
        "NOME_BAIRRO",
        "NOME",
        "NOME_FANTASIA",
    ]:
        df[coluna] = df[coluna].fillna("").astype(str).str.strip()

    # Usa o nome fantasia; se não existir, usa a razão social.
    df["nome_exibicao"] = df["NOME_FANTASIA"].where(
        df["NOME_FANTASIA"] != "",
        df["NOME"],
    )

    # Monta um endereço textual para futura geocodificação.
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

    # Prioriza estabelecimentos identificados como restaurantes.
    df["eh_restaurante"] = (
        df["DESCRICAO_CNAE_PRINCIPAL"]
        .str.contains("RESTAURANTES", case=False, na=False)
    )

    return df

def carregar_restaurantes_geocodificados():
    """Retorna os estabelecimentos com coordenadas válidas."""

    raiz = Path(__file__).resolve().parent.parent
    caminho_geo = raiz / "data" / "bares_geocodificados.csv"

    restaurantes = carregar_restaurantes()
    coordenadas = pd.read_csv(caminho_geo)

    coordenadas = coordenadas.dropna(subset=["lat", "lon"])
    coordenadas = coordenadas.drop_duplicates(subset=["_id"])

    dados = restaurantes.merge(
        coordenadas[["_id", "lat", "lon"]],
        on="_id",
        how="inner"
    )

    resultado = []

    for _, row in dados.iterrows():
        resultado.append({
            "id": int(row["_id"]),
            "name": row["nome_exibicao"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"])
        })

    return resultado