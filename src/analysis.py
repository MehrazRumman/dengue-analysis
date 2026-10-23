"""Dengue in Bangladesh: hotspots over time, burden, deaths and climate links.

Run `python src/clean.py` first. Writes tables to reports/ and charts to figures/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
REP = ROOT / "reports"
FIG.mkdir(exist_ok=True)
REP.mkdir(exist_ok=True)

# Palette: validated reference instance (dataviz skill, references/palette.md), light mode.
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
CRITICAL = "#d03b3b"
SEQ_BLUE = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ_ORANGE = ["#fcfcfb", "#fde3d6", "#f8bfa4", "#f39a72", "#eb6834", "#c64f20", "#8f3713"]
CMAP_BLUE = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
CMAP_ORANGE = LinearSegmentedColormap.from_list("seq_orange", SEQ_ORANGE)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif", "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": AXIS, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
    "axes.titlesize": 11, "axes.titlelocation": "left", "axes.axisbelow": True,
})

DIVISION_ORDER = ["Dhaka", "Barishal", "Chattogram", "Khulna", "Rajshahi", "Mymensingh", "Rangpur", "Sylhet"]


def save(fig, name):
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def load():
    monthly = pd.read_csv(ROOT / "data/processed/monthly_division_2020_2025.csv", parse_dates=["date"])
    yearly_nat = pd.read_csv(ROOT / "data/external/national_yearly_2000_2026.csv")
    pop = pd.read_csv(ROOT / "data/external/division_population_2022.csv").set_index("division")["population_2022_adjusted"]
    snap = pd.read_csv(ROOT / "data/external/snapshot_2026_division.csv")
    return monthly, yearly_nat, pop, snap


# ---------------------------------------------------------------- tables

def division_year_table(monthly, pop):
    t = monthly.groupby(["division", "year"], as_index=False)[["cases", "deaths"]].sum()
    t["population"] = t.division.map(pop)
    t["incidence_per_100k"] = t.cases / t.population * 1e5
    t["deaths_per_million"] = t.deaths / t.population * 1e6
    t["cfr_pct"] = np.where(t.cases > 0, t.deaths / t.cases * 100, np.nan)

    nat = t.groupby("year")[["cases", "population"]].sum()
    nat_inc = nat.cases / nat.population * 1e5
    t["relative_risk"] = t.incidence_per_100k / t.year.map(nat_inc)
    t["hotspot_tier"] = pd.cut(t.relative_risk, [-np.inf, 0.75, 1.25, 1.75, np.inf],
                               labels=["low", "average", "elevated", "hotspot"])
    t["rank_in_year"] = t.groupby("year").incidence_per_100k.rank(ascending=False).astype(int)
    return t.round({"incidence_per_100k": 1, "deaths_per_million": 2, "cfr_pct": 3, "relative_risk": 2})


def division_overall_table(monthly, pop):
    t = monthly.groupby("division")[["cases", "deaths"]].sum()
    t["population"] = pop
    t["avg_annual_incidence_per_100k"] = t.cases / t.population * 1e5 / (monthly.date.nunique() / 12)
    t["cfr_pct"] = t.deaths / t.cases * 100
    t["share_of_cases_pct"] = t.cases / t.cases.sum() * 100
    t["share_of_deaths_pct"] = t.deaths / t.deaths.sum() * 100
    hot_months = (monthly.assign(inc=monthly.cases / monthly.division.map(pop) * 1e5)
                  .query("inc >= 10").groupby("division").size())
    t["months_over_10_per_100k"] = hot_months.reindex(t.index).fillna(0).astype(int)
    return t.sort_values("avg_annual_incidence_per_100k", ascending=False).round(2)


def seasonality_table(monthly):
    nat = monthly.groupby(["year", "month_num"])[["cases", "deaths"]].sum().reset_index()
    peaks = nat.loc[nat.groupby("year").cases.idxmax(), ["year", "month_num", "cases"]]
    peaks = peaks.rename(columns={"month_num": "peak_month", "cases": "peak_month_cases"})
    totals = nat.groupby("year").cases.sum()
    jul_nov = nat.query("7 <= month_num <= 11").groupby("year").cases.sum()
    peaks["share_jul_to_nov_pct"] = (peaks.year.map(jul_nov) / peaks.year.map(totals) * 100).round(1)
    return nat, peaks


def climate_lag_table(monthly):
    """Spearman correlation of a division's monthly cases with climate N months earlier."""
    rows = []
    for var in ["temperature_c", "humidity"]:
        for lag in range(0, 4):
            d = monthly.sort_values("date").copy()
            d["x"] = d.groupby("division")[var].shift(lag)
            d = d.dropna(subset=["x"])
            rows.append({"variable": var, "lag_months": lag,
                         # Spearman = Pearson on ranks (avoids a scipy dependency)
                         "spearman_r": round(d.cases.rank().corr(d.x.rank()), 3), "n": len(d)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- figures

def fig_national_trend(yn):
    yn = yn.copy()
    yn["cfr"] = yn.deaths / yn.cases * 100
    labels = [f"{y}*" if p != "full year" else str(y) for y, p in zip(yn.year, yn.period)]
    x = np.arange(len(yn))
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True, gridspec_kw={"hspace": 0.35})
    for ax, col, color, title, fmt in [
        (axes[0], "cases", BLUE, "Hospitalised dengue cases per year", "{:,.0f}"),
        (axes[1], "deaths", CRITICAL, "Dengue deaths per year", "{:,.0f}"),
        (axes[2], "cfr", INK2, "Case fatality rate (deaths per 100 hospitalised cases, %)", "{:.2f}%"),
    ]:
        ax.bar(x, yn[col], color=color, width=0.72)
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
        # Label the peaks plus the latest year; skip neighbours that would collide.
        top = set(yn[col].nlargest(2 if col != "cfr" else 3).index) | {yn.index[-1]}
        for i in sorted(top):
            ax.annotate(fmt.format(yn.loc[i, col]), (x[i], yn.loc[i, col]), ha="center", va="bottom",
                        fontsize=8, color=INK2, xytext=(0, 2), textcoords="offset points")
        ax.margins(y=0.15)
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    axes[2].set_xticks(x, labels, rotation=45, ha="right")
    fig.text(0.01, -0.02, "* 2026 is year to date (1 Jan - 21 Oct). Source: DGHS via Hossain et al. 2023 (2000-22), "
             "DGHS press releases (2023-26).", fontsize=8, color=MUTED)
    save(fig, "01_national_trend_2000_2026.png")


def heatmap(ax, mat, cmap, fmt, title, vmax=None):
    im = ax.imshow(mat.values, cmap=cmap, aspect="auto", vmin=0, vmax=vmax or np.nanmax(mat.values))
    ax.set_xticks(range(mat.shape[1]), mat.columns)
    ax.set_yticks(range(mat.shape[0]), mat.index)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    thresh = (vmax or np.nanmax(mat.values)) * 0.55
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.values[i, j]
            if np.isnan(v):
                continue
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=8.5,
                    color=SURFACE if v > thresh else INK)
    ax.set_title(title)
    return im


def fig_incidence_heatmap(dy):
    inc = dy.pivot(index="division", columns="year", values="incidence_per_100k").loc[DIVISION_ORDER]
    inc.columns = [f"{c}*" if c == 2025 else str(c) for c in inc.columns]
    rr = dy.pivot(index="division", columns="year", values="relative_risk").loc[DIVISION_ORDER]
    rr.columns = inc.columns
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"wspace": 0.3})
    im = heatmap(axes[0], inc, CMAP_BLUE, lambda v: f"{v:,.0f}", "Cases per 100,000 people")
    fig.colorbar(im, ax=axes[0], shrink=0.8).outline.set_visible(False)
    im = heatmap(axes[1], rr, CMAP_ORANGE, lambda v: f"{v:.1f}x",
                 "Relative risk vs national rate (>=1.75x = hotspot)", vmax=3.5)
    fig.colorbar(im, ax=axes[1], shrink=0.8).outline.set_visible(False)
    fig.text(0.01, -0.03, "* 2025 covers Jan-Oct only. Population: BBS Census 2022 (adjusted). "
             "Cases: Mendeley dataset doi:10.17632/cgwjshkx5k.2 (DGHS bulletins).", fontsize=8, color=MUTED)
    save(fig, "02_hotspot_heatmap_division_year.png")


def fig_seasonality(nat):
    mat = nat.pivot(index="year", columns="month_num", values="cases")
    mat.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig, ax = plt.subplots(figsize=(11, 3.8))
    im = heatmap(ax, mat, CMAP_BLUE, lambda v: f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}",
                 "National hospitalised cases by month - 85-95% of cases fall in Jul-Nov")
    fig.colorbar(im, ax=ax, shrink=0.85).outline.set_visible(False)
    save(fig, "03_seasonality_month_year.png")


def fig_small_multiples(monthly, pop):
    m = monthly.assign(inc=monthly.cases / monthly.division.map(pop) * 1e5)
    fig, axes = plt.subplots(2, 4, figsize=(14, 6), sharex=True, sharey=True)
    ymax = m.inc.max() * 1.1
    for ax, div in zip(axes.flat, DIVISION_ORDER):
        d = m[m.division == div]
        ax.fill_between(d.date, d.inc, color=BLUE, alpha=0.15, linewidth=0)
        ax.plot(d.date, d.inc, color=BLUE, linewidth=2)
        pk = d.loc[d.inc.idxmax()]
        ax.annotate(f"{pk.inc:.0f} ({pk.date:%b %y})", (pk.date, pk.inc), xytext=(4, 2),
                    textcoords="offset points", fontsize=8, color=INK2)
        ax.set_title(div, fontsize=10)
        ax.set_ylim(0, ymax)
        ax.grid(axis="x", visible=False)
        ax.tick_params(axis="x", labelrotation=0, labelsize=8)
    fig.supylabel("Monthly cases per 100,000", color=INK2, fontsize=10)
    fig.suptitle("Monthly incidence by division, Jan 2020 - Oct 2025 (shared scale)", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    save(fig, "04_division_monthly_incidence.png")


def fig_deaths(do):
    d = do.loc[DIVISION_ORDER[::-1]]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True, gridspec_kw={"wspace": 0.15})
    for ax, col, color, title, fmt in [
        (axes[0], "deaths", CRITICAL, "Deaths, 2020 - Oct 2025", "{:,.0f}"),
        (axes[1], "deaths_per_million", CRITICAL, "Deaths per million people", "{:.1f}"),
        (axes[2], "cfr_pct", INK2, "Case fatality rate (%)", "{:.2f}%"),
    ]:
        vals = d[col] if col != "deaths_per_million" else d.deaths / d.population * 1e6
        ax.barh(d.index, vals, color=color, height=0.65)
        for y, v in enumerate(vals):
            ax.text(v, y, " " + fmt.format(v), va="center", fontsize=8.5, color=INK2)
        ax.set_title(title)
        ax.grid(axis="y", visible=False)
        ax.margins(x=0.22)
    save(fig, "05_deaths_by_division.png")


def fig_dhaka_share(dy, yn):
    t = dy.groupby("year").apply(lambda g: g.loc[g.division != "Dhaka", "cases"].sum() / g.cases.sum() * 100,
                                 include_groups=False)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    labels = [f"{y}*" if y == 2025 else str(y) for y in t.index]
    ax.bar(labels, t.values, color=ORANGE, width=0.6)
    for i, v in enumerate(t.values):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9, color=INK2)
    ax.set_ylim(0, 100)
    ax.set_title("Share of cases from outside Dhaka division - dengue has spread nationwide")
    ax.grid(axis="x", visible=False)
    fig.text(0.01, -0.04, "* Jan-Oct 2025.", fontsize=8, color=MUTED)
    save(fig, "06_outside_dhaka_share.png")
    return t


def fig_climate(monthly, lags):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"wspace": 0.25})
    for ax, var, title in [(axes[0], "temperature_c", "Temperature"), (axes[1], "humidity", "Relative humidity")]:
        d = lags[lags.variable == var]
        ax.bar(d.lag_months.astype(str), d.spearman_r, color=BLUE, width=0.55)
        for i, v in enumerate(d.spearman_r):
            ax.text(i, v + 0.01 * np.sign(v), f"{v:.2f}", ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=9, color=INK2)
        ax.axhline(0, color=AXIS, linewidth=1)
        ax.set_ylim(-0.2, 0.8)
        ax.set_xlabel("Lag (months before case count)")
        ax.set_title(f"{title} vs cases (Spearman r)")
        ax.grid(axis="x", visible=False)
    save(fig, "07_climate_lag_correlation.png")


def fig_2026(snap):
    d = snap.dropna(subset=["deaths_ytd"]).copy()
    d["location"] = d.location.replace({"Dhaka South CC / Dhaka Medical College Hospital (as reported)": "DSCC / DMCH (as reported)",
                                        "Dhaka North City Corporation": "Dhaka North CC"})
    d = d.sort_values("deaths_ytd")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(d.location, d.deaths_ytd, color=CRITICAL, height=0.6)
    for y, v in enumerate(d.deaths_ytd):
        ax.text(v, y, f" {v:.0f}", va="center", fontsize=9, color=INK2)
    ax.set_title("2026 dengue deaths by reporting area (to 19 Oct 2026)")
    ax.grid(axis="y", visible=False)
    ax.margins(x=0.12)
    fig.text(0.01, -0.04, "Source: DGHS figures as reported by The Daily Star, 20 Oct 2026. Itemised areas sum to 328 of 352.",
             fontsize=8, color=MUTED)
    save(fig, "08_deaths_2026_by_area.png")


def main():
    monthly, yn, pop, snap = load()

    dy = division_year_table(monthly, pop)
    do = division_overall_table(monthly, pop)
    nat, peaks = seasonality_table(monthly)
    lags = climate_lag_table(monthly)
    yn_out = yn.assign(cfr_pct=(yn.deaths / yn.cases * 100).round(3))

    dy.to_csv(REP / "division_year_burden.csv", index=False)
    do.to_csv(REP / "division_overall_2020_2025.csv")
    peaks.to_csv(REP / "seasonal_peaks.csv", index=False)
    lags.to_csv(REP / "climate_lag_correlations.csv", index=False)
    yn_out.drop(columns="source").to_csv(REP / "national_yearly_with_cfr.csv", index=False)

    fig_national_trend(yn)
    fig_incidence_heatmap(dy)
    fig_seasonality(nat)
    fig_small_multiples(monthly, pop)
    fig_deaths(do)
    outside = fig_dhaka_share(dy, yn)
    fig_climate(monthly, lags)
    fig_2026(snap)

    pd.set_option("display.width", 200)
    print("== national\n", yn_out.drop(columns=["source", "period"]).to_string(index=False))
    print("== division overall\n", do.to_string())
    print("== hotspot tiers\n", dy.pivot(index="division", columns="year", values="hotspot_tier").loc[DIVISION_ORDER])
    print("== relative risk\n", dy.pivot(index="division", columns="year", values="relative_risk").loc[DIVISION_ORDER])
    print("== CFR by division-year\n", dy.pivot(index="division", columns="year", values="cfr_pct").loc[DIVISION_ORDER])
    print("== peaks\n", peaks.to_string(index=False))
    print("== outside Dhaka share\n", outside.round(1).to_string())
    print("== climate lags\n", lags.to_string(index=False))


if __name__ == "__main__":
    main()
