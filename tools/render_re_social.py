#!/usr/bin/env python3
"""Deterministic 1080x1080 PNG for the weekly real-estate social post. All numbers come from data/real-estate.json."""
import json, statistics, sys
from decimal import Decimal, ROUND_HALF_UP
r1=lambda v: str(Decimal(str(v)).quantize(Decimal("0.1"),rounding=ROUND_HALF_UP))
from PIL import Image, ImageDraw, ImageFont
d = json.load(open("data/real-estate.json"))
city = d["cities"]["lagos"]; rows = sorted(city["districts"], key=lambda r: -r["gross_yield_pct"])
ys = [r["gross_yield_pct"] for r in rows]; med = statistics.median(ys)
NAVY=(10,22,46); GOLD=(212,175,55); WHITE=(240,240,235); MUT=(150,160,180); PANEL=(20,38,72)
F="/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
f=lambda s,b=False: ImageFont.truetype(F%("-Bold" if b else ""),s)
im=Image.new("RGB",(1080,1080),NAVY); g=ImageDraw.Draw(im)
g.rectangle([0,0,1080,10],fill=GOLD)
g.text((60,50),"AFRICA MONEY BRIEF  |  REAL ESTATE",font=f(26,True),fill=GOLD)
g.text((60,100),"Lagos gross rental yields",font=f(54,True),fill=WHITE)
g.text((60,170),"Nigeria review, as of %s"%("14 Oct 2026"),font=f(26),fill=MUT)
g.text((60,225),r1(min(ys))+"%",font=f(64,True),fill=GOLD); g.text((60,300),"lowest (%s)"%rows[-1]["area"],font=f(22),fill=MUT)
g.text((400,225),r1(med)+"%",font=f(64,True),fill=GOLD); g.text((400,300),"median of %d areas"%len(ys),font=f(22),fill=MUT)
g.text((740,225),r1(max(ys))+"%",font=f(64,True),fill=GOLD); g.text((740,300),"highest (%s)"%rows[0]["area"],font=f(22),fill=MUT)
y0=360; mx=max(ys)
for i,r in enumerate(rows):
    y=y0+i*62
    g.text((60,y+8),r["area"],font=f(24),fill=WHITE)
    w=int(r["gross_yield_pct"]/mx*430)
    g.rectangle([330,y+4,330+w,y+44],fill=GOLD)
    g.text((330+w+14,y+8),"%.2f%%"%r["gross_yield_pct"],font=f(24,True),fill=WHITE)
g.rectangle([60,800,1020,930],fill=PANEL)
g.text((80,815),"Source: published research dataset, 16 Jul 2026",font=f(24),fill=WHITE)
g.text((80,850),"Evidence grade B  |  single source  |  status: collecting",font=f(24),fill=WHITE)
g.text((80,885),"Asking-rent based, not transaction prices. Gross, before costs.",font=f(24),fill=WHITE)
g.text((60,960),"Abuja: no source meets our evidence gates this week.",font=f(24),fill=GOLD)
g.text((60,1005),"africamoneybrief.com/real-estate.html",font=f(26,True),fill=WHITE)
g.text((60,1040),"Informational only; not investment advice.",font=f(20),fill=MUT)
im.save(sys.argv[1] if len(sys.argv)>1 else "assets/social/AMB_RE_2026-10-14.png")
print("median",med,"min",min(ys),"max",max(ys))
