def test_import_and_compute():
    import rmr_calculator as rc
    p = rc.Person(weight_kg=85, height_cm=180, age_years=45, sex="male", body_fat_pct=18)
    rmr_map = rc.rmr_compare(p)
    assert "Mifflin_St_Jeor" in rmr_map and rmr_map["Mifflin_St_Jeor"] > 0
    tdee = rc.estimate_tdee(p, method="Mifflin_St_Jeor", activity_level="moderate", include_tef=True, tef_pct=0.1)
    assert tdee is not None and tdee > rmr_map["Mifflin_St_Jeor"]