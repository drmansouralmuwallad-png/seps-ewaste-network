"""Figure 2: facility map. Country outline from Natural Earth (1:110m, via geopandas 0.14);
site coordinates from GeoNames (via geonamescache). Writes figures/fig2_network_map.pdf."""
import json, os, warnings
warnings.filterwarnings("ignore")
import geopandas as gpd
import geonamescache
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.family": "DejaVu Sans"})

S1 = json.load(open("stage1.json"))
GN = {"Riyadh": "Riyadh", "Mecca": "Makkah", "Medina": "Madinah", "Dammam": "Dammam",
      "Tabuk": "Tabuk", "Abha": "Abha", "Buraidah": "Buraydah", "Hafar Al-Batin": "Hafar Al-Batin",
      "Sakakah": "Sakakah", "Jeddah": "Jeddah", "Al Kharj": "Al Kharj", "Yanbu": "Yanbu",
      "Turbarjal": "Ţubarjal", "Ad Dilam": "Ad Dilam", "Umm Lajj": "Umluj"}
cities = {c["name"]: (c["longitude"], c["latitude"])
          for c in geonamescache.GeonamesCache().get_cities().values() if c["countrycode"] == "SA"}
xy = {k: cities[v] for k, v in GN.items()}
# Al Qunfudhah is not in geonamescache (cities above its population cut-off); coordinates
# from GeoNames id 108896 (populated place), 19.12639 N, 41.07889 E.
xy["Al Qunfudhah"] = (41.07889, 19.12639)

world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
ksa = world[world.name == "Saudi Arabia"]
fig, ax = plt.subplots(figsize=(6.4, 5.4))
world.plot(ax=ax, color="#f2f2f2", edgecolor="#bbbbbb", lw=0.5)
ksa.plot(ax=ax, color="#e6edf3", edgecolor="#6b7c8f", lw=0.8)

def pts(names, **kw):
    for n in names:
        ax.scatter(*xy[n], zorder=4, **kw)
        kw.pop("label", None)

# collection -> segregation links (nearest segregation centre within 1,000 km)
dist = json.load(open("realdata.json"))
C = dist["cities"]; D = dist["dist"]
for cc in S1["collection"]:
    sc = min(S1["segregation"], key=lambda s: D[C.index(cc)][C.index(s)])
    ax.plot(*zip(xy[cc], xy[sc]), color="#2b6cb0", lw=0.8, alpha=0.6, zorder=2)

pts(S1["segregation"], s=150, marker="s", facecolor="none", edgecolor="#c05621", lw=1.8,
    label="Segregation centre (3)")
pts(["Turbarjal", "Ad Dilam", "Umm Lajj"], s=60, marker="^", color="#2f855a",
    edgecolor="white", lw=0.6, label="Recycling centre (3)")
pts(["Riyadh", "Jeddah", "Dammam"], s=60, marker="D", color="#6b46c1", edgecolor="white",
    lw=0.6, label="Refurbishing centre (3)")

for n in S1["collection"]:   # drawn last so co-located centres stay visible
    ax.scatter(*xy[n], s=30, marker="o", color="#2b6cb0", edgecolor="white", lw=0.6, zorder=6,
               label=f"Collection centre ({len(S1['collection'])})" if n == S1["collection"][0] else None)
label = set(S1["collection"]) | {"Jeddah", "Turbarjal", "Ad Dilam", "Umm Lajj"}
off = {"Riyadh": (-34, -11), "Dammam": (6, 4), "Hafar Al-Batin": (-30, 7), "Ad Dilam": (6, -9),
       "Mecca": (6, -9), "Jeddah": (-36, 2), "Umm Lajj": (-40, 0), "Turbarjal": (-46, 4),
       "Sakakah": (6, 2), "Medina": (6, 2)}
for n in label:
    ax.annotate(n, xy[n], textcoords="offset points", xytext=off.get(n, (6, 3)), fontsize=7,
                color="#222")
ax.set_xlim(34, 56.5); ax.set_ylim(15.5, 33)
ax.set_xlabel("Longitude (°E)", fontsize=8); ax.set_ylabel("Latitude (°N)", fontsize=8)
ax.tick_params(labelsize=7)
ax.legend(loc="lower left", fontsize=7, frameon=True, framealpha=0.95)
os.makedirs("figures", exist_ok=True)
fig.savefig("figures/fig2_network_map.pdf", bbox_inches="tight")
fig.savefig("figures/fig2_network_map.png", dpi=300, bbox_inches="tight")
print("fig2_network_map")
