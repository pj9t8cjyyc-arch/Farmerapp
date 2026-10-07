"""District headquarters (approximate lat/lon, good enough for weather) for Telangana and Andhra Pradesh.
Farmers elsewhere can use 'use my location' (GPS) instead."""

DISTRICTS = {  # name: (state, lat, lon, Telugu name)
    "Hyderabad": ("Telangana", 17.39, 78.49, "హైదరాబాద్"), "Warangal": ("Telangana", 17.97, 79.59, "వరంగల్"),
    "Nizamabad": ("Telangana", 18.67, 78.09, "నిజామాబాద్"), "Karimnagar": ("Telangana", 18.44, 79.13, "కరీంనగర్"),
    "Khammam": ("Telangana", 17.25, 80.15, "ఖమ్మం"), "Adilabad": ("Telangana", 19.67, 78.53, "ఆదిలాబాద్"),
    "Mahabubnagar": ("Telangana", 16.74, 77.99, "మహబూబ్‌నగర్"), "Nalgonda": ("Telangana", 17.05, 79.27, "నల్గొండ"),
    "Medak": ("Telangana", 18.05, 78.26, "మెదక్"), "Siddipet": ("Telangana", 18.10, 78.85, "సిద్దిపేట"),
    "Sangareddy": ("Telangana", 17.62, 78.09, "సంగారెడ్డి"),
    "Guntur": ("Andhra Pradesh", 16.30, 80.44, "గుంటూరు"), "Krishna (Machilipatnam)": ("Andhra Pradesh", 16.19, 81.13, "కృష్ణా (మచిలీపట్నం)"),
    "Kurnool": ("Andhra Pradesh", 15.83, 78.04, "కర్నూలు"), "Anantapur": ("Andhra Pradesh", 14.68, 77.60, "అనంతపురం"),
    "Kadapa": ("Andhra Pradesh", 14.47, 78.82, "కడప"), "Chittoor": ("Andhra Pradesh", 13.22, 79.10, "చిత్తూరు"),
    "Nellore": ("Andhra Pradesh", 14.44, 79.99, "నెల్లూరు"), "Prakasam (Ongole)": ("Andhra Pradesh", 15.50, 80.05, "ప్రకాశం (ఒంగోలు)"),
    "Visakhapatnam": ("Andhra Pradesh", 17.69, 83.22, "విశాఖపట్నం"), "East Godavari (Kakinada)": ("Andhra Pradesh", 16.99, 82.25, "తూర్పు గోదావరి (కాకినాడ)"),
    "West Godavari (Eluru)": ("Andhra Pradesh", 16.71, 81.10, "పశ్చిమ గోదావరి (ఏలూరు)"), "Srikakulam": ("Andhra Pradesh", 18.30, 83.90, "శ్రీకాకుళం"),
    "Vizianagaram": ("Andhra Pradesh", 18.11, 83.40, "విజయనగరం"),
}


def listing() -> list[dict]:
    return [{"name": k, "state": v[0], "lat": v[1], "lon": v[2], "te": v[3]} for k, v in DISTRICTS.items()]
