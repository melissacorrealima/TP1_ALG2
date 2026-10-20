
import math


BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
DECODE_MAP = {c: i for i, c in enumerate(BASE32)}

RAIO_TERRA_KM = 6371.0088


def encode(lat: float, lon: float, precision: int = 8) -> str:
    """Codifica coordenadas geográficas em Geohash Base32."""
    min_lat, max_lat = -90.0, 90.0
    min_lon, max_lon = -180.0, 180.0

    geohash = []
    bits = 0

    for i in range(precision * 5):
        if i % 2 == 0:
            mid = (min_lon + max_lon) / 2

            if lon >= mid:
                bits = (bits << 1) | 1
                min_lon = mid
            else:
                bits <<= 1
                max_lon = mid
        else:
            mid = (min_lat + max_lat) / 2

            if lat >= mid:
                bits = (bits << 1) | 1
                min_lat = mid
            else:
                bits <<= 1
                max_lat = mid

        if (i + 1) % 5 == 0:
            geohash.append(BASE32[bits])
            bits = 0

    return "".join(geohash)


def decode_bbox(geohash: str) -> tuple[float, float, float, float]:
    """Retorna os limites da célula Geohash."""
    min_lat, max_lat = -90.0, 90.0
    min_lon, max_lon = -180.0, 180.0

    even_bit = True

    for char in geohash.lower():
        val = DECODE_MAP[char]

        for shift in (4, 3, 2, 1, 0):
            bit = (val >> shift) & 1

            if even_bit:
                mid = (min_lon + max_lon) / 2.0

                if bit == 1:
                    min_lon = mid
                else:
                    max_lon = mid
            else:
                mid = (min_lat + max_lat) / 2.0

                if bit == 1:
                    min_lat = mid
                else:
                    max_lat = mid

            even_bit = not even_bit

    return min_lat, max_lat, min_lon, max_lon


def get_neighbors(geohash: str) -> list[str]:
    """Retorna a célula central e suas oito vizinhas."""
    min_lat, max_lat, min_lon, max_lon = decode_bbox(geohash)

    center_lat = (min_lat + max_lat) / 2.0
    center_lon = (min_lon + max_lon) / 2.0

    d_lat = max_lat - min_lat
    d_lon = max_lon - min_lon

    neighbors = []
    seen = set()

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            point_lat = max(
                -89.9,
                min(89.9, center_lat + dy * d_lat)
            )

            point_lon = (
                (center_lon + dx * d_lon + 180.0) % 360.0
            ) - 180.0

            gh = encode(
                point_lat,
                point_lon,
                precision=len(geohash)
            )

            if gh not in seen:
                seen.add(gh)
                neighbors.append(gh)

    return neighbors


def get_prefix_length(radius_km: float) -> int:
    """Seleciona a precisão do prefixo conforme o raio."""
    if radius_km <= 0.85:
        return 6

    if radius_km <= 5.0:
        return 5

    return 4


def celula_intersecta_circulo(
    geohash: str,
    lat_centro: float,
    lon_centro: float,
    raio_km: float,
) -> bool:
    """
    Verifica conservadoramente se uma célula pode
    intersectar o círculo de busca.

    Retorna False apenas quando um limite inferior
    de distância supera o raio.
    """
    lat_min, lat_max, lon_min, lon_max = decode_bbox(geohash)

    lat_proxima = max(
        lat_min,
        min(lat_centro, lat_max)
    )

    lon_proxima = max(
        lon_min,
        min(lon_centro, lon_max)
    )

    delta_lat = math.radians(
        abs(lat_proxima - lat_centro)
    )

    delta_lon = math.radians(
        abs(lon_proxima - lon_centro)
    )

    limite_lat = RAIO_TERRA_KM * delta_lat

    maior_lat_abs = max(
        abs(lat_min),
        abs(lat_max),
        abs(lat_centro)
    )

    fator_lon = max(
        0.0,
        math.cos(math.radians(maior_lat_abs))
    )

    limite_lon = (
        RAIO_TERRA_KM
        * fator_lon
        * 2
        * math.asin(
            min(1.0, math.sin(delta_lon / 2))
        )
    )

    distancia_minima = max(
        limite_lat,
        limite_lon
    )

    return distancia_minima <= raio_km


def get_cells_for_radius(
    lat: float,
    lon: float,
    radius_km: float,
    precision: int = 5,
) -> list[str]:
    """
    Recupera as células Geohash potencialmente
    intersectadas pelo círculo de busca.

    Primeiro percorre o retângulo delimitador e,
    depois, descarta células comprovadamente fora
    do raio.

    Implementação voltada a buscas locais, sem
    cruzamento do antimeridiano.
    """
    if not math.isfinite(radius_km) or radius_km < 0:
        raise ValueError("O raio deve ser finito e não negativo.")

    if not (
        math.isfinite(lat)
        and math.isfinite(lon)
        and -90 <= lat <= 90
        and -180 <= lon <= 180
    ):
        raise ValueError("Coordenadas inválidas.")

    if not 1 <= precision <= 8:
        raise ValueError(
            "A precisão deve estar entre 1 e 8."
        )

    # Calcula os limites aproximados do círculo.
    delta_lat = math.degrees(
        radius_km / RAIO_TERRA_KM
    )

    cos_lat = math.cos(math.radians(lat))

    if abs(cos_lat) < 1e-12:
        delta_lon = 180.0
    else:
        delta_lon = math.degrees(
            radius_km
            / (RAIO_TERRA_KM * abs(cos_lat))
        )

    # Margem conservadora para buscas locais.
    delta_lat *= 1.01
    delta_lon *= 1.01

    lat_min = max(-90.0, lat - delta_lat)
    lat_max = min(90.0, lat + delta_lat)

    lon_min = lon - delta_lon
    lon_max = lon + delta_lon

    if (
        delta_lon >= 180
        or lon_min < -180
        or lon_max > 180
    ):
        raise ValueError(
            "Região fora dos limites suportados."
        )

    # Obtém as dimensões de uma célula Geohash.
    gh_central = encode(
        lat,
        lon,
        precision=precision
    )

    (
        cel_lat_min,
        cel_lat_max,
        cel_lon_min,
        cel_lon_max,
    ) = decode_bbox(gh_central)

    altura = cel_lat_max - cel_lat_min
    largura = cel_lon_max - cel_lon_min

    # Índices das células na grade global.
    indice_lat_inicio = math.floor(
        (lat_min + 90.0) / altura
    )

    indice_lat_fim = math.floor(
        (lat_max + 90.0) / altura
    )

    indice_lon_inicio = math.floor(
        (lon_min + 180.0) / largura
    )

    indice_lon_fim = math.floor(
        (lon_max + 180.0) / largura
    )

    celulas = set()

    # Laços finitos usando índices inteiros.
    for i in range(
        indice_lat_inicio,
        indice_lat_fim + 1
    ):
        centro_lat = (
            -90.0 + (i + 0.5) * altura
        )

        for j in range(
            indice_lon_inicio,
            indice_lon_fim + 1
        ):
            centro_lon = (
                -180.0 + (j + 0.5) * largura
            )

            celula = encode(
                centro_lat,
                centro_lon,
                precision=precision
            )

            if celula_intersecta_circulo(
                celula,
                lat,
                lon,
                radius_km
            ):
                celulas.add(celula)

    return sorted(celulas)
