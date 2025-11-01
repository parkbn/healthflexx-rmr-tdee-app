import os, sys
import pandas as pd
import streamlit as st

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

import rmr_calculator as rc

st.set_page_config(page_title="RMR + TDEE Calculator", page_icon="🧮", layout="wide")

st.title("🧮 RMR + TDEE Calculator")
st.caption("Mifflin–St Jeor • Revised Harris–Benedict • Katch–McArdle • Cunningham")

with st.sidebar:
    st.header("Inputs")

    sex = st.selectbox("Sex", ["male", "female"], index=0)
    age = st.number_input("Age (years)", min_value=10, max_value=100, value=45, step=1)

    # --- Height input with flexible parsing ---
    height_raw = st.text_input(
        "Height",
        value="180",
        help="Enter cm (e.g., 180), inches (e.g., 70 in), or feet/inches (e.g., 5'11\").",
    )

    def parse_height_to_cm(s: str) -> float:
        s = (s or "").strip().lower()
        # feet/inches like 5'11" or 5 ft 11 in
        if "'" in s or "ft" in s:
            # normalize separators
            t = s.replace("ft", "'").replace("feet", "'").replace(" ", "")
            # split on '
            try:
                parts = t.split("'")
                ft = float(parts[0]) if parts[0] else 0.0
                inch_str = parts[1] if len(parts) > 1 else "0"
                inch = float(inch_str.replace('"', "").replace("in", "").strip() or 0)
                return round((ft * 12.0 + inch) * 2.54, 1)
            except Exception:
                return 180.0
        # explicit inches (e.g., "70 in", '70"', or 70in)
        if "in" in s or '"' in s:
            try:
                x = s.replace('"', "").replace("in", "").strip()
                return round(float(x) * 2.54, 1)
            except Exception:
                return 180.0
        # explicit centimeters
        if "cm" in s:
            try:
                return round(float(s.replace("cm", "").strip()), 1)
            except Exception:
                return 180.0
        # plain number: assume cm
        try:
            return round(float(s), 1)
        except Exception:
            return 180.0

    height = parse_height_to_cm(height_raw)
    # show the normalized cm so users see what the app is using
    st.caption(f"Using height: **{height:.1f} cm**")

    # --- Weight input with kg/lb parsing ---
weight_raw = st.text_input(
    "Weight",
    value="85",
    help="Enter weight in kg or lb (e.g., 85, 180 lb).",
)

def parse_weight_to_kg(s: str) -> float:
    s = (s or "").strip().lower()
    if "lb" in s or "lbs" in s or "pound" in s:
        try:
            x = float(s.replace("lbs", "").replace("lb", "").replace("pounds", "").strip())
            return round(x * 0.453592, 1)
        except Exception:
            return 85.0
    if "kg" in s:
        try:
            return round(float(s.replace("kg", "").strip()), 1)
        except Exception:
            return 85.0
    try:
        return round(float(s), 1)
    except Exception:
        return 85.0

weight = parse_weight_to_kg(weight_raw)
st.caption(f"Using weight: **{weight:.1f} kg**")

    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=85.0, step=0.5)
    bfp = st.number_input("Body fat % (optional)", min_value=0.0, max_value=80.0, value=18.0, step=0.5)
    use_bfp = st.checkbox("Use body fat %", value=True)

    # LBM: auto-calc when using BFP; manual entry otherwise
    if use_bfp:
        lbm_calc = weight * (1 - bfp / 100.0)
        st.number_input(
            "Lean Body Mass (kg)",
            value=float(round(lbm_calc, 1)),
            help="LBM = body weight minus fat mass (auto-calculated). Used in Katch–McArdle and Cunningham.",
            disabled=True,
        )
        lbm_value = float(lbm_calc)
    else:
        lbm_value = st.number_input(
            "Lean Body Mass (kg)",
            min_value=0.0,
            max_value=200.0,
            value=0.0,
            step=0.5,
            help="If you know your Lean Body Mass directly, enter it here.",
        )

    st.subheader("TDEE Settings")
    activity = st.selectbox(
        "Activity level (PAL)",
        list(rc.ACTIVITY_LEVELS.keys()),
        index=list(rc.ACTIVITY_LEVELS.keys()).index("moderate"),
    )
    method = st.selectbox(
        "RMR method for TDEE",
        ["Mifflin_St_Jeor", "Harris_Benedict_Revised", "Katch_McArdle", "Cunningham"],
        index=0,
    )
    include_tef = st.checkbox("Include TEF", value=False)
    tef_pct = st.slider("TEF %", 0.0, 30.0, 10.0, 1.0)


# -------- Build Person safely (no undefined vars) --------
kwargs = dict(weight_kg=weight, height_cm=height, age_years=int(age), sex=sex)
if use_bfp:
    # prefer body fat % path (Katch/Cunningham will compute LBM internally if needed)
    kwargs["body_fat_pct"] = float(bfp)
else:
    # only pass LBM if user actually provided > 0
    if lbm_value and lbm_value > 0:
        kwargs["lbm_kg"] = float(lbm_value)

p = rc.Person(**kwargs)

# -------- Compute RMR/TDEE --------
rmr_map = rc.rmr_compare(p)
df_rmr = pd.DataFrame([rmr_map])

tdee = rc.estimate_tdee(
    p,
    method=method,
    activity_level=activity,
    include_tef=include_tef,
    tef_pct=(tef_pct / 100.0),
)
st.metric("TDEE (kcal/day)", f"{tdee:.0f}" if tdee is not None else "—")
# Show how TDEE was computed
pal_val = rc.ACTIVITY_LEVELS.get(activity, 1.55)
tef_note = "TEF included" if include_tef else "no TEF"
pretty_method = method.replace("_", " ")

st.caption(
    f"Computed as RMR(**{pretty_method}**) × PAL(**{activity} ≈ {pal_val:.2f}**)"
    + (f" × (1 + {tef_pct/100:.2f} TEF)" if include_tef else "")
    + "."
)


col1, col2 = st.columns([2, 3])
with col1:
    st.subheader("RMR by Equation (kcal/day)")
    st.dataframe(df_rmr.style.format(precision=1))

with col2:
    st.subheader("Details")
    st.write(
        pd.DataFrame(
            [
                {
                    "Sex": sex,
                    "Age (y)": age,
                    "Height (cm)": height,
                    "Weight (kg)": weight,
                    "Body fat %": (bfp if use_bfp else None),
                    "LBM kg (override)": (None if use_bfp else lbm_value if lbm_value > 0 else None),
                    "Activity level": activity,
                    "Method for TDEE": method,
                    "Include TEF": include_tef,
                    "TEF %": tef_pct,
                }
            ]
        )
    )

st.divider()
st.header("📦 Batch CSV")
st.caption(
    "Upload a CSV and we’ll compute RMR and TDEE columns. Columns (case-insensitive): "
    "sex, age_years, height_cm, weight_kg, body_fat_pct (opt), lbm_kg (opt), activity_level (opt), method (opt), "
    "include_tef (True/False), tef_pct (0-1 or 0-100)."
)

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded is not None:
    df_in = pd.read_csv(uploaded)
    rows_out = []
    for _, row in df_in.iterrows():
        sex_row = str(row.get("sex") or row.get("Sex") or "").strip().lower()
        age_row = row.get("age_years") or row.get("age")
        height_row = row.get("height_cm")
        weight_row = row.get("weight_kg")
        bfp_row = row.get("body_fat_pct")
        lbm_row = row.get("lbm_kg")
        activity_level = str(row.get("activity_level") or "moderate").strip().lower()
        method_row = str(row.get("method") or "Mifflin_St_Jeor")
        include_tef_row = str(row.get("include_tef") or "False").strip().lower() in ["true", "1", "yes", "y"]
        tef_raw = row.get("tef_pct")
        try:
            tef_val = float(tef_raw)
            tef_val = tef_val / 100.0 if tef_val > 1 else tef_val
        except Exception:
            tef_val = 0.10

        p_kwargs = dict(
            weight_kg=float(weight_row),
            height_cm=float(height_row),
            age_years=int(round(float(age_row))),
            sex=sex_row,
        )
        try:
            if lbm_row is not None and not pd.isna(lbm_row) and float(lbm_row) > 0:
                p_kwargs["lbm_kg"] = float(lbm_row)
            elif bfp_row is not None and not pd.isna(bfp_row):
                bfp_val = float(bfp_row)
                if bfp_val <= 1.0:
                    bfp_val *= 100.0
                p_kwargs["body_fat_pct"] = bfp_val
        except Exception:
            pass

        person = rc.Person(**p_kwargs)
        rmr_map_row = rc.rmr_compare(person)
        tdee_row = rc.estimate_tdee(
            person, method=method_row, activity_level=activity_level, include_tef=include_tef_row, tef_pct=tef_val
        )

        rows_out.append(
            {
                **row.to_dict(),
                "RMR_Mifflin_St_Jeor": rmr_map_row.get("Mifflin_St_Jeor"),
                "RMR_Harris_Benedict_Revised": rmr_map_row.get("Harris_Benedict_Revised"),
                "RMR_Katch_McArdle": rmr_map_row.get("Katch_McArdle"),
                "RMR_Cunningham": rmr_map_row.get("Cunningham"),
                "TDEE_from_selected_method": tdee_row,
                "activity_level_used": activity_level,
                "method_used": method_row,
                "include_tef_used": include_tef_row,
                "tef_pct_used": tef_val,
            }
        )

    df_out = pd.DataFrame(rows_out)
    st.subheader("Results")
    st.dataframe(df_out.head(50))
    st.download_button(
        "Download results as CSV",
        df_out.to_csv(index=False).encode("utf-8"),
        "rmr_tdee_results.csv",
        "text/csv",
    )

st.sidebar.markdown("---")
st.sidebar.caption("Place `rmr_calculator.py` next to this file. Run with: `streamlit run streamlit_app.py`")
