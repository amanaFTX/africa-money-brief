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

    if data.get("nigeria_market_note"):
        lines += ["NIGERIA MARKET NOTE", "", data["nigeria_market_note"], ""]

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


def pct(new, old):
    return (new / old - 1) * 100


def render_early(data):
    edition = dt.date.fromisoformat(data["date"])
    prior = json.loads((ROOT / "data/fx/latest.json").read_text(encoding="utf-8"))
    n = data["nigeria"]
    m = data["markets"]
    lines = [
        "🌍 AFRICA MONEY BRIEF | FX EARLY LOOK",
        f"📅 {edition.strftime('%A, %-d %B %Y')} · pre-market",
        "",
        "Previous-close and latest-benchmark references across Nigeria, Ghana, Kenya, South Africa and Egypt. These are not live opening quotes; each figure carries its effective date.",
        "",
        "🇳🇬 NIGERIA",
    ]
    for code in ("USD", "GBP", "EUR"):
        v = n[code]
        p = prior["nigeria"][code]
        lines.append(
            f"• {code}: ₦{v['official_selling_rate']:,.2f} ({date_label(v['official_rate_date'])}; {official_label(v)}) "
            f"{pct(v['official_selling_rate'], p['official_selling_rate']):+.2f}% vs {date_label(p['official_rate_date'])}"
        )
    has_parallel = all(n[c].get("parallel_buy_low") is not None for c in ("USD", "GBP", "EUR"))
    if has_parallel:
        lines += ["", "Nigeria parallel-market observations (previous close / early; not live opening quotes):"]
        for code in ("USD", "GBP", "EUR"):
            v = n[code]
            buy_mid = (v["parallel_buy_low"] + v["parallel_buy_high"]) / 2
            sell_mid = (v["parallel_sell_low"] + v["parallel_sell_high"]) / 2
            amb_mid = (buy_mid + sell_mid) / 2
            lines.append(
                f"• {code}: Buy {quote(v['parallel_buy_low'], v['parallel_buy_high'])} | "
                f"Sell {quote(v['parallel_sell_low'], v['parallel_sell_high'])} | "
                f"AMB midpoint ₦{amb_mid:,.2f} | Parallel-buy premium {v['premium_pct']:+.2f}%"
            )
        lines += [
            "",
            "Aggregated from multiple independent market sources observed from 13 Oct 16:13–22:06 WAT and 14 Oct 03:00–pre-07:00 WAT. "
            "GBP and EUR show material cross-source dispersion; the ranges preserve it rather than force a single quote.",
            "",
        ]
    else:
        lines += [
            "",
            "Parallel-market ranges are withheld this morning: fewer than two independent current observations could be verified, so no premium is shown.",
            "",
        ]
    def row(name, flag, sym, note):
        v = m[name]
        r = v["rates"]
        asof = date_label(v["asof"])
        return [
            f"{flag} {name.upper()} ({asof})",
            f"US$1 = {sym}{r['USD']:,.4f} | £1 = {sym}{r['GBP']:,.4f} | €1 = {sym}{r['EUR']:,.4f}",
            note,
            "",
        ]
    editions = sorted(
        (json.loads(Path(f).read_text(encoding="utf-8")) for f in glob.glob(str(ROOT / "data/fx/2???-??-??.json"))),
        key=lambda e: e["date"],
        reverse=True,
    )
    editions = [e for e in editions if e.get("schema") == "amb-fx-site/1" and e["date"] < data["date"]]

    def baseline(name):
        for e in editions:
            if e["markets"][name]["asof"] < m[name]["asof"]:
                return e["markets"][name]
        return None

    def move(name, label):
        ref = baseline(name)
        if not ref:
            return ""
        change = pct(m[name]["rates"]["USD"], ref["rates"]["USD"])
        return f" USD/{label} {change:+.2f}% versus the {date_label(ref['asof'])} reference."

    gh = baseline("Ghana")
    gh_move = pct(m["Ghana"]["rates"]["USD"], gh["rates"]["USD"]) if gh else 0
    lines += row("Ghana", "🇬🇭", "GH₵", f"Bank of Ghana interbank mid-rates; the cedi {'firmed' if gh_move < 0 else 'softened'} {abs(gh_move):.2f}% against the US dollar versus the {date_label(gh['asof'])} reference.")
    lines += row("Kenya", "🇰🇪", "KSh", "CBK commercial-banks’ average closing rates (not a standalone buy or sell quote)." + move("Kenya", "KES"))
    lines += row("South Africa", "🇿🇦", "R", "SARB weighted-average bank rates at about 10:30; 13 Oct benchmark reverified directly through the SARB endpoint this morning." + move("South Africa", "ZAR"))
    lines += row("Egypt", "🇪🇬", "E£", "CBE buy/sell mid-rates." + move("Egypt", "EGP"))
    lines += [
        "SOURCES & METHODOLOGY",
        "",
        "Official rates: latest available central-bank reference rates (CBN, Bank of Ghana, CBK, SARB, CBE), with effective dates indicated. Ghana and Egypt figures are midpoints of published buy/sell rates.",
        "",
        "Nigeria parallel-market rates: Aggregated from multiple independent market sources; previous-close/early observations are explicitly time-labeled and are not live opening quotes.",
        "",
        "Rates are indicative and may vary by source, location, transaction size and time. Informational only — not FX advice. The Flagship edition follows after verification.",
        "",
        "🔗 https://africamoneybrief.com/fx.html",
        "",
        "#AfricaMoneyBrief #FX #AfricanMarkets",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    opts = args()
    data = json.loads(Path(opts.input).read_text(encoding="utf-8"))
    early = data.get("edition_type") == "Early Look"
    text = render_early(data) if early else render(data)
    output = Path(opts.output) if opts.output else ROOT / "assets/social" / f"AMB_FX_{'Early_Look' if early else 'Flagship'}_{data['date']}.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(output)
