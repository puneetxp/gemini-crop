"""
Deterministic agro-chemical safety check for AI advice (diagnosis, crop plans).

Gemini may suggest a pesticide; before a farmer sees it this module:
  1. removes any suggestion naming an active ingredient that is banned or
     phased out for agricultural use in India (Insecticides Act, 1968 orders,
     incl. the 2018 ban of 18 actives and earlier bans), and
  2. strips model-invented doses, telling the farmer to follow the CIBRC
     label or their KVK / agriculture officer instead,
  3. keeps organic and cultural (IPM) options first.

This is a guardrail, not a registration database: an active that passes is
not thereby approved for that crop. The list is small on purpose and easy to
extend; states can add their own restrictions.
"""

import re
from typing import Any, Dict, List, Tuple

# Banned / phased out for use in agriculture in India. Lower-case, matched as whole words.
BANNED_ACTIVES = {
    # 2018 order (12 banned from Aug 2018, 6 more from Dec 2020)
    "benomyl", "carbaryl", "diazinon", "fenarimol", "fenthion", "linuron",
    "methoxy ethyl mercury chloride", "methyl parathion", "sodium cyanide", "thiometon",
    "tridemorph", "trifluralin", "alachlor", "dichlorvos", "phorate", "phosphamidon",
    "triazophos", "trichlorfon",
    # Earlier bans
    "endosulfan", "aldrin", "dieldrin", "chlordane", "heptachlor", "lindane", "ddt",
    "toxaphene", "ethyl parathion", "parathion", "pentachlorophenol", "nitrofen",
    "ethylene dibromide", "calcium cyanide", "copper acetoarsenite", "menazon",
    "paraquat dimethyl sulphate", "pentachloronitrobenzene", "tetradifon",
}

# Not banned outright but not allowed on vegetables
NOT_ON_VEGETABLES = {"monocrotophos"}
VEGETABLES = {
    "tomato", "brinjal", "eggplant", "chilli", "chili", "okra", "bhindi", "cabbage", "cauliflower",
    "potato", "onion", "cucumber", "gourd", "spinach", "capsicum", "pea", "beans",
}

# A dose is an amount per something ("2.5 g/L", "@ 1 kg per acre"); a strength like "75% WP" stays
_DOSE = re.compile(
    r"@?\s*\d+(\.\d+)?\s*(ml|g|gm|gram|grams|kg|l|litre|liter|ppm)\s*(/|per)\s*[a-z]+\b(\s+of\s+water)?|@\s*\d+(\.\d+)?\s*\S*",
    re.IGNORECASE,
)

LABEL_NOTE = "Use only as per the CIBRC-approved label for this crop; ask your KVK or agriculture officer for the dose."


def _names_in(text: str, names: set) -> List[str]:
    low = text.lower()
    return [n for n in names if re.search(rf"\b{re.escape(n)}\b", low)]


def check_chemicals(items: List[Any], crop_name: str = "") -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Filter chemical suggestions. Returns (kept suggestions without doses, removed with reasons).
    """
    is_veg = any(v in (crop_name or "").lower() for v in VEGETABLES)
    kept: List[str] = []
    removed: List[Dict[str, str]] = []
    for item in items or []:
        text = str(item).strip()
        if not text:
            continue
        banned = _names_in(text, BANNED_ACTIVES)
        if banned:
            removed.append({"suggestion": text, "reason": f"{', '.join(banned)} is banned for agricultural use in India"})
            continue
        if is_veg and _names_in(text, NOT_ON_VEGETABLES):
            removed.append({"suggestion": text, "reason": "monocrotophos is not allowed on vegetables in India"})
            continue
        kept.append(re.sub(r"\s{2,}", " ", _DOSE.sub("", text)).replace("()", "").strip(" ,;-@"))
    return [k for k in kept if k], removed


def apply_to_diagnosis(diagnosis: Dict[str, Any], crop_name: str = "") -> Dict[str, Any]:
    """Run the check on a diagnosis dict in place and add a 'safety' block."""
    treatment = diagnosis.get("treatment") if isinstance(diagnosis.get("treatment"), dict) else {}
    kept, removed = check_chemicals(treatment.get("chemical") or [], crop_name)
    # IPM order: organic and cultural before chemical
    diagnosis["treatment"] = {
        "organic": [str(x) for x in treatment.get("organic") or []],
        "cultural": [str(x) for x in treatment.get("cultural") or []],
        "chemical": kept,
    }
    diagnosis["safety"] = {
        "checked": True,
        "removed": removed,
        "label_note": LABEL_NOTE if kept else "",
    }
    return diagnosis
