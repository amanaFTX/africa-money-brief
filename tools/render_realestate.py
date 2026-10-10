#!/usr/bin/env python3
"""Render real-estate.html region <!--AMB:realestate--> from data/real-estate.json, data/images.json, data/money-rates.json.
Fails (non-zero) on any gate violation; never renders a number that has not passed the gates."""
import json,re,sys,html,statistics
FORBIDDEN=re.compile(r'aboki|osuwon|nairafx|ngnrates|nairarates|egrates|standard bank|mansa',re.I)
D=json.load(open('data/real-estate.json')); IM=json.load(open('data/images.json'))['images']; M=json.load(open('data/money-rates.json'))
G=D['gates']; err=[]; e=html.escape
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
            n=f'{s}/{d["area"]}/{d["segment"]}'
            if d.get('grade') not in D['grades']: err.append(f'{n} bad grade')
            if d['grade']=='C' and (d.get('listings') or 0)<G['min_listings_grade_c']: err.append(f'{n} grade C needs >= {G["min_listings_grade_c"]} listings')
            for f in ('publisher','period','published','collected','gross_yield_pct'):
                if d.get(f) in (None,''): err.append(f'{n} missing {f}')
            y=d.get('gross_yield_pct')
            if y is not None and not (G['gross_yield_pct'][0]<=y<=G['gross_yield_pct'][1]): err.append(f'{n} gross yield {y}% outside gate; verify for typo/outlier')
            if d.get('price_usd') and d.get('rent_usd_month'):
                calc=d['rent_usd_month']*12/d['price_usd']*100
                if abs(calc-y)>G['yield_arith_tolerance_pts']: err.append(f'{n} yield {y}% != rent*12/price {calc:.2f}%')
    if FORBIDDEN.search(json.dumps(D)): err.append('forbidden provider name in data')
    if err: sys.exit('RENDER ERROR: '+'; '.join(err))
validate()
FL={'NG':'🇳🇬','GH':'🇬🇭','KE':'🇰🇪','ZA':'🇿🇦','EG':'🇪🇬','RW':'🇷🇼'}
def tbill(cc):
    c=M['countries'].get(cc); b=c and c.get('bills')
    if not b: return None
    t=[x for x in b['tenors'] if x['days']==364][0]
    if b['basis']=='discount': d=t['rate']/100; return ((1/(1-d*364/365))-1)*365/364*100
    return t['rate']
def med(ds): return statistics.median(d['gross_yield_pct'] for d in ds)
def net(y): lo,hi=G['net_haircut_pts']; return y-hi,y-lo
def payback(y):
    nl,nh=net(y); return (100/nh,100/nl) if nl>0 else None
f1=lambda x:f'{x+1e-9:.1f}'
def rng(pb):
    if not pb: return '\u2014'
    a,b=round(pb[0]),round(pb[1]); return f'{a} yrs' if a==b else f'{a}\u2013{b} yrs'
live=[(s,c) for s,c in D['cities'].items() if c['districts']]
def city_card(s,c):
    im=IM[s]; ds=c['districts']; bonus=' <span class="chip">Bonus city</span>' if c['tier']=='bonus' else ''
    if ds:
        y=med(ds); body=f'<div class="big">{f1(y)}%<small> median gross yield</small></div><p>{len(ds)} data points · {e(ds[0]["publisher"])} · {e(ds[0]["period"])}</p>'
    else: body='<span class="pill warn">Collecting</span><p>No current verified yield yet</p>'
    return (f'<article class="rcity"><div class="rimg"><img src="{im["file"]}" alt="{e(im["alt"])}"><span class="rtag">{e(im["label"])}</span></div>'
            f'<div class="rbody"><small>{FL[c["country"]]} {e(D["countries"][c["country"]].upper())}</small><h3>{e(c["name"])}{bonus}</h3>{body}</div></article>')
# headline facts (computed)
facts=[]
rank=sorted(live,key=lambda sc:-med(sc[1]['districts']))
hi,lo=rank[0],rank[-1]
facts.append((f'{f1(med(hi[1]["districts"]))}%',f'{hi[1]["name"]} has the highest median gross yield in this release.'))
facts.append((f'{f1(med(lo[1]["districts"]))}%',f'{lo[1]["name"]} has the lowest.'))
for s,c in live:
    t=tbill(c['country'])
    if c['country']=='NG' and t: facts.append((f'{f1(t)}%',f'Nigeria’s 364-day Treasury bill yields {f1(t)}%, against a {f1(med(c["districts"]))}% median gross yield in Lagos, before any price growth.')); break
fh=''.join(f'<div class="fact"><b>{a}</b><span>{b}</span></div>' for a,b in facts)
Q=[('Should I invest in real estate?','Net yield plus price growth vs stocks, T-bills and inflation, in local currency and USD.'),
('What is the return vs the stock market?','City return against each country’s main equity index and the T-bill yields on <a href="money-rates.html">Money &amp; Rates</a>.'),
('What is the payback period?','Price ÷ net annual rent. The table below shows a range using the publisher’s cost rule of thumb.'),
('Residential or commercial?','Gross yield by district and type; cap rates where research reports publish them.'),
('Short-let or long-let?','Nightly rate × occupancy × 365, less platform fees, cleaning and management, against long-let net yield.'),
('Which cities are best in each country?','A published scoring model: yield, growth, liquidity, FX risk, transaction cost, legal clarity.'),
('How do the countries compare?','One table, one definition, one as-of date per figure.')]
qs=''.join(f'<article class="card"><span class="tag">QUESTION {i+1}</span><h3>{q}</h3><p>{a}</p></article>' for i,(q,a) in enumerate(Q))
rows=''
for s,c in D['cities'].items():
    ds=c['districts']; cc=c['country']
    if ds:
        y=med(ds); nl,nh=net(y); pb=payback(y); t=tbill(cc)
        pbs=rng(pb)
        rows+=(f'<tr><td>{FL[cc]} {e(c["name"])}</td><td class="num"><b>{f1(y)}%</b></td><td class="num">{f1(nl)}–{f1(nh)}%</td><td class="num">{pbs}</td>'
               f'<td class="num">{(f1(t)+"%") if t else "—"}</td><td class="num">{e(ds[0]["period"])}</td></tr>')
    else: rows+=f'<tr class="dim"><td>{FL[cc]} {e(c["name"])}</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">Collecting</td></tr>'
det=''
for s,c in live:
    for d in c['districts']:
        pb=payback(d['gross_yield_pct']); nl,nh=net(d['gross_yield_pct'])
        x=[]
        if d.get('rent_ngn_year_2bed'): x.append(f'2-bed rent ₦{d["rent_ngn_year_2bed"]/1e6:g}m a year')
        if d.get('price_usd'): x.append(f'${d["price_usd"]:,} · ${d["rent_usd_month"]:,}/month')
        if d.get('note') and not d.get('rent_ngn_year_2bed') and not d.get('price_usd'): x.append(d['note'])
        flag='<span class="pill ok">Cross-checked</span>' if d['cross_check']=='two' else '<span class="pill warn">Single source</span>'
        det+=(f'<tr><td>{e(c["name"])}</td><td>{e(d["area"])}<small>{e(d["segment"])}</small></td><td class="num"><b>{f1(d["gross_yield_pct"])}%</b></td>'
              f'<td class="num">{f1(nl)}–{f1(nh)}%</td><td class="num">{rng(pb)}</td>'
              f'<td>{e(d["publisher"])}<small>{e(d["period"])} · published {e(d["published"])} · grade {d["grade"]}</small></td><td>{flag}<small>{e("; ".join(x))}</small></td></tr>')
xn=''.join(f'<li><b>{e(c["name"])}:</b> {e(c["cross_note"])}</li>' for s,c in live if c.get('cross_note'))
rj=''.join(f'<li><b>{e(r["item"])}:</b> {e(r["reason"])}</li>' for r in D.get('rejected',[]))
out=f'''<div class="re"><section class="section"><div class="heading"><div><p class="eyebrow">WHAT THE DATA SAYS</p><h2>Should you invest in African real estate?</h2></div><p>{e(D["release"])}. Gross yields here are before price growth, taxes and fees.</p></div><div class="facts">{fh}</div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">CROSS-COUNTRY COMPARISON</p><h2>Yield, payback and the T-bill alternative</h2></div><p>Median of each city’s published data points. {e(D["net_note"])}</p></div><div class="panel"><div class="tw"><table class="rtable"><thead><tr><th>City</th><th class="num">Gross yield</th><th class="num">Indicative net</th><th class="num">Payback</th><th class="num">364-day T-bill</th><th class="num">Data period</th></tr></thead><tbody>{rows}</tbody></table></div></div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">CITY ATLAS</p><h2>Five countries, plus Kigali</h2></div><p>Images are labelled illustrations for now. Licensed photography replaces them city by city, each with a licence record.</p></div><div class="rgrid">{"".join(city_card(s,c) for s,c in D["cities"].items())}</div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">THE EVIDENCE</p><h2>Every data point, with its source</h2></div><p>Grade B: published research. Asking prices are not transaction prices.</p></div><div class="panel"><div class="tw"><table class="rtable"><thead><tr><th>City</th><th>Area / segment</th><th class="num">Gross</th><th class="num">Net</th><th class="num">Payback</th><th>Publisher</th><th>Checks</th></tr></thead><tbody>{det}</tbody></table></div></div></section>
<section class="section"><div class="panel"><div class="ph"><h3>How AMB checks property data</h3></div><ul class="rlist"><li>Grades: <b>A</b> official or transaction index, <b>B</b> published research report, <b>C</b> listing-portal asking sample (needs at least {G["min_listings_grade_c"]} listings), <b>D</b> crowdsourced.</li><li>Gates: gross yield {G["gross_yield_pct"][0]}–{G["gross_yield_pct"][1]}%, rent × 12 ÷ price must match the published yield, anything stale is labelled, and suspect figures are held out.</li>{xn}<li>Not investment advice. Property is illiquid; published yields are gross and based on asking prices.</li></ul><div class="ph" style="margin-top:18px"><h3>Held out of this release</h3></div><ul class="rlist">{rj}</ul></div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">QUESTIONS THIS PAGE WILL ANSWER</p><h2>Coming in later releases</h2></div></div><div class="cards">{qs}</div></section></div>'''
p='real-estate.html'; t=open(p).read()
new='<!--AMB:realestate-->'+out+'<!--/AMB:realestate-->'
if '<!--AMB:realestate-->' not in t: sys.exit('markers missing')
open(p,'w').write(re.sub(r'<!--AMB:realestate-->[\s\S]*?<!--/AMB:realestate-->',lambda m:new,t)); print('rendered real-estate.html')
