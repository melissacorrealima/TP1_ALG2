
from pathlib import Path

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# Caminhos do projeto
RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_SAIDA = RAIZ / "data" / "bares_geocodificados.csv"


def normalizar_endereco(endereco):
    """Expande abreviações comuns usadas no CSV."""
    substituicoes = {
        "AVE ": "Avenida ",
        "RUA ": "Rua ",
        "ROD ": "Rodovia ",
        "ESTR ": "Estrada ",
        "ALAM ": "Alameda ",
        "PRACA ": "Praça ",
    }

    endereco = str(endereco).strip()

    for antigo, novo in substituicoes.items():
        if endereco.upper().startswith(antigo):
            endereco = novo + endereco[len(antigo):]
            break

    return endereco


def main():
    from src.carregar_restaurantes import carregar_restaurantes

    # Carrega os dados e seleciona os 10 primeiros restaurantes.
    df = carregar_restaurantes()
    df = df[df["eh_restaurante"]].head(10).copy()

    # Recupera os resultados anteriores, se existirem.
    if ARQUIVO_SAIDA.exists():
        cache = pd.read_csv(ARQUIVO_SAIDA)
    else:
        cache = pd.DataFrame(
            columns=["_id", "endereco", "lat", "lon"]
        )

    resultados = cache.to_dict("records")

    geolocator = Nominatim(
        user_agent="GeoEntregaBH_TP1_ALG2_estudo"
    )

    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1.1,
        max_retries=1,
        error_wait_seconds=2,
        swallow_exceptions=False,
    )

    for _, row in df.iterrows():
        identificador = str(row["_id"])

        # Procura um resultado anterior para este estabelecimento.
        registro_existente = next(
            (
                r for r in resultados
                if str(r["_id"]) == identificador
            ),
            None,
        )

        # Se já tem coordenadas, preserva e não consulta novamente.
        if registro_existente is not None:
            tem_lat = pd.notna(registro_existente.get("lat"))
            tem_lon = pd.notna(registro_existente.get("lon"))

            if tem_lat and tem_lon:
                print(f"Já geocodificado: {row['nome_exibicao']}")
                continue

            # Se não tinha coordenadas, permite uma nova tentativa.
            resultados.remove(registro_existente)

        endereco_original = row["endereco"]
        endereco_busca = normalizar_endereco(endereco_original)

        print(
            f"Consultando: {row['nome_exibicao']} "
            f"— {endereco_busca}"
        )

        lat, lon = None, None

        try:
            local = geocode(
                endereco_busca,
                exactly_one=True,
                country_codes="br",
                timeout=15,
            )

            if local is None:
                print("  Endereço não encontrado.")
            else:
                lat = float(local.latitude)
                lon = float(local.longitude)
                print(f"  Coordenadas: {lat}, {lon}")

        except Exception as erro:
            print(f"  Falha na consulta: {erro}")

        resultados.append({
            "_id": row["_id"],
            "endereco": endereco_original,
            "lat": lat,
            "lon": lon,
        })

        # Salva após cada endereço para preservar o progresso.
        pd.DataFrame(resultados).to_csv(
            ARQUIVO_SAIDA,
            index=False,
        )

    resultado_df = pd.DataFrame(resultados)
    validos = resultado_df.dropna(subset=["lat", "lon"])

    print("\nTeste concluído.")
    print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")
    print(f"Registros com coordenadas: {len(validos)}")
    print(f"Registros no arquivo: {len(resultado_df)}")


if __name__ == "__main__":
    main()
