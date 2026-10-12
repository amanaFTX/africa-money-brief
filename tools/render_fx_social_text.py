#!/usr/bin/env python3
"""Render the canonical long-form AMB FX Flagship social caption."""
import argparse
import datetime as dt
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS = {"Ghana": "🇬🇭", "Kenya": "🇰🇪", "South Africa": "🇿🇦", "Egypt": "🇪🇬"}
CURRENCY_NAMES = {"Ghana": "cedi", "Kenya": "shilling", "South Africa": "rand", "Egypt": "pound"}
UNITS = {"USD": "US$1", "GBP": "£1", "EUR": "€1"}


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(ROOT / "data/fx/latest.json"))
    p.add_argument("--output")
    return p.parse_args()


def date_label(value):
    return dt.date.fromisoformat(value).strftime("%-d %b")


def quote(low, high):
    return f"₦{low:,.0f}" if low == high else f"₦{low:,.0f}–{high:,.0f}"


def official_label(value):
    if value["official_basis"] == "CBN selling rate (NFEM)":
        return "CBN NFEM"
    if value["official_basis"].startswith("CBN"):
        return "CBN published selling"
    return "derived official"


def previous_edition(current_date):
    candidates = []
    for path in glob.glob(str(ROOT / "data/fx/2???-??-??.json")):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema") == "amb-fx-site/1" and data["date"] < current_date:
            candidates.append(data)
    return max(candidates, key=lambda x: x["date"]) if candidates else None


def movement_insights(data, prior):
    if not prior:
        return []
    out = []
    for market, current in data["markets"].items():
        old = prior.get("markets", {}).get(market)
        if not old or current["asof"] <= old["asof"]:
            continue
        moves = {c: (current["rates"][c] / old["rates"][c] - 1) * 100 for c in ("USD", "GBP", "EUR")}
        signs = {1 if v > 0 else -1 if v < 0 else 0 for v in moves.values()}
        largest = max(moves, key=lambda c: abs(moves[c]))
        if signs <= {0, 1}:
            direction = "weakened"
        elif signs <= {0, -1}:
            direction = "strengthened"
        else:
            direction = "was mixed"
        if direction == "was mixed":
            out.append(f"• {market}: moves were mixed; the largest was {largest} ({moves[largest]:+.2f}%).")
        else:
            out.append(
                f"• {market}: the {CURRENCY_NAMES[market]} {direction} across USD, GBP and EUR versus the "
                f"{date_label(old['asof'])} reference; the largest move was against {largest} ({abs(moves[largest]):.2f}%)."
            )
    return out


def render(data):
    edition = dt.date.fromisoformat(data["date"])
    lines = [
        "🌍 AFRICA MONEY BRIEF | FX FLAGSHIP",
        f"📅 {edition.strftime('%A, %-d %B %Y')}",
        "",
        "Africa’s latest official and parallel-market currency references across Nigeria, Ghana, Kenya, South Africa and Egypt. Each rate carries its effective date.",
        "",
    ]
    for code in ("USD", "GBP", "EUR"):
        v = data["nigeria"][code]
        buy_mid = (v["parallel_buy_low"] + v["parallel_buy_high"]) / 2
        sell_mid = (v["parallel_sell_low"] + v["parallel_sell_high"]) / 2
        amb_mid = (buy_mid + sell_mid) / 2
        lines += [
            f"{code} — Local currency per {UNITS[code]}",
            "",
            f"🇳🇬 Official: ₦{v['official_selling_rate']:,.2f} ({date_label(v['official_rate_date'])}; {official_label(v)})",
            f"🇳🇬 Parallel: Buy {quote(v['parallel_buy_low'], v['parallel_buy_high'])} | Sell {quote(v['parallel_sell_low'], v['parallel_sell_high'])}",
            f"📊 AMB midpoint: ₦{amb_mid:,.2f} | Parallel-buy premium: +{v['premium_pct']:.2f}%",
            "",
        ]
        for market, m in data["markets"].items():
            lines.append(f"{FLAGS[market]} {m['symbol']}{m['rates'][code]:,.4f} ({date_label(m['asof'])})")
        lines.append("")

    ranked = sorted(((data["nigeria"][c]["premium_pct"], c) for c in ("USD", "GBP", "EUR")), reverse=True)
    lines += [
        "📊 MARKET INSIGHT",
        "",
        "Nigeria’s indicative parallel-buy premiums against the latest CBN selling benchmarks:",
        "",
        *[f"• {code}: +{premium:.2f}%" for premium, code in ranked],
        "",
        f"{ranked[0][1]} carries the widest premium; {ranked[-1][1]} carries the narrowest.",
    ]
    moves = movement_insights(data, previous_edition(data["date"]))
    if moves:
        lines += ["", "Cross-market change since the previous Flagship:", "", *moves]
    freshness = "; ".join(f"{m} {date_label(v['asof'])}" for m, v in data["markets"].items())
    lines += [
        "",
        f"Official reference dates: {freshness}.",
        "",
        "SOURCES & METHODOLOGY",
        "",
        "Official rates: Latest available central-bank reference rates, with effective dates indicated.",
        "",
        "Nigeria parallel-market rates: Aggregated from multiple independent market sources.",
        "",
        "AMB midpoint: Average of the parallel buy-range and sell-range midpoints.",
        "",
        "Parallel-buy premium (%) = (parallel buying midpoint ÷ CBN selling rate − 1) × 100.",
        "",
        "Nigeria’s USD benchmark is the CBN NFEM rate; GBP and EUR use the CBN’s published selling rows for the same effective date.",
        "",
        "Rates are indicative and may vary by source, location, transaction size and time. Informational only — not FX advice.",
        "",
        "🔗 https://africamoneybrief.com/fx.html",
        "",
        "#AfricaMoneyBrief #FX #AfricanMarkets",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    opts = args()
    data = json.loads(Path(opts.input).read_text(encoding="utf-8"))
    text = render(data)
    output = Path(opts.output) if opts.output else ROOT / "assets/social" / f"AMB_FX_Flagship_{data['date']}.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(output)
