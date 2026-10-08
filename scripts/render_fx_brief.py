#!/usr/bin/env python3
"""Render AMB FX briefing PNG from a versioned JSON briefing. No external image URL."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

source=Path(sys.argv[1])
data=json.loads(source.read_text(encoding="utf-8"))
output=Path("assets/briefs")/(source.stem+".png")
output.parent.mkdir(parents=True,exist_ok=True)
W,H=1200,1500
im=Image.new("RGB",(W,H),"#061426")
d=ImageDraw.Draw(im)
def font(size,bold=False):
    names=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    return ImageFont.truetype(names[0],size)
white="#F5F8FC"; gold="#E7B65A"; muted="#C0CEDC"
d.rounded_rectangle((44,42,1156,1458),radius=28,outline="#38516C",width=3)
d.text((90,95),"AFRICA MONEY BRIEF",font=font(49,True),fill=gold)
d.text((90,175),data["title"],font=font(58,True),fill=white)
d.text((90,252),data["subtitle"],font=font(27),fill=muted)
y=338
for entry in data["markets"]:
    d.rounded_rectangle((80,y,1120,y+160),radius=20,fill="#10253D",outline="#284763",width=2)
    d.text((110,y+18),entry["country"],font=font(35,True),fill=gold)
    d.text((110,y+74),entry["rates"],font=font(26),fill=white)
    if entry.get("note"):
        d.text((110,y+120),entry["note"],font=font(19),fill=muted)
    y+=187
d.text((90,1300),data["footer"],font=font(23),fill=muted)
d.text((90,1350),"africamoneybrief.com  |  @AMBriefDaily",font=font(24,True),fill=gold)
im.save(output,optimize=True)
print(output)
