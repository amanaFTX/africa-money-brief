#!/usr/bin/env python3
"""Render real-estate.html region <!--AMB:realestate--> from data/real-estate.json + data/images.json.
Fails (non-zero) on any gate violation; never renders a number that has not passed the gates."""
import json,re,sys,datetime as dt,html,statistics
FORBIDDEN=re.compile(r'aboki|osuwon|nairafx|ngnrates|nairarates|egrates|standard bank|mansa',re.I)
D=json.load(open('data/real-estate.json')); IM=json.load(open('data/images.json'))['images']
ASOF=dt.date.fromisoformat(D['as_of']); G=D['gates']; err=[]
e=html.escape
def validate():
    for k,i in IM.items():
        for f in ('file','kind','licence','credit','alt'):
            if not i.get(f): err.append(f'image {k} missing {f}')
        if i.get('kind')=='illustration' and (i.get('depicts_real_property') or i.get('label')!='Illustration'):
            err.append(f'illustration {k} must be labelled and not depict a real property')
    for s,c in D['cities'].items():
        if c['country'] not in D['countries']: err.append(f'{s} unknown country')
        if s not in IM: err.append(f'{s} has no registered image')
        for d in c['districts']:
            n=d.get('listings') or 0
            if n<G['min_listings']: err.append(f'{s}/{d["name"]} only {n} listings')
            if d.get('grade') not in D['grades']: err.append(f'{s}/{d["name"]} bad grade')
            if not d.get('sources') or not d.get('collected'): err.append(f'{s}/{d["name"]} missing source/date')
            elif (ASOF-dt.date.fromisoformat(d['collected'])).days<0: err.append(f'{s}/{d["name"]} dated after as_of')
            y=gross(d)
            if y is not None and not (G['gross_yield_pct'][0]<=y<=G['gross_yield_pct'][1]): err.append(f'{s}/{d["name"]} gross yield {y:.1f}% outside gate; verify for typo/outlier')
    if FORBIDDEN.search(json.dumps(D)): err.append('forbidden provider name in data')
    if err: sys.exit('RENDER ERROR: '+'; '.join(err))
def gross(d):
    p,r=d.get('price_per_m2_local'),d.get('rent_per_m2_month_local')
    return None if not(p and r) else r*12/p*100
validate()
FL={'NG':'🇳🇬','GH':'🇬🇭','KE':'🇰🇪','ZA':'🇿🇦','EG':'🇪🇬','RW':'🇷🇼'}
def city_card(s,c):
    im=IM[s]; ds=c['districts']
    if ds:
        ys=[gross(d) for d in ds if gross(d)]; body=f'<b>{statistics.median(ys):.1f}%</b> median gross yield · {sum(d["listings"] for d in ds)} listings' if ys else 'Prices collected; rents pending'
    else: body='<span class="pill warn">Collecting</span><br>First data in the next release'
    bonus=' <span class="chip">Bonus city</span>' if c['tier']=='bonus' else ''
    return (f'<article class="rcity"><div class="rimg"><img src="{im["file"]}" alt="{e(im["alt"])}"><span class="rtag">{e(im["label"])}</span></div>'
            f'<div class="rbody"><small>{FL[c["country"]]} {e(D["countries"][c["country"]].upper())}</small><h3>{e(c["name"])}{bonus}</h3><p>{body}</p></div></article>')
Q=[('Should I invest in real estate?','Net yield + price growth vs stocks, T-bills and inflation, in local currency and USD.'),
('What is the return vs the stock market?','City return against each country’s main equity index and the T-bill yields on <a href="money-rates.html">Money &amp; Rates</a>.'),
('What is the payback period?','Price ÷ net annual rent after vacancy, management, maintenance, service charges and tax. A second figure adds price growth.'),
('Residential or commercial?','Gross yield by district and type; cap rates where research reports publish them.'),
('Short-let or long-let?','Nightly rate × occupancy × 365, less platform fees, cleaning and management, against long-let net yield.'),
('Which cities are best in each country?','A published scoring model: yield, growth, liquidity, FX risk, transaction cost, legal clarity. Weights shown in full.'),
('How do the countries compare?','One table, one definition, one as-of date per figure, ranked only once the gates pass.')]
qs=''.join(f'<article class="card"><span class="tag">QUESTION {i+1}</span><h3>{q}</h3><p>{a}</p><p class="pend"><span class="pill warn">Answer pending first data release</span></p></article>' for i,(q,a) in enumerate(Q))
core=[(s,c) for s,c in D['cities'].items() if c['tier']=='core']; bon=[(s,c) for s,c in D['cities'].items() if c['tier']=='bonus']
rows=''
for s,c in core+bon:
    ds=c['districts']; ys=[gross(d) for d in ds if gross(d)]
    rows+=f'<tr><td>{FL[c["country"]]} {e(c["name"])}</td><td class="num">{"%.1f%%"%statistics.median(ys) if ys else "—"}</td><td class="num">—</td><td class="num">—</td><td class="num">{max(d["collected"] for d in ds) if ds else "Collecting"}</td></tr>'
out=f'''<div class="re"><section class="section"><div class="heading"><div><p class="eyebrow">THE QUESTIONS THIS PAGE ANSWERS</p><h2>Should you invest in African real estate?</h2></div><p>{e(D["release"])}. AMB publishes a figure only after it passes its gates, so unverified numbers never appear here.</p></div><div class="cards">{qs}</div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">CROSS-COUNTRY COMPARISON</p><h2>Yield, payback and rank</h2></div><p>Gross yield = annual rent ÷ price. Net yield and payback appear once assumptions are published.</p></div><div class="panel"><table class="rtable"><thead><tr><th>City</th><th class="num">Gross yield</th><th class="num">Net yield</th><th class="num">Payback</th><th class="num">Data as of</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">CITY ATLAS</p><h2>Five countries, plus Kigali</h2></div><p>Images are labelled illustrations for now. Licensed photography replaces them city by city, each with a licence record.</p></div><div class="rgrid">{"".join(city_card(s,c) for s,c in core+bon)}</div></section>
<section class="section"><div class="panel"><div class="ph"><h3>How AMB checks property data</h3></div><ul class="rlist"><li>Evidence grades: <b>A</b> official or transaction index, <b>B</b> published research, <b>C</b> listing-portal asking sample, <b>D</b> crowdsourced. Every figure shows its grade, source and date.</li><li>Gates: at least {G["min_listings"]} listings per district, sources within {G["max_cross_source_gap_pct"]}%, gross yield between {G["gross_yield_pct"][0]}% and {G["gross_yield_pct"][1]}%, and anything older than {G["stale_days"]} days is labelled stale.</li><li>Not investment advice. Property markets are illiquid and asking prices are not transaction prices.</li></ul></div></section></div>'''
p='real-estate.html'; t=open(p).read()
new='<!--AMB:realestate-->'+out+'<!--/AMB:realestate-->'
if '<!--AMB:realestate-->' in t: t=re.sub(r'<!--AMB:realestate-->[\s\S]*?<!--/AMB:realestate-->',lambda m:new,t)
else: sys.exit('markers missing')
open(p,'w').write(t); print('rendered real-estate.html')
