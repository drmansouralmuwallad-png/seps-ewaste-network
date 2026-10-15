"""Write params_complete.json: every input the model uses, read from model.py and
stage1.json so the file cannot drift from the code."""
import json
import model as M
S1 = json.load(open("stage1.json"))
out = {
 "_README": "Complete input set. Run ./run_all.sh to regenerate every result.",
 "_provenance": {
  "official_data": ["node populations (Saudi Census 2022, population.json)",
                    "high-income regions (GASTAT HIES 2018)", "exchange rate"],
  "measured_data": ["road distances (Google Maps Distance Matrix API)"],
  "literature": ["learning rate"],
  "calibration_values_from_the_study_data": ["formal collection volume per period", "prices",
                          "operating costs (segregation, recycling, refurbishing)", "demands",
                          "fuel and vehicle parameters", "WC1", "recovery fractions",
                          "installation costs"],
  "modelling_choices": ["capacities", "collection-centre operating cost", "e_min", "mu",
                        "coverage radii", "processing cost (0) and yields (1)", "tolerance delta",
                        "solver gap and time limits"],
  "calibration_values_from_the_study_data_extra": ["share of refurbished output sold locally",
                        "recycling, refurbishing and disposal sites (recycling sites anchored to the nearest listed city)"],
  "public_sources": {"equity regions": "GASTAT Household Income and Expenditure Survey 2018",
                     "map": "Natural Earth 1:110m; GeoNames via geonamescache"}},
 "periods": M.T, "cities": M.CITIES,
 "stage1": {k: S1[k] for k in ("radius_km", "one_out_minimum", "collection", "segregation",
                               "high_income_regions", "high_income_regions_wide", "investment_kusd")},
 "recycling_centres_anchored_to": M.RC_ANCHOR, "refurbishing_centres": M.RF_NAMES,
 "disposal_site": M.CITIES[M.DUMP],
 "fuel_usd_per_litre": M.FP, "fuel_litre_per_km": M.FCR, "vehicle_tonnes": M.VC,
 "price_usd_per_tonne": {"recycled": M.PR, "refurbished_local": M.PL, "refurbished_intl": M.PI},
 "share_local": M.SHARE_LOCAL, "alpha_beta_gamma": [M.ALPHA, M.BETA, round(1 - M.ALPHA - M.BETA, 2)],
 "learning_rate": M.LR, "learning_exponent": M.B_LEARN, "WC1_tonnes_per_worker": M.WC1,
 "sar_per_usd": M.SAR_USD,
 "operating_cost_kusd_per_period": {"collection": M.FOC_CC, "segregation": M.FOC_SEG,
                                    "recycling": M.FOC_REC, "refurbishing": M.FOC_REF},
 "capacity_tonnes_per_period": {"collection": M.CAP_CC, "segregation": M.CAP_SC,
                                "recycling": M.CAP_RC, "refurbishing": M.CAP_RF},
 "min_throughput_fraction": M.MIN_UTIL, "e_min": M.E_MIN,
 "installation_cost_kusd": {"collection": 2000.0, "segregation": 4250.0},
 "demand_tonnes": {"local": M.DL, "intl": M.DI, "raw": M.DR},
 "generation_tonnes": M.EWASTE.tolist(), "distance_km": M.DIST.tolist(),
 "solver": f"HiGHS via PuLP, gapRel {M.SOLVE_GAP:g}, time limit {M.SOLVE_TLIM} s",
}
json.dump(out, open("params_complete.json", "w"), indent=1)
print("params_complete.json")
