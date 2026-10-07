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
    "fert.confirm": (
        "These doses are general guidelines, not a prescription; confirm with your local KVK or agriculture officer.",
        "ఈ మోతాదులు సాధారణ మార్గదర్శకాలు మాత్రమే; స్థానిక KVK లేదా వ్యవసాయ అధికారిని సంప్రదించి నిర్ధారించుకోండి."),
}


def msg(code: str, level: str = "info", crop: str | None = None, **kw) -> dict:
    en, te = M[code]
    if crop:
        names = CROP_NAMES.get(crop, (crop, crop))
        return {"code": code, "level": level, "text": en.format(crop=names[0], **kw),
                "text_te": te.format(crop=names[1], **kw)}
    return {"code": code, "level": level, "text": en.format(**kw), "text_te": te.format(**kw)}
