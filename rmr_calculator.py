from dataclasses import dataclass
from typing import Optional, Dict

# Common physical activity multipliers (PAL)
ACTIVITY_LEVELS: Dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9
}

@dataclass
class Person:
    weight_kg: float
    height_cm: float
    age_years: int
    sex: str  # 'male' or 'female'
    body_fat_pct: Optional[float] = None
    lbm_kg: Optional[float] = None

def mifflin_st_jeor(p: Person) -> float:
    base = 10*p.weight_kg + 6.25*p.height_cm - 5*p.age_years
    return base + (5 if p.sex.lower() == "male" else -161)

def harris_benedict_revised(p: Person) -> float:
    if p.sex.lower() == "male":
        return 88.36 + 13.4*p.weight_kg + 4.8*p.height_cm - 5.7*p.age_years
    else:
        return 447.6 + 9.2*p.weight_kg + 3.1*p.height_cm - 4.3*p.age_years

def _calc_lbm(p: Person) -> Optional[float]:
    if p.lbm_kg is not None:
        return p.lbm_kg
    if p.body_fat_pct is not None:
        return p.weight_kg * (1 - p.body_fat_pct/100.0)
    return None

def katch_mcardle(p: Person) -> Optional[float]:
    lbm = _calc_lbm(p)
    if lbm is None:
        return None
    return 370 + 21.6 * lbm

def cunningham(p: Person) -> Optional[float]:
    lbm = _calc_lbm(p)
    if lbm is None:
        return None
    return 500 + 22 * lbm

def rmr_compare(p: Person) -> Dict[str, Optional[float]]:
    return {
        "Mifflin_St_Jeor": round(mifflin_st_jeor(p), 1),
        "Harris_Benedict_Revised": round(harris_benedict_revised(p), 1),
        "Katch_McArdle": round(katch_mcardle(p), 1) if katch_mcardle(p) is not None else None,
        "Cunningham": round(cunningham(p), 1) if cunningham(p) is not None else None,
    }

def tdee_from_rmr(rmr_kcal: float, activity_level: str = "moderate",
                  include_tef: bool = False, tef_pct: float = 0.10) -> float:
    pal = ACTIVITY_LEVELS.get(activity_level, 1.55)
    tdee = rmr_kcal * pal
    if include_tef:
        tdee *= (1.0 + tef_pct)
    return round(tdee, 1)

def estimate_tdee(p: Person, method: str = "Mifflin_St_Jeor",
                  activity_level: str = "moderate",
                  include_tef: bool = False, tef_pct: float = 0.10) -> Optional[float]:
    rmr_map = rmr_compare(p)
    rmr = rmr_map.get(method)
    if rmr is None:
        return None
    return tdee_from_rmr(rmr, activity_level=activity_level, include_tef=include_tef, tef_pct=tef_pct)