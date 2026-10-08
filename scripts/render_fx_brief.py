#!/usr/bin/env python3
"""AMB FX infographic — branded reference layout, rendered on GitHub Actions."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

source = Path(sys.argv[1])
data = json.loads(source.read_text(encoding="utf-8"))
out = Path("assets/briefs") / (source.stem + ".png")
out.parent.mkdir(parents=True, exist_ok=True)
W, H = 1100, 1376
navy, panel, panel2 = "#081b2e", "#102d45", "#17334b"
gold, orange, white, muted = "#f6bf79", "#df914f", "#f8f9fc", "#a8baca"
im = Image.new("RGB", (W,H), navy)
d = ImageDraw.Draw(im)
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
heavy = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def f(size, bold=False):
    return ImageFont.truetype(heavy if bold else regular, size)
def txt(x,y,s,size,color=white,bold=False):
    d.text((x,y),str(s),font=f(size,bold),fill=color)
def fit(s, width, size, minimum=13, bold=True):
    while size>minimum and d.textbbox((0,0),s,font=f(size,bold))[2]>width:
        size-=1
    return size
# Thin circular gold detail, cropped in top right
for r in range(70,215,8):
    d.arc((955-r,65-r,955+r,65+r),180,355,fill="#785638",width=1)
d.rounded_rectangle((44,35,1055,140),radius=24,fill=panel)
txt(69,54,"AFRICA",44,white,True)
txt(269,54,"MONEY BRIEF",44,gold,True)
txt(70,112,"AFRICA'S MARKETS, DECODED.",15,muted,True)
txt(50,166,data.get("title","AFRICA FX: EARLY LOOK").replace(" • ",": "),48,white,True)
txt(53,231,data.get("dateline","THU 8 OCT 2026  |  RATES VERIFIED AS OF 06:30 AM WAT"),21,gold,True)
d.rounded_rectangle((49,265,1053,313),radius=11,fill=orange)
txt(67,277,data.get("benchmark_label","07 OCT PRIOR CLOSE / BENCHMARK • NOT LIVE 08 OCT QUOTES"),19,navy,True)
cols=[355,585,819]
txt(49,334,"MARKET / STATUS",20,gold,True)
for x,cc in zip(cols,("USD","GBP","EUR")): txt(x,334,cc,20,gold,True)
market_y=374
for i,m in enumerate(data["markets"]):
    y=market_y+i*131
    d.rounded_rectangle((46,y,1054,y+120),radius=15,fill=panel if i%2==0 else panel2,outline="#3b5b72",width=1)
    name=m.get("name",m.get("country","").split("  |")[0]).upper()
    txt(67,y+16,name,23,white,True)
    txt(67,y+55,m.get("source",m.get("country","").split("|")[-1].strip()),15,muted)
    txt(67,y+86,m.get("status","07 OCT • PRIOR SESSION"),12,gold,True)
    rates=m.get("columns")
    if not rates:
        # Existing Oct 8 source data fallback
        import re
        s=m["rates"]
        if name=="EGYPT":
            rates=["E£52.3204 / 52.4600","E£69.1414 / 69.3469","E£58.5465 / 58.7132"]
        else:
            rates=re.findall(r"(?:USD|GBP|EUR)\\s+([^ ]+)",s)
    for x,value in zip(cols,rates):
        value=str(value)
        txt(x,y+49,value,fit(value,213,22,13),white,True)
parallel=data.get("parallel",{})
y=1040
d.rounded_rectangle((46,y,1054,y+171),radius=18,fill=gold)
txt(67,y+14,parallel.get("title","NIGERIA PARALLEL — 07 OCT OBSERVATIONS"),21,navy,True)
txt(67,y+51,"USD BUY  "+parallel.get("usd_buy","₦1,355–1,358.50"),20,navy,True)
txt(566,y+51,"USD SELL  "+parallel.get("usd_sell","₦1,365–1,368.27"),20,navy,True)
txt(67,y+87,parallel.get("gbp","GBP: B ₦1,815–1,832.91  |  S ₦1,848–1,852.59"),15,navy)
txt(67,y+114,parallel.get("eur","EUR: B ₦1,525.62–1,530  |  S ₦1,548.42–1,550"),15,navy)
txt(67,y+140,parallel.get("note","Two independent 7 Oct sources • ranges, not consensus"),13,navy)
d.rounded_rectangle((46,1225,1054,1293),radius=14,fill="#0c2439",outline=gold,width=2)
txt(66,1233,data.get("overnight_title","OVERNIGHT USD  |  DXY ~102.25 (EARLY 8 OCT)"),19,gold,True)
txt(66,1263,data.get("overnight_note","WATCH: STRONGER USD & OIL PRESSURE AS AFRICA OPENS"),15,white)
txt(52,1307,"Rates vary by source, location & time. Informational only; not financial or FX advice.",13,muted)
txt(52,1335,"africamoneybrief.com/fx.html  •  @AMBriefDaily",15,gold,True)
im.save(out,optimize=True)
print(out)
