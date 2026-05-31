import json
import os
import requests
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from jwt.algorithms import RSAAlgorithm

TENANT_ID = os.environ["AZURE_TENANT_ID"]
JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Cache up to 1 keyset, refreshed every 24 hours
# Type annotation: keys are hashkey tuples, values are the JWKS list (list[dict])
_jwks_cache: TTLCache[tuple, list[dict]] = TTLCache(maxsize=1, ttl=86400)


@cached(cache=_jwks_cache, key=lambda: hashkey("jwks"))
def _fetch_jwks() -> list[dict]:
    response = requests.get(JWKS_URI, timeout=10)
    response.raise_for_status()
    return response.json()["keys"]


def get_public_key(kid: str):
    """Return the RSA public key matching the given key ID."""
    keys = _fetch_jwks()
    match = next((k for k in keys if k["kid"] == kid), None)

    if match is None:
        # kid not found — Azure may have rotated keys, so bust the cache and retry once
        _jwks_cache.clear()
        keys = _fetch_jwks()
        match = next((k for k in keys if k["kid"] == kid), None)

    if match is None:
        raise ValueError(f"No public key found for kid: {kid}")

    return RSAAlgorithm.from_jwk(json.dumps(match))
