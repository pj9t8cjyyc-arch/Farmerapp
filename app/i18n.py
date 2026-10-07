"""Bilingual (English + Telugu) message templates for server-generated advice.

Every message is returned as {"level", "text", "text_te"} so web, Android and iOS
clients can show Telugu, English or both without re-implementing the wording.
Telugu wording should be reviewed by a native speaker before release.
"""

CROP_NAMES = {  # key: (English, Telugu)
    "chilli": ("chilli", "మిర్చి"), "onion": ("onion", "ఉల్లి"), "tomato": ("tomato", "టమాటా"),
    "paddy": ("paddy", "వరి"), "wheat": ("wheat", "గోధుమ"), "cotton": ("cotton", "పత్తి"),
    "maize": ("maize", "మొక్కజొన్న"), "groundnut": ("groundnut", "వేరుశనగ"),
    "turmeric": ("turmeric", "పసుపు"),
}

M = {  # code: (English, Telugu)
    "sell.no_signal": (
        "Forecast move ({ch:+.1f}%) is smaller than the model's error (~{mape}%); no clear signal. Sell based on your cash needs.",
        "అంచనా మార్పు ({ch:+.1f}%) మోడల్ తప్పిదం (~{mape}%) కంటే తక్కువ; స్పష్టమైన సంకేతం లేదు. మీ డబ్బు అవసరాన్ని బట్టి అమ్మండి."),
    "sell.hold": (
        "Prices are expected to rise {ch:+.1f}% in {days} days. Consider holding stock if you have safe storage and no urgent cash need.",
        "{days} రోజుల్లో ధరలు {ch:+.1f}% పెరిగే అవకాశం ఉంది. సురక్షిత నిల్వ ఉండి, అత్యవసరంగా డబ్బు అవసరం లేకపోతే నిల్వ ఉంచడం పరిశీలించండి."),
    "sell.perishable": (
        "A rise of {ch:+.1f}% is expected, but {crop} is perishable; do not hold it for long.",
        "{ch:+.1f}% పెరుగుదల అంచనా, కానీ {crop} త్వరగా పాడయ్యే పంట; ఎక్కువ రోజులు నిల్వ ఉంచవద్దు."),
    "sell.fall": (
        "Prices are expected to fall {ch:+.1f}%. Consider selling sooner.",
        "ధరలు {ch:+.1f}% తగ్గే అవకాశం ఉంది. త్వరగా అమ్మడం పరిశీలించండి."),
    "sell.flat": (
        "Prices look roughly flat ({ch:+.1f}%).",
        "ధరలు దాదాపు స్థిరంగా ఉన్నాయి ({ch:+.1f}%)."),
    "sell.nofc": (
        "Forecast unavailable: at least 14 days of price history are needed.",
        "అంచనా అందుబాటులో లేదు: కనీసం 14 రోజుల ధరల చరిత్ర కావాలి."),
    "sell.below_cost": (
        "Market price (Rs {price:.0f}/quintal) is below your cost (Rs {cost:.0f}/quintal). Compare markets and consider MSP or storage.",
        "మార్కెట్ ధర (₹{price:.0f}/క్వింటాల్) మీ ఖర్చు (₹{cost:.0f}/క్వింటాల్) కంటే తక్కువ. మార్కెట్లను పోల్చండి; MSP లేదా నిల్వను పరిశీలించండి."),
    "sell.margin": (
        "The current price gives about {m:.0f}% margin over your cost.",
        "ప్రస్తుత ధర వల్ల మీ ఖర్చుపై సుమారు {m:.0f}% లాభం వస్తుంది."),
    "cost.none": (
        "Add expenses to get cost insights.",
        "ఖర్చుల సూచనల కోసం ఖర్చులు నమోదు చేయండి."),
    "cost.fert": (
        "Fertilizer is {p:.0f}% of your cost. Get a soil test and use the fertilizer calculator to avoid over-application.",
        "ఎరువుల ఖర్చు మీ మొత్తం ఖర్చులో {p:.0f}%. మట్టి పరీక్ష చేయించి, ఎరువుల కాలిక్యులేటర్ వాడి ఎక్కువగా వేయకుండా చూడండి."),
    "cost.pest": (
        "Pesticide is {p:.0f}% of your cost; spray only when field scouting shows a need (IPM).",
        "పురుగుమందుల ఖర్చు {p:.0f}%; పొలం పరిశీలనలో అవసరమైతేనే పిచికారీ చేయండి (IPM)."),
    "cost.labour": (
        "Labour is {p:.0f}% of your cost; check whether machines or group hiring can help.",
        "కూలీ ఖర్చు {p:.0f}%; యంత్రాలు లేదా గుంపుగా కూలీలను పెట్టుకోవడం సహాయపడుతుందేమో చూడండి."),
    "cost.ok": (
        "No single cost category looks unusually high.",
        "ఏ ఒక్క ఖర్చు విభాగం అసాధారణంగా ఎక్కువగా లేదు."),
    "fert.nosoil": (
        "No soil test given: using the standard dose. A soil test (about Rs 100-300 at a KVK or state lab) can cut fertilizer cost by skipping nutrients your soil already has.",
        "మట్టి పరీక్ష ఇవ్వలేదు: ప్రామాణిక మోతాదు వాడుతున్నాం. మట్టి పరీక్ష (KVK/ప్రభుత్వ ల్యాబ్‌లో సుమారు ₹100–300) చేయిస్తే మట్టిలో ఇప్పటికే ఉన్న పోషకాలు వేయకుండా ఎరువుల ఖర్చు తగ్గించవచ్చు."),
    "fert.acid": (
        "Soil is acidic (pH below 5.5): apply lime as locally recommended before fertilizer.",
        "మట్టి ఆమ్లంగా ఉంది (pH 5.5 కంటే తక్కువ): ఎరువుకు ముందు స్థానిక సిఫారసు ప్రకారం సున్నం వేయండి."),
    "fert.alk": (
        "Soil is alkaline (pH above 8.5): consider gypsum and organic matter.",
        "మట్టి క్షారంగా ఉంది (pH 8.5 కంటే ఎక్కువ): జిప్సం, సేంద్రియ ఎరువు వేయడం పరిశీలించండి."),
    "fert.split": (
        "Split nitrogen into 2-3 doses (basal, vegetative, flowering) to cut losses; add farmyard manure or compost.",
        "నత్రజనిని 2–3 దఫాలుగా (ప్రాథమిక, పెరుగుదల, పూత దశలో) వేయండి; పశువుల ఎరువు లేదా కంపోస్ట్ కలపండి."),
    "t.irrigate_now": (
        "Water your {crop} today. Soil water deficit is about {d} mm (limit {t} mm).",
        "{crop}కు ఈరోజు నీరు పెట్టండి. నేలలో నీటి లోటు సుమారు {d} మి.మీ (పరిమితి {t} మి.మీ)."),
    "t.irrigate_soon": (
        "Water your {crop} around {date} (in about {n} days).",
        "{crop}కు {date} నాటికి (సుమారు {n} రోజుల్లో) నీరు పెట్టండి."),
    "t.irrigate_ok": (
        "No watering needed now for {crop}: deficit {d} of {t} mm; next watering around {date}.",
        "{crop}కు ఇప్పుడు నీరు అవసరం లేదు: లోటు {d}/{t} మి.మీ; తదుపరి నీరు సుమారు {date}."),
    "t.irrigate_ok2": (
        "No watering needed now for {crop}: deficit {d} of {t} mm.",
        "{crop}కు ఇప్పుడు నీరు అవసరం లేదు: లోటు {d}/{t} మి.మీ."),
    "t.irrigate_fallback": (
        "Live weather is unavailable. {crop} was last watered {n} days ago; the usual gap is about {g} days.",
        "ప్రత్యక్ష వాతావరణం అందుబాటులో లేదు. {crop}కు చివరిగా {n} రోజుల క్రితం నీరు పెట్టారు; సాధారణ వ్యవధి సుమారు {g} రోజులు."),
    "t.irrigate_fallback_now": (
        "Live weather is unavailable. {crop} was last watered {n} days ago (usual gap about {g} days): check the soil and water if dry.",
        "ప్రత్యక్ష వాతావరణం అందుబాటులో లేదు. {crop}కు చివరిగా {n} రోజుల క్రితం నీరు పెట్టారు (సాధారణ వ్యవధి సుమారు {g} రోజులు): నేల చూసి ఎండి ఉంటే నీరు పెట్టండి."),
    "t.irrigate_never": (
        "No watering recorded yet for {crop}. Tap 'Watered' every time you irrigate so the advice stays accurate.",
        "{crop}కు ఇంకా నీరు పెట్టిన నమోదు లేదు. ప్రతిసారి నీరు పెట్టినప్పుడు 'నీరు పెట్టాను' నొక్కండి, అప్పుడు సలహా కచ్చితంగా ఉంటుంది."),
    "t.rainfed_dry": (
        "{crop} is rain-fed and the soil water deficit is {d} mm. If you have any water source, a protective watering will help.",
        "{crop} వర్షాధారం, నేలలో నీటి లోటు {d} మి.మీ. ఏదైనా నీటి వనరు ఉంటే రక్షణ నీరు ఇవ్వడం మంచిది."),
    "t.rainfed_ok": (
        "{crop} is rain-fed. Soil water deficit is {d} mm, which is fine for now.",
        "{crop} వర్షాధారం. నేలలో నీటి లోటు {d} మి.మీ, ప్రస్తుతానికి పర్వాలేదు."),
    "t.ponded": (
        "Keep 2-5 cm of water in the {crop} field now; drain it about {n} days before harvest.",
        "{crop} పొలంలో ఇప్పుడు 2-5 సెం.మీ. నీరు ఉంచండి; కోతకు సుమారు {n} రోజుల ముందు నీరు తీసేయండి."),
    "t.fert_due": (
        "Apply {label} on {crop} now ({window}): {products}.",
        "{crop}కు ఇప్పుడు {label} వేయండి ({window}): {products}."),
    "t.fert_soon": (
        "{label} for {crop} is coming up ({window}): {products}.",
        "{crop}కు {label} త్వరలో ({window}): {products}."),
    "t.fert_overdue": (
        "{label} for {crop} is overdue (was due {window}). If not done yet, apply now: {products}.",
        "{crop}కు {label} ఆలస్యమైంది ({window}). ఇంకా వేయకపోతే ఇప్పుడే వేయండి: {products}."),
    "t.fert_later": (
        "{label} for {crop} ({window}): {products}.",
        "{crop}కు {label} ({window}): {products}."),
    "t.harvest_soon": (
        "{crop} harvest window opens around {date}. Check market prices and arrange labour and transport.",
        "{crop} కోత సుమారు {date} నుంచి మొదలవుతుంది. మార్కెట్ ధరలు చూసి, కూలీలు, రవాణా ఏర్పాటు చేసుకోండి."),
    "t.harvest_now": (
        "{crop} is in its harvest window (from about {date}). Harvest when the crop is ready, then tap 'Harvested'.",
        "{crop} కోత సమయంలో ఉంది (సుమారు {date} నుంచి). పంట సిద్ధంగా ఉన్నప్పుడు కోయండి, తర్వాత 'కోశాను' నొక్కండి."),
    "t.stop_irrigation": (
        "Stop watering {crop} from about {date}, before harvest.",
        "కోతకు ముందు {crop}కు సుమారు {date} నుంచి నీరు ఆపండి."),
    "t.set_date": (
        "Set the planting date for {crop} to get your plan.",
        "ప్రణాళిక కోసం {crop} నాటిన తేదీ నమోదు చేయండి."),
    "a.rain": (
        "Heavy rain expected on {date} ({mm} mm). Avoid spraying and fertilizer that day and check drainage.",
        "{date}న భారీ వర్షం ({mm} మి.మీ) వచ్చే అవకాశం. ఆ రోజు మందులు, ఎరువులు వేయకండి; నీరు పోయే దారి చూడండి."),
    "a.heat": (
        "Very hot days ahead (up to {t}°C on {date}). Water in the early morning or evening and avoid spraying at midday.",
        "రాబోయే రోజుల్లో చాలా వేడి ({date}న {t}°C వరకు). ఉదయం లేదా సాయంత్రం నీరు పెట్టండి; మధ్యాహ్నం మందు కొట్టకండి."),
    "a.noweather": (
        "Live weather is not available right now, so watering advice uses standard gaps.",
        "ప్రత్యక్ష వాతావరణం ఇప్పుడు అందుబాటులో లేదు, కాబట్టి నీటి సలహా సాధారణ వ్యవధుల ఆధారంగా ఉంది."),
    "a.noloc": (
        "Add your location to get live weather and exact watering advice.",
        "ప్రత్యక్ష వాతావరణం, కచ్చితమైన నీటి సలహా కోసం మీ ప్రాంతం నమోదు చేయండి."),
    "fert.confirm": (
        "These doses are general guidelines, not a prescription; confirm with your local KVK or agriculture officer.",
        "ఈ మోతాదులు సాధారణ మార్గదర్శకాలు మాత్రమే; స్థానిక KVK లేదా వ్యవసాయ అధికారిని సంప్రదించి నిర్ధారించుకోండి."),
}


def msg(code: str, level: str = "info", crop: str | None = None, **kw) -> dict:
    """Render a bilingual message. A keyword value may be an (English, Telugu) tuple for text that differs by language."""
    en, te = M[code]
    kw_en = {k: (v[0] if isinstance(v, tuple) else v) for k, v in kw.items()}
    kw_te = {k: (v[1] if isinstance(v, tuple) else v) for k, v in kw.items()}
    if crop:
        names = CROP_NAMES.get(crop, (crop, crop))
        kw_en["crop"], kw_te["crop"] = names
    return {"code": code, "level": level, "text": en.format(**kw_en), "text_te": te.format(**kw_te)}
