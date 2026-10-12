#!/usr/bin/env python3
"""Render the canonical 1080x1350 AMB FX Flagship social card from site data."""
import argparse
import datetime as dt
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1350
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAVY, PANEL, PANEL2 = "#061426", "#0B2037", "#0E2946"
GOLD, WHITE, MUTED, GREEN, LINE = "#EBCB74", "#F7FAFC", "#9FB2C5", "#64E2A6", "#27435E"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(ROOT / "data/fx/latest.json"))
    p.add_argument("--output")
    return p.parse_args()


def quote(low, high):
    return f"₦{low:,.0f}" if low == high else f"₦{low:,.0f}–{high:,.0f}"


def official_label(value):
    basis = value["official_basis"]
    if basis == "CBN selling rate (NFEM)":
        return "CBN NFEM"
    if basis.startswith("CBN"):
        return "CBN published"
    return "Derived"


def freshness(edition, asof):
    days = (edition - asof).days
    return "TODAY" if days == 0 else f"{days} day{'s' if days != 1 else ''} old"


def render(data, output):
    edition = dt.date.fromisoformat(data["date"])
    im = Image.new("RGB", (W, H), NAVY)
    px = im.load()
    for y in range(H):
        t = y / H
        rgb = (int(6 + 3 * t), int(20 + 10 * t), int(38 + 17 * t))
        for x in range(W):
            px[x, y] = rgb

    draw = ImageDraw.Draw(im)
    for x in range(0, W, 72):
        draw.line((x, 0, x, H), fill="#09213A", width=1)
    for y in range(0, H, 72):
        draw.line((0, y, W, y), fill="#09213A", width=1)

    logo = Image.open(ROOT / "assets/africa-money-brief-logo.png").convert("RGB")
    logo = logo.resize((104, 104), Image.Resampling.LANCZOS)
    im.paste(logo, (58, 40))
    draw.text((182, 52), "AFRICA", font=font(28, True), fill=WHITE)
    draw.text((182, 83), "MONEY BRIEF", font=font(28, True), fill=GOLD)
    draw.text((182, 116), "AFRICA’S MARKETS, DECODED.", font=font(13), fill=MUTED)
    draw.rounded_rectangle((766, 54, 1022, 126), radius=20, fill="#102E4D", outline="#31506C", width=2)
    draw.text((794, 68), "FX FLAGSHIP", font=font(18, True), fill=GOLD)
    draw.text((794, 94), edition.strftime("%a · %-d %b %Y").upper(), font=font(15, True), fill=WHITE)

    draw.text((58, 178), "NIGERIA", font=font(16, True), fill=GOLD)
    draw.text((58, 204), "Official vs parallel", font=font(44, True), fill=WHITE)
    draw.text((58, 261), "Local currency per one unit · Effective dates shown", font=font(18), fill=MUTED)

    units = {"USD": "per US$1", "GBP": "per £1", "EUR": "per €1"}
    cards = []
    for code in ("USD", "GBP", "EUR"):
        v = data["nigeria"][code]
        buy_mid = (v["parallel_buy_low"] + v["parallel_buy_high"]) / 2
        sell_mid = (v["parallel_sell_low"] + v["parallel_sell_high"]) / 2
        cards.append((
            code,
            units[code],
            f"₦{v['official_selling_rate']:,.2f}",
            f"{dt.date.fromisoformat(v['official_rate_date']).strftime('%-d %b')} · {official_label(v)}",
            quote(v["parallel_buy_low"], v["parallel_buy_high"]),
            quote(v["parallel_sell_low"], v["parallel_sell_high"]),
            f"₦{(buy_mid + sell_mid) / 2:,.2f}",
            f"+{v['premium_pct']:.2f}%",
        ))

    for x, c in zip((58, 397, 736), cards):
        y0, x1, y1 = 310, x + 286, 690
        draw.rounded_rectangle((x, y0, x1, y1), radius=24, fill=PANEL, outline=LINE, width=2)
        draw.text((x + 22, y0 + 20), c[0], font=font(28, True), fill=WHITE)
        draw.text((x + 22, y0 + 56), c[1], font=font(14), fill=MUTED)
        draw.rounded_rectangle((x + 177, y0 + 20, x + 264, y0 + 57), radius=12, fill="#123D35")
        draw.text((x + 188, y0 + 28), c[7], font=font(15, True), fill=GREEN)
        draw.line((x + 22, y0 + 87, x + 264, y0 + 87), fill=LINE, width=2)
        draw.text((x + 22, y0 + 108), "OFFICIAL", font=font(12, True), fill=MUTED)
        draw.text((x + 22, y0 + 130), c[2], font=font(25, True), fill=WHITE)
        draw.text((x + 22, y0 + 164), c[3], font=font(12), fill=MUTED)
        draw.text((x + 22, y0 + 202), "PARALLEL BUY", font=font(12, True), fill=MUTED)
        draw.text((x + 22, y0 + 223), c[4], font=font(20, True), fill=WHITE)
        draw.text((x + 22, y0 + 262), "PARALLEL SELL", font=font(12, True), fill=MUTED)
        draw.text((x + 22, y0 + 283), c[5], font=font(20, True), fill=WHITE)
        draw.line((x + 22, y0 + 321, x + 264, y0 + 321), fill=LINE, width=2)
        draw.text((x + 22, y0 + 339), "AMB MIDPOINT", font=font(12, True), fill=GOLD)
        draw.text((x + 132, y0 + 334), c[6], font=font(20, True), fill=GOLD)

    draw.text((58, 738), "AFRICA CROSS-MARKETS", font=font(16, True), fill=GOLD)
    draw.text((58, 768), "Latest official reference rates", font=font(31, True), fill=WHITE)
    tx0, ty0, tx1 = 58, 820, 1022
    draw.rounded_rectangle((tx0, ty0, tx1, 1208), radius=22, fill=PANEL2, outline=LINE, width=2)
    cols = (76, 350, 535, 720, 887)
    for x, header in zip(cols, ("MARKET / AS OF", "USD", "GBP", "EUR", "FRESHNESS")):
        draw.text((x, ty0 + 20), header, font=font(13, True), fill=MUTED)
    draw.line((76, ty0 + 55, 1004, ty0 + 55), fill=LINE, width=2)

    for i, (name, market) in enumerate(data["markets"].items()):
        y = ty0 + 75 + i * 76
        asof = dt.date.fromisoformat(market["asof"])
        age = freshness(edition, asof)
        if i:
            draw.line((76, y - 13, 1004, y - 13), fill="#1D3A55", width=1)
        draw.text((76, y), name.upper(), font=font(17, True), fill=WHITE)
        draw.text((76, y + 25), asof.strftime("%-d %b"), font=font(12), fill=MUTED)
        for x, code in zip((350, 535, 720), ("USD", "GBP", "EUR")):
            draw.text((x, y + 8), f"{market['symbol']}{market['rates'][code]:,.4f}", font=font(16, True), fill=WHITE)
        draw.text((887, y + 8), age, font=font(13, True), fill=GREEN if age == "TODAY" else GOLD)

    draw.text((58, 1241), "Premium = parallel buying midpoint ÷ CBN selling rate − 1.", font=font(14), fill=MUTED)
    draw.text((58, 1265), "Parallel observations aggregated from multiple independent market sources.", font=font(14), fill=MUTED)
    draw.text((58, 1298), "Indicative only · Not FX advice", font=font(13), fill="#7F95A8")
    draw.text((762, 1279), "africamoneybrief.com/fx.html", font=font(14, True), fill=GOLD)

    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output, quality=96)
    print(output)


if __name__ == "__main__":
    args = parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = Path(args.output) if args.output else ROOT / "assets/social" / f"AMB_FX_Flagship_{data['date']}.png"
    render(data, output)
