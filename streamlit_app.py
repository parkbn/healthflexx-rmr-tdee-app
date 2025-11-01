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
    
    ##height = st.number_input("Height (cm)", min_value=100, max_value=230, value=180, step=1)
# Height input with optional "in" conversion
height_input = st.text_input(
    "Height",
    value="180",
    help="Enter height in cm or inches (e.g., 70 in).",
)

# Detect if user included inches
if "in" in height_input.lower():
    try:
        height_val = float(height_input.lower().replace("in", "").strip())
        height = round(height_val * 2.54, 1)
        st.caption(f"Converted: {height_val:.1f} in = **{height:.1f} cm**")
    except ValueError:
        height = 180.0
        st.warning("Could not parse inches value — defaulted to 180 cm.")
else:
    try:
        height = float(height_input)
    except ValueError:
        height = 180.0
        st.warning("Please enter a numeric height (in cm or inches).")
    
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=85.0, step=0.5)
    bfp = st.number_input("Body fat % (optional)", min_value=0.0, max_value=80.0, value=18.0, step=0.5)
    use_bfp = st.checkbox("Use body fat %", value=True)

    # LBM: auto-calc when using BFP; manual entry otherwise
    if use_bfp:
        lbm_calc = weight * (1 - bfp / 100)  # auto calculated
        st.number_input(
            "Lean Body Mass (kg)",
            value=float(lbm_calc),
            help="LBM = body weight minus fat mass (auto-calculated). Used in Katch–McArdle and Cunningham equations.",
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

    ##st.info("**LBM (Lean Body Mass)** = body weight minus fat mass. Used in some equations like Katch–McArdle and Cunningham.")

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
