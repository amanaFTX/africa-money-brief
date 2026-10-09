#!/usr/bin/env python3
"""AMB site renderer. Renders index/fx/archive/data pages from data/fx/*.json (schema amb-fx-site/1).
Usage: python3 tools/render.py [--check]   (run from repo root; idempotent; fails on any validation error)
Inputs : data/fx/<YYYY-MM-DD>.json (schema 'amb-fx-site/1'), data/fx/index.json (edition list)
Outputs: data/fx/latest.json, data/fx/series.csv, and the <!--AMB:name-->...<!--/AMB:name--> regions of the HTML pages."""
import json,re,sys,glob,os,datetime as dt
FORBIDDEN=re.compile(r'aboki|osuwon|nairafx|ngnrates|nairarates|egrates|standard bank',re.I)
SYM={'USD':'US$','GBP':'£','EUR':'€'}
f=lambda x,d=2:f'{x:,.{d}f}'
def D(s): return dt.date.fromisoformat(s)
def dlabel(s): return D(s).strftime('%-d %b')
def die(m): print('RENDER ERROR:',m); sys.exit(1)
def load():
    eds={}
    for p in sorted(glob.glob('data/fx/2???-??-??.json')):
        j=json.load(open(p,encoding='utf-8'))
        if j.get('schema')!='amb-fx-site/1': continue
        raw=open(p,encoding='utf-8').read()
        if FORBIDDEN.search(raw): die(f'forbidden provider name in {p}')
        validate(j,p); eds[j['date']]=j
    if not eds: die('no schema amb-fx-site/1 editions found')
    return eds
def validate(j,p):
    for c in ['USD','GBP','EUR']:
        v=j['nigeria'].get(c) or die(f'{p}: missing Nigeria {c}')
        for k in ['parallel_buy_low','parallel_buy_high','parallel_sell_low','parallel_sell_high','official_selling_rate','official_rate_date','official_basis','premium_pct']:
            if v.get(k) is None: die(f'{p}: {c} missing {k}')
        if not v['parallel_buy_low']<=v['parallel_buy_high'] or not v['parallel_sell_low']<=v['parallel_sell_high']: die(f'{p}: {c} range order')
        bm=(v['parallel_buy_low']+v['parallel_buy_high'])/2; sm=(v['parallel_sell_low']+v['parallel_sell_high'])/2
        if bm>sm: die(f'{p}: {c} buy mid above sell mid')
        w=max(v['parallel_buy_high']-v['parallel_buy_low'],v['parallel_sell_high']-v['parallel_sell_low'])
        if w>max(20,0.015*(bm+sm)/2) and not v.get('range_flag_acknowledged'): die(f'{p}: {c} range width gate ({w})')
        calc=round((bm/v['official_selling_rate']-1)*100,2)
        if abs(calc-v['premium_pct'])>0.005: die(f'{p}: {c} premium_pct {v["premium_pct"]} != recomputed {calc}')
        v['_bm']=bm; v['_sm']=sm; v['_mid']=(bm+sm)/2
        if v.get('cbn_check') and v['cbn_check']['pct']>0.3: die(f'{p}: {c} derived-vs-CBN check {v["cbn_check"]["pct"]}% > 0.3%')
    for n,m in j['markets'].items():
        if not m.get('asof') or set(m['rates'])!={'USD','GBP','EUR'}: die(f'{p}: market {n} incomplete')
CBNL="<a href='https://www.cbn.gov.ng/rates/ExchRateByCurrency.html'>CBN ↗</a>"
def basis(c,v):
    if v['official_basis']=='CBN selling rate (NFEM)':
        return f"<p class='basis'>CBN NFEM rate (volume-weighted; the CBN’s official selling rate for the day), {dlabel(v['official_rate_date'])}. The premium uses this rate. Source: {CBNL}</p>"
    chk=v.get('cbn_check'); ck=f" Check: the CBN’s own {dlabel(chk['date'])} selling rate was ₦{f(chk['rate'])} ({chk['pct']:.2f}% away)." if chk else ''
    return f"<p class='basis'>Derived official rate, {dlabel(v['official_rate_date'])}: {v.get('official_inputs','')} = ₦{f(v['official_selling_rate'])}.{ck} Sources: {CBNL} · <a href='https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html'>ECB ↗</a></p>"
def panel(c,v):
    sell=f"₦{v['parallel_sell_low']:,}" if v['parallel_sell_low']==v['parallel_sell_high'] else f"₦{v['parallel_sell_low']:,}–{v['parallel_sell_high']:,}"
    lab='NFEM rate' if v['official_basis'].startswith('CBN selling') else 'derived'
    return f'''<div class="panel"><div class="ph"><h3>{c} → NGN <small>per {SYM[c]}1</small></h3><span class="prem big">+{v['premium_pct']:.2f}%</span></div><div class="grid4"><div><small>CBN {lab} · {dlabel(v['official_rate_date'])}</small><b>₦{f(v['official_selling_rate'])}</b></div><div><small>Parallel buy</small><b>₦{v['parallel_buy_low']:,}–{v['parallel_buy_high']:,}</b></div><div><small>Parallel sell</small><b>{sell}</b></div><div><small>AMB midpoint</small><b class="gold">₦{f(v['_mid'])}</b></div></div>{basis(c,v)}</div>'''
def chip(n): return '<span class="chip ok">Today</span>' if n==0 else f'<span class="chip {"warn" if n>1 else "ok"}">{n} day{"s" if n>1 else ""} old</span>'
def mtable(j):
    ed=D(j['date']); rows=''
    for n,m in j['markets'].items():
        rows+=f'<tr><td>{n}</td>'+''.join(f"<td>{m['symbol']}{m['rates'][c]:,.4f}</td>" for c in ['USD','GBP','EUR'])+f"<td>{dlabel(m['asof'])} {chip((ed-D(m['asof'])).days)}</td></tr>"
    return f'<div class="tw"><table><thead><tr><th>Market</th><th>USD</th><th>GBP</th><th>EUR</th><th>As of</th></tr></thead><tbody>{rows}</tbody></table></div>'
def flagship(j,latest=True):
    sfx=' · '+j['label_suffix'].upper() if j.get('label_suffix') else ''
    note=f" <b>{j['label_suffix']} edition:</b> {j['correction_note']}" if j.get('correction_note') else ''
    eid=f"flagship-{j['date']}"
    return f'''<section class="section" id="{eid}"><p class="eyebrow">FX FLAGSHIP · EDITION {dlabel(j['date']).upper()} {D(j['date']).year}{sfx}</p><h2 class="h2s" style="margin-top:8px">Nigeria — official vs parallel</h2>
<p class="lead">Local currency per one unit of foreign currency. Every figure carries its effective date.{note}</p>
{''.join(panel(c,j['nigeria'][c]) for c in ['USD','GBP','EUR'])}
<p class="fine">Premium = parallel buying midpoint ÷ CBN selling rate − 1 (buy at the CBN, sell in the parallel market). Where the CBN’s own GBP and EUR rows lag, official rates are derived and the inputs shown. Parallel observations: aggregated from multiple independent market sources; rates vary by location and transaction size. Indicative only; not FX advice.</p>
<h2 class="h2s">Africa cross-markets — official rates</h2>{mtable(j)}
<p class="fine">{j.get('markets_note','Reference values as published by each central bank or authorized institution, with their effective dates.')} Primary sources: <a href="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html">CBN</a> · <a href="https://www.bog.gov.gh/treasury-and-the-markets/daily-interbank-fx-rates/">Bank of Ghana</a> · <a href="https://www.centralbank.go.ke/cbk-indicative-rates/">CBK</a> · <a href="https://www.cbe.org.eg/en/economic-research/statistics/cbe-exchange-rates">CBE</a>.</p>
<div class="btns"><a class="btn" href="data/fx/{j['date']}.json">Download this edition (JSON)</a><a class="ghost" href="data/fx/series.csv">CSV</a><a class="ghost" href="archive.html">All editions</a></div></section>'''
def earlier(eds,latest):
    out=''
    for d in sorted(eds,reverse=True):
        if d==latest: continue
        j=eds[d]; out+=f'<details id="flagship-{d}"><summary>{dlabel(d)} · FX Flagship</summary><div class="v2"><section class="section">{flagship(j,False).split(">",1)[1].rsplit("</section>",1)[0]}</section></div></details>'
    return out
def board(j):
    rows=''.join(f"<div class=\"r\"><div>{c}/NGN<small>{'CBN NFEM' if v['official_basis'].startswith('CBN selling') else 'Derived'} ₦{f(v['official_selling_rate'])} · {dlabel(v['official_rate_date'])}</small></div><strong>₦{f(v['_bm'])} <span class=\"prem\" style=\"color:#64e2a6;font-size:14px\">+{v['premium_pct']:.2f}%</span></strong></div>" for c,v in ((c,j['nigeria'][c]) for c in ['USD','GBP','EUR']))
    sfx=' (corrected)' if j.get('label_suffix') else ''
    return f'<div class="board"><div class="boardtop"><span>NIGERIA · PARALLEL BUY MIDPOINT</span><span class="live">EDITION {dlabel(j["date"]).upper()}</span></div><div id="mini">{rows}</div><p id="verified">Premium = parallel buying midpoint ÷ CBN selling rate − 1. Edition {dlabel(j["date"])}{sfx}. Indicative only.</p></div>'
def glance(j):
    m=''.join(f"<div class=\"metric\"><small>{c} / NGN</small><strong>+{v['premium_pct']:.2f}%</strong><span>Parallel buy mid ₦{f(v['_bm'])} vs CBN ₦{f(v['official_selling_rate'])}</span></div>" for c,v in ((c,j['nigeria'][c]) for c in ['USD','GBP','EUR']))
    sfx=' (corrected)' if j.get('label_suffix') else ''
    return f'<div class="v2"><section class="section"><div class="heading"><div><p class="eyebrow">TODAY AT A GLANCE</p><h2>Premium: parallel buy vs CBN selling rate</h2></div><p>Edition {dlabel(j["date"])} {D(j["date"]).year}{sfx}. CBN NFEM rate for USD; GBP and EUR as dated. <a href="fx.html" style="color:var(--gold)">Full FX brief →</a></p></div><div class="dashgrid">{m}<div class="metric"><small>Coverage</small><strong>5 markets</strong><span>NG · GH · KE · ZA · EG</span></div></div></section></div>'
def archive(idx):
    def row(e):
        k='Flagship' if 'Flagship' in e['type'] else 'Early Look'
        lab='Structured dataset' if e.get('json') else 'Page only · dataset not published'
        links=f'<a href="{e["url"]}">View</a>'+(f'<a href="{e["json"]}">JSON</a>' if e.get('json') else '')
        return f'<div class="ai" data-t="{k}"><span class="ad">{D(e["date"]).strftime("%-d %b %Y")}</span><div><b>{e["type"]}</b><br><small>{lab}</small></div><div class="al">{links}</div></div>'
    return ''.join(row(e) for e in sorted(idx['editions'],key=lambda e:(e['date'],e['type']),reverse=True))
def datalatest(j):
    return f'<article class="card feature"><span class="tag">LATEST · {j["date"]}</span><h3>FX Flagship dataset</h3><p><a href="data/fx/latest.json" style="color:var(--gold)">JSON</a> · <a href="data/fx/series.csv" style="color:var(--gold)">CSV</a> · <a href="data/fx/{j["date"]}.json" style="color:var(--gold)">dated copy</a></p></article>'
def series(eds):
    out='date,pair,market,rate_type,low,high,mid,official,premium_pct,asof\n'
    for d in sorted(eds):
        j=eds[d]
        for c in ['USD','GBP','EUR']:
            v=j['nigeria'][c]
            out+=f"{d},{c}/NGN,Nigeria,parallel_buy,{v['parallel_buy_low']},{v['parallel_buy_high']},{v['_bm']},,,{d}\n{d},{c}/NGN,Nigeria,parallel_sell,{v['parallel_sell_low']},{v['parallel_sell_high']},{v['_sm']},,,{d}\n{d},{c}/NGN,Nigeria,amb_mid,,,{v['_mid']},{v['official_selling_rate']},{v['premium_pct']},{v['official_rate_date']}\n"
        for n,m in j['markets'].items():
            for c,x in m['rates'].items(): out+=f"{d},{c}/{n[:3].upper()},{n},official,,,{x},{x},,{m['asof']}\n"
    return out
def region(path,name,new):
    s=open(path,encoding='utf-8').read()
    pat=re.compile(r'(<!--AMB:%s-->).*?(<!--/AMB:%s-->)'%(name,name),re.S)
    if not pat.search(s): die(f'marker {name} missing in {path}')
    t=pat.sub(lambda m:m.group(1)+new+m.group(2),s,count=1)
    if FORBIDDEN.search(new): die(f'forbidden name in rendered {name}')
    open(path,'w',encoding='utf-8').write(t)

def load_early():
    out={}
    for p in sorted(glob.glob('data/fx/early-2???-??-??.json')):
        raw=open(p,encoding='utf-8').read()
        if FORBIDDEN.search(raw): die(f'forbidden provider name in {p}')
        j=json.loads(raw)
        if j.get('schema')!='amb-fx-early/1': continue
        for c in ['USD','GBP','EUR']:
            v=j['nigeria'].get(c) or die(f'{p}: missing Nigeria {c}')
            for k in ['official_selling_rate','official_rate_date','official_basis']:
                if v.get(k) is None: die(f'{p}: {c} missing {k}')
            if v.get('parallel_buy_low') is not None:
                bl,bh,sl,sh=[v.get(k) for k in ['parallel_buy_low','parallel_buy_high','parallel_sell_low','parallel_sell_high']]
                if None in (bl,bh,sl,sh) or bl>bh or sl>sh: die(f'{p}: {c} parallel range incomplete/ordered wrongly')
                bm=(bl+bh)/2; sm=(sl+sh)/2
                if bm>sm: die(f'{p}: {c} buy mid above sell mid')
                if max(bh-bl,sh-sl)>max(20,0.015*(bm+sm)/2): die(f'{p}: {c} range width gate')
                v['_prem']=round((bm/v['official_selling_rate']-1)*100,2)
                if v.get('premium_pct') is not None and abs(v['_prem']-v['premium_pct'])>0.005: die(f'{p}: {c} premium mismatch')
            if v.get('cbn_check') and v['cbn_check']['pct']>0.3: die(f'{p}: {c} derived-vs-CBN check failed')
        for n,m in j['markets'].items():
            if not m.get('asof') or set(m['rates'])!={'USD','GBP','EUR'}: die(f'{p}: market {n} incomplete')
        out[j['date']]=j
    return out
def early_block(j):
    rows=''
    for c in ['USD','GBP','EUR']:
        v=j['nigeria'][c]
        if v.get('parallel_buy_low') is not None:
            par=f"₦{v['parallel_buy_low']:,}–{v['parallel_buy_high']:,} / ₦{v['parallel_sell_low']:,}–{v['parallel_sell_high']:,}"; pr=f"+{v['_prem']:.2f}%"
        else: par='Not sourced'; pr='—'
        rows+=f"<tr><td>{c}</td><td>₦{f(v['official_selling_rate'])} <small>({dlabel(v['official_rate_date'])}, {'CBN selling' if v['official_basis'].startswith('CBN') else 'derived'})</small></td><td>{par}</td><td class=\"prem\">{pr}</td></tr>"
    return f"""<details id="early-look-{j['date']}" open><summary>{dlabel(j['date'])} · Early Look (pre-market)</summary><section class="section"><p class="eyebrow">FX EARLY LOOK · {dlabel(j['date']).upper()} {D(j['date']).year} · PRE-MARKET</p><p class="lead">{j.get('headline','Previous-close and overnight reference only; not live opening quotes. Each figure carries its own effective date.')}</p>
<div class="tw"><table><thead><tr><th>Currency</th><th>Nigeria official</th><th>Parallel buy / sell</th><th>Premium</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="fine">{j.get('nigeria_note','Premium = parallel buying midpoint ÷ CBN selling rate − 1. Parallel observations: aggregated from multiple independent market sources; indicative only.')}</p>
<h3 style="margin:22px 0 10px">Africa cross-markets</h3>{mtable(j)}
<p class="fine">{j.get('markets_note','Latest published reference values with their effective dates.')} Informational only; not financial or FX advice. The Flagship edition follows after verification.</p></section></details>"""

def main():
    eds=load(); latest=max(eds); j=eds[latest]
    early=load_early()
    idx=json.load(open('data/fx/index.json',encoding='utf-8'))
    have={(e['date'],e['type']) for e in idx['editions']}
    for d in eds:
        if (d,'FX Flagship') not in have and not any(e['date']==d and e['type'].startswith('FX Flagship') for e in idx['editions']): idx['editions'].append({'date':d,'type':'FX Flagship','url':f'fx.html#flagship-{d}','json':f'data/fx/{d}.json'})
    for d in early:
        if not any(e['date']==d and e['type']=='Early Look' for e in idx['editions']): idx['editions'].append({'date':d,'type':'Early Look','url':f'fx.html#early-look-{d}','json':f'data/fx/early-{d}.json'})
    for e in idx['editions']:
        if e.get('json') and not os.path.exists(e['json']): die(f'index lists missing file {e["json"]}')
    json.dump(idx,open('data/fx/index.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
    clean=lambda x:{k:(clean(v) if isinstance(v,dict) else v) for k,v in x.items() if not k.startswith('_')}
    json.dump(clean(j),open('data/fx/latest.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
    open('data/fx/series.csv','w').write(series(eds))
    region('index.html','board',board(j)); region('index.html','glance',glance(j))
    region('fx.html','flagship',flagship(j)); region('fx.html','earlier',earlier(eds,latest)+''.join(early_block(early[d]).replace(' open>','>',1) for d in sorted(early,reverse=True) if d!=max(early)  or max(early)<latest))
    el=max(early) if early else None
    region('fx.html','early-latest',early_block(early[el]).replace('<details','<div class="v2"><details',1).replace('</details>','</details></div>') if el and el>=latest else '')
    region('archive.html','archive-list',archive(idx)); region('data.html','data-latest',datalatest(j))
    print('rendered edition',latest,'| editions with data:',len(eds))
main()
