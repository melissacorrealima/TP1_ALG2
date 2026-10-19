BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
DECODE_MAP = {c: i for i, c in enumerate(BASE32)}

def encode(lat: float, lon: float, precision: int = 8) -> str:
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
    min_lat, max_lat, min_lon, max_lon = decode_bbox(geohash)

    center_lat = (min_lat + max_lat) / 2.0
    center_lon = (min_lon + max_lon) / 2.0
    d_lat = max_lat - min_lat
    d_lon = max_lon - min_lon

    neighbors = []
    seen = set()

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            point_lat = max(-89.9, min(89.9, center_lat + dy * d_lat))
            point_lon = ((center_lon + dx * d_lon + 180.0) % 360.0) - 180.0
            gh = encode(point_lat, point_lon, precision=len(geohash))
            if gh not in seen:
                seen.add(gh)
                neighbors.append(gh)

    return neighbors

def get_prefix_length(radius_km: float) -> int:
    if radius_km <= 0.85:
        return 6
    if radius_km <= 5.0:
        return 5
    return 4