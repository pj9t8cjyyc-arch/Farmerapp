"""Crop catalogue: Agmarknet commodity names, demo base prices (Rs/quintal) and
general NPK guidelines (kg/ha of N, P2O5, K2O).

NPK numbers are generic textbook-style guidelines for orientation only; the
advice engine tells the farmer to confirm with a soil test / local KVK.
"""

CROPS = {
    # key: (agmarknet commodity, demo base price, N, P2O5, K2O, storable)
    "chilli":    ("Dry Chillies", 15000, 120, 60, 60, True),
    "onion":     ("Onion",         1800, 100, 50, 50, True),
    "tomato":    ("Tomato",        2000, 120, 60, 60, False),
    "paddy":     ("Paddy(Dhan)(Common)", 2200, 120, 60, 40, True),
    "wheat":     ("Wheat",         2400, 120, 60, 40, True),
    "cotton":    ("Cotton",        7000, 120, 60, 60, True),
    "maize":     ("Maize",         2200, 120, 60, 40, True),
    "groundnut": ("Groundnut",     6000,  25, 50, 75, True),
    "turmeric":  ("Turmeric",     13000, 100, 60, 120, True),
}

CATEGORIES = ["seed", "fertilizer", "pesticide", "labour", "irrigation",
              "machinery", "transport", "other"]


def key(crop: str) -> str:
    return crop.strip().lower()


def valid(crop: str) -> bool:
    return key(crop) in CROPS
