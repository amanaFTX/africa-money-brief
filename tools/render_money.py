import json,re,sys,datetime as dt,html
FORBIDDEN=re.compile(r'aboki|osuwon|nairafx|ngnrates|nairarates|egrates|standard bank|mansa',re.I)
D=json.load(open('data/money-rates.json')); C=D['countries']; ASOF=dt.date.fromisoformat(D['as_of'])
f=lambda x,d=2:f'{x:,.{d}f}'
dl=lambda s:dt.date.fromisoformat(s).strftime('%-d %b %Y')
ds=lambda s:dt.date.fromisoformat(s).strftime('%-d %b')
def yld(b,t):  # annualised yield used for comparison
    if b['basis']=='discount':
        n=t['days']; d=t['rate']/100; return ((1/(1-d*n/365))-1)*365/n*100
    return t['rate']
def age(s):
    n=(ASOF-dt.date.fromisoformat(s)).days; return n
def chip(s):
    n=age(s); 
    if n<=7: return '<span class="pill ok">Current</span>'
    if n<=45: return f'<span class="pill gold">{n} days old</span>'
    return f'<span class="pill warn">{n} days old</span>'
def validate():
    err=[]
    for k,c in C.items():
        for key in ('policy',):
            if dt.date.fromisoformat(c[key]['date'])>ASOF: err.append(f'{k} {key} date after as_of')
        b=c['bills']
        if b:
            if dt.date.fromisoformat(b['auction'])>ASOF: err.append(f'{k} auction date after as_of')
            if b['basis'] not in ('discount','interest','yield'): err.append(f'{k} bills basis')
            ds_={t['days'] for t in b['tenors']}
            if not {91,182,364}<=ds_: err.append(f'{k} missing 91/182/364 tenor')
            for t in b['tenors']:
                if not (0<t['rate']<60): err.append(f'{k} {t["t"]} rate out of range')
                if t.get('prev') is not None and abs(t['rate']-t['prev'])>3: err.append(f'{k} {t["t"]} moved >3 points; needs corroboration')
        d=c['deposits']
        if d:
            for r in d['rows']:
                if not (0<r['rate']<60): err.append(f'{k} deposit rate out of range')
    if err: sys.exit('RENDER ERROR: '+'; '.join(err))
validate()
order=['NG','GH','KE','ZA','EG']
# ---- board ----
def best_dep(c):
    d=C[c]['deposits']
    if not d: return None
    top=max(d['rows'],key=lambda r:r['rate']); return top
rows=''
for k in order:
    c=C[k]; b=c['bills']; p=c['policy']
    def cell(i):
        if not b or i>=len(b['tenors']) : return '<td class="num">—</td>'
        t=[x for x in b['tenors'] if x['days']==[91,182,364][i]][0]; y=yld(b,t)
        sub=f'<small>{f(t["rate"])}% discount</small>' if b['basis']=='discount' else f'<small>{ds(b["auction"])}</small>'
        return f'<td class="num"><b>{f(y)}%</b>{sub}</td>'
    if b:
        cells=''.join(cell(i) for i in range(3))
        t364=[x for x in b['tenors'] if x['days']==364][0]; y364=yld(b,t364)
        inf=c['inflation']
        real=f'<td class="num"><b class="{"pos" if y364-inf["rate"]>0 else "neg"}">{y364-inf["rate"]:+.2f} pts</b><small>vs {f(inf["rate"],2)}% inflation, {inf["period"]}</small></td>' if inf else '<td class="num">—<small>inflation not yet verified</small></td>'
    else:
        cells='<td colspan="3" class="num"><span class="pill warn">Re-verifying</span><small>Official yields could not be confirmed on 9 Oct</small></td>'; real='<td class="num">—</td>'
    d=best_dep(k)
    dep=f'<td class="num"><b>{f(d["rate"])}%</b><small>{d["p"]} · {ds(c["deposits"]["date"])}</small></td>' if d else '<td class="num">—<small>none verified</small></td>'
    rows+=f'<tr><td><b>{c["flag"]} {c["name"]}</b><small>{p["label"]} {f(p["rate"])}% · {ds(p["date"])}</small></td>{cells}{real}{dep}</tr>'
board=f'''<div class="tw"><table><thead><tr><th>COUNTRY</th><th class="num">91-DAY</th><th class="num">182-DAY</th><th class="num">364-DAY</th><th class="num">364-DAY VS INFLATION</th><th class="num">TOP DEPOSIT RATE</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="fine">Annualised yield on government bills at the latest primary auction. Nigeria’s auction results are discount rates, so AMB converts them to an equivalent annual yield (actual/365) for comparison; the published discount rate is shown underneath. Ghana, Kenya and South Africa publish interest or yield rates directly. Gross of tax, fees and currency moves. Indicative only; not investment advice.</p>'''
# ---- bars ----
mx=20
def bar(k):
    c=C[k]; b=c['bills']
    if not b: return f'<div class="bar"><span>{c["flag"]} {c["name"]}</span><div class="track"></div><em>Re-verifying</em></div>'
    t91=[x for x in b['tenors'] if x['days']==91][0]; t364=[x for x in b['tenors'] if x['days']==364][0]
    a=yld(b,t91); z=yld(b,t364)
    return f'<div class="bar"><span>{c["flag"]} {c["name"]}</span><div class="track"><i class="a" style="width:{a/mx*100:.1f}%"></i><i class="b" style="width:{z/mx*100:.1f}%"></i></div><em>{f(a)}% · {f(z)}%</em></div>'
bars=f'<div class="legend"><span><i style="background:#f5c84c"></i>91-day</span><span><i style="background:#64b5e2"></i>364-day</span></div><div class="bars">{"".join(bar(k) for k in order)}</div>'
# ---- country sections ----
def section(k):
    c=C[k]; p=c['policy']; b=c['bills']; d=c['deposits']; inf=c['inflation']
    stats=f'<div class="stats"><div class="stat"><small>{p["label"].upper()} · {dl(p["date"])}</small><b>{f(p["rate"])}%</b></div><div class="stat"><small>INFLATION{" · "+inf["period"].upper() if inf else ""}</small><b>{f(inf["rate"],2)+"%" if inf else "Pending"}</b></div><div class="stat"><small>LATEST BILL AUCTION</small><b>{dl(b["auction"]) if b else "Pending"}</b></div></div>'
    if b:
        tr=''
        for t in b['tenors']:
            y=yld(b,t); ch=(t['rate']-t['prev']) if t['prev'] is not None else None
            chs='—' if ch is None else (f'{ch*100:+.1f} bp' if abs(ch)>=0.0005 else 'unchanged')
            rate=f'{f(t["rate"],4 if t["rate"]<10 and k in("GH","KE") else 2)}%'
            yc=f'<td class="num"><b>{f(y)}%</b></td>' if b['basis']=='discount' else ''
            tr+=f'<tr><td><b>{t["t"]}</b></td><td class="num">{rate}</td>{yc}<td class="num">{chs}</td><td>{t["alloc"]}</td></tr>'
        yh='<th class="num">EQUIV. YIELD</th>' if b['basis']=='discount' else ''
        lab={'discount':'STOP (DISCOUNT) RATE','interest':'INTEREST RATE','yield':'YIELD'}[b['basis']]
        bt=f'<div class="tw"><table style="min-width:640px"><thead><tr><th>BILL</th><th class="num">{lab}</th>{yh}<th class="num">CHANGE</th><th>AUCTION DETAIL</th></tr></thead><tbody>{tr}</tbody></table></div><p class="fine">Source: <a href="{b["src_url"]}">{b["src"]}</a>, auction {dl(b["auction"])}.</p>'
    else:
        bt='<div class="gap"><b>Treasury-bill yields are being re-verified.</b> The earlier board listed 3–12 month secondary-market yields of 24–25%. They do not reconcile with a 19% key rate, and the CBE auction pages did not load for AMB’s check on 9 Oct, so no Egyptian bill yields are shown until they are confirmed from a CBE or Ministry of Finance release.</div>'
    if d:
        dr=''.join(f'<tr><td><b>{r["p"]}</b><small>{r["terms"]}</small></td><td class="num"><b>{f(r["rate"])}%</b></td><td>{r["detail"]}</td></tr>' for r in d['rows'])
        dep=f'<div class="tw" style="margin-top:16px"><table style="min-width:640px"><thead><tr><th>{d["kind"].upper()}</th><th class="num">TOP RATE</th><th>DETAIL</th></tr></thead><tbody>{dr}</tbody></table></div><p class="fine">{d["src"]}, as of {dl(d["date"])} {chip(d["date"])} {d.get("note","")}</p>'
    else:
        dep='<div class="gap" style="margin-top:16px"><b>Bank savings and certificate rates are not yet verified for Egypt.</b> AMB will add them once published rates can be matched to a date, minimum balance and tenor.</div>'
    return f'<section class="section" id="{k.lower()}"><div class="chead"><div><p class="eyebrow">{c["name"].upper()}</p><h2>{c["flag"]} {c["name"]}</h2></div></div>{stats}<h3 style="margin:18px 0 10px">Treasury bills</h3>{bt}<h3 style="margin:22px 0 0">Bank deposits and savings</h3>{dep}</section>'
secs=''.join(section(k) for k in order)
takes={'NG':'','GH':'','KE':'','ZA':'','EG':''}
# ---- calculator ----
calc='''<div class="calc" id="amb-calc"><div><div class="f"><label for="cp">PRODUCT</label><select id="cp"></select></div><div class="f"><label for="ca">AMOUNT</label><input id="ca" type="number" inputmode="decimal" min="0" step="1000" value="10000000"></div><div class="f" id="cmw"><label for="cm">MONTHS HELD</label><input id="cm" type="number" min="1" max="12" step="1" value="12"></div></div>
<div class="res"><span id="cl">Estimated interest</span><strong id="ci">—</strong><span id="cs">Loading rates…</span><span style="font-size:12px;color:#8ba0b3">Simple interest at the rate shown, before tax, fees and exchange-rate moves. Bills are held to maturity; deposits assume the rate stays unchanged. An example, not an offer.</span></div></div>
<script src="assets/calc.js"></script>'''
# ---- freshness ----
fr=''
for k in order:
    c=C[k]; b=c['bills']
    fr+=f'<tr><td><b>{c["flag"]} {c["name"]}</b></td><td>{dl(c["policy"]["date"])} {chip(c["policy"]["date"])}</td><td>{(dl(b["auction"])+" "+chip(b["auction"])) if b else "<span class=\'pill warn\'>Re-verifying</span>"}</td><td>{(dl(c["deposits"]["date"])+" "+chip(c["deposits"]["date"])) if c["deposits"] else "<span class=\'pill warn\'>Not verified</span>"}</td><td>{("Primary" if k!="ZA" else "Secondary relay; primary check pending") if b else "—"}</td></tr>'
fresh=f'<div class="tw fresh"><table style="min-width:640px"><thead><tr><th>COUNTRY</th><th>POLICY RATE</th><th>T-BILL AUCTION</th><th>DEPOSIT DATA</th><th>BILL SOURCE</th></tr></thead><tbody>{fr}</tbody></table></div>'
ng=C['NG']['bills']; y364=yld(ng,[t for t in ng['tenors'] if t['days']==364][0])
def takeaway():
    parts=[]; best=None
    for k in order:
        c=C[k]; b=c['bills']
        if not b: continue
        t=[x for x in b['tenors'] if x['days']==364][0]; y=yld(b,t)
        if best is None or y>best[0]: best=(y,k,t)
    if best:
        y,k,t=best; c=C[k]; inf=c['inflation']
        sp=f", about {y-inf['rate']:.1f} points above {inf['period']} inflation" if inf and y>inf['rate'] else ''
        disc=f" ({f(t['rate'])}% on the discount basis)" if c['bills']['basis']=='discount' else ''
        parts.append(f"{c['name']}’s 364-day bill is the highest verified yield on the board at about {f(y)}%{disc}{sp}.")
    for k in order:
        c=C[k]; b=c['bills']; inf=c['inflation']
        if b and inf:
            t=[x for x in b['tenors'] if x['days']==91][0]; y=yld(b,t)
            if y<inf['rate']: parts.append(f"{c['name']}’s 91-day bill ({f(y)}%) pays less than {inf['period']} inflation ({f(inf['rate'],1)}%).")
    gap=None
    for k in order:
        c=C[k]; b=c['bills']; d=c['deposits']
        if not(b and d): continue
        sv=[r for r in d['rows'] if r['p'].lower().startswith('savings')]
        if not sv: continue
        t=[x for x in b['tenors'] if x['days']==364][0]; y=yld(b,t); g=y-sv[0]['rate']
        if gap is None or g>gap[0]: gap=(g,k,y,sv[0]['rate'])
    if gap: parts.append(f"In {C[gap[1]]['name']}, the 364-day bill yields about {f(gap[2],1)}% against an average savings rate of {f(gap[3],1)}%.")
    return ' '.join(parts)
body=f'''<div class="mr">
<section class="subhero"><div><p class="eyebrow">AMB CASH &amp; YIELD</p><h1>Where is cash<br><i>earning more?</i></h1><p class="lead">Government bills and bank deposit rates for savers and investors in Nigeria, Ghana, Kenya, South Africa and Egypt, with the date and source on every figure.</p><p class="trust">✓ Latest official auctions &nbsp; ✓ Dates visible &nbsp; ✓ Deposit and bill rates kept separate</p></div><div class="subhero-brand"><img src="assets/africa-money-brief-logo.png" alt="Africa Money Brief"><span>AFRICA’S MARKETS,<br><b>DECODED.</b></span></div></section>
<section class="section" id="board"><div class="asof"><span class="pill gold">BOARD · {dl(D["as_of"])}</span><span>Each row shows its own dates below. Nothing here is a live quote.</span></div>
<div class="jump"><a href="#board">Compare</a><a href="#calc">Estimate earnings</a><a href="#ng">Nigeria</a><a href="#gh">Ghana</a><a href="#ke">Kenya</a><a href="#za">South Africa</a><a href="#eg">Egypt</a><a href="#read">How to read this</a></div>
<div class="heading"><div><p class="eyebrow">THE COMPARISON</p><h2>Bills vs inflation, by country</h2></div><p>Annualised bill yields from each country’s latest auction, set against the latest inflation reading AMB has verified.</p></div>{board}
<div style="margin-top:22px">{bars}</div>
<p class="take"><b>What stands out.</b> {takeaway()}</p></section>
<section class="section" id="calc"><div class="heading"><div><p class="eyebrow">ESTIMATE EARNINGS</p><h2>What would my money earn?</h2></div><p>Pick a bill or deposit from the board, enter an amount, and see the simple interest.</p></div>{calc}</section>
{secs}
<section class="section" id="read"><div class="heading"><div><p class="eyebrow">HOW TO READ THIS</p><h2>Compare like with like</h2></div></div><div class="how"><article><span class="pill gold">DISCOUNT VS YIELD</span><h3>Nigeria quotes a discount rate</h3><p>A 15.85% stop rate on a 364-day bill is a price discount. The money-on-money yield is higher, about {f(y364)}%. AMB converts so bills compare with deposits and with other countries.</p></article><article><span class="pill gold">AVERAGE VS OFFER</span><h3>System averages are not offers</h3><p>Ghana, Kenya and South Africa deposit figures are banking-system averages. A single bank’s rate can be higher or lower, depending on balance and tenor.</p></article><article><span class="pill gold">NOMINAL VS REAL</span><h3>Inflation and currency matter</h3><p>A high local-currency yield can lose value if inflation or the exchange rate moves against it. Check the FX page before comparing across countries.</p></article></div></section>
<section class="section"><div class="heading"><div><p class="eyebrow">FRESHNESS</p><h2>What is verified, and when</h2></div><p>Every date AMB relies on, so you can see what is current and what is waiting for a refresh.</p></div>{fresh}
<p class="fine">Indicative information only, not investment advice. Rates vary by institution, product, amount, tenor and date. Withholding tax and fees apply in several markets. <a href="methodology.html">Read our methodology →</a></p></section>
</div>'''

# ---- write region ----
p='money-rates.html'; page=open(p,encoding='utf-8').read()
pat=re.compile(r'(<!--AMB:money-->).*?(<!--/AMB:money-->)',re.S)
if not pat.search(page): sys.exit('RENDER ERROR: marker AMB:money missing')
if FORBIDDEN.search(body): sys.exit('RENDER ERROR: forbidden provider name')
open(p,'w',encoding='utf-8').write(pat.sub(lambda m:m.group(1)+body+m.group(2),page,count=1))
print('money page rendered, as_of',D['as_of'])
