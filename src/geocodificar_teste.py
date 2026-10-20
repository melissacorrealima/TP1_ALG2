
from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_SAIDA = RAIZ / "data" / "bares_geocodificados.csv"

LIMITE = 100


def normalizar_endereco(endereco):
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
            return novo + endereco[len(antigo):]

    return endereco


def main():
    from src.carregar_restaurantes import carregar_restaurantes

    df = carregar_restaurantes()
    df = df[df["eh_restaurante"]].copy()

    if ARQUIVO_SAIDA.exists():
        cache = pd.read_csv(
            ARQUIVO_SAIDA,
            dtype={"_id": str},
        )
    else:
        cache = pd.DataFrame(
            columns=["_id", "endereco", "lat", "lon", "status"]
        )

    cache = cache.drop_duplicates(subset=["_id"], keep="last")

    if "status" not in cache.columns:
        cache["status"] = cache.apply(
            lambda r: "ok"
            if pd.notna(r["lat"]) and pd.notna(r["lon"])
            else "pendente",
            axis=1,
        )

    resultados = cache.to_dict("records")
    registrados = set(cache["_id"].astype(str))

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

    consultas = 0

    for _, row in df.iterrows():
        if consultas >= LIMITE:
            break

        identificador = str(row["_id"])

        if identificador in registrados:
            continue

        endereco = normalizar_endereco(row["endereco"])

        print(f"Consultando: {row['nome_exibicao']}")

        lat, lon = None, None
        status = "nao_encontrado"

        try:
            local = geocode(
                endereco,
                exactly_one=True,
                country_codes="br",
                timeout=15,
            )

            if local is not None:
                lat = float(local.latitude)
                lon = float(local.longitude)

                if -20.1 <= lat <= -19.7 and -44.2 <= lon <= -43.7:
                    status = "ok"
                    print(f"  Coordenadas: {lat}, {lon}")
                else:
                    lat, lon = None, None
                    status = "fora_da_regiao"
                    print("  Resultado fora da região de BH.")
            else:
                print("  Endereço não encontrado.")

        except Exception as erro:
            status = "erro"
            print(f"  Falha: {erro}")

        resultados.append({
            "_id": identificador,
            "endereco": row["endereco"],
            "lat": lat,
            "lon": lon,
            "status": status,
        })

        registrados.add(identificador)
        consultas += 1

        pd.DataFrame(resultados).to_csv(
            ARQUIVO_SAIDA,
            index=False,
        )

    resultado = pd.DataFrame(resultados)
    validos = resultado.dropna(subset=["lat", "lon"])

    print("\nGeocodificação concluída.")
    print(f"Novas consultas: {consultas}")
    print(f"Registros com coordenadas: {len(validos)}")
    print(f"Total de registros: {len(resultado)}")


if __name__ == "__main__":
    main()
