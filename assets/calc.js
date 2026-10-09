/* AMB earnings estimator: reads data/money-rates.json (single source of truth for the Money & Rates page). */
(function(){
  var box=document.getElementById('amb-calc'); if(!box) return;
  var p=box.querySelector('#cp'),a=box.querySelector('#ca'),m=box.querySelector('#cm'),w=box.querySelector('#cmw');
  var O=[];
  function yld(b,t){ if(b.basis==='discount'){var d=t.rate/100,n=t.days;return ((1/(1-d*n/365))-1)*365/n*100} return t.rate }
  function fmt(n){return n.toLocaleString('en-US',{maximumFractionDigits:0})}
  function run(){
    if(!O.length) return;
    var o=O[+p.value],amt=parseFloat(a.value)||0,mo=o.d?o.d/365*12:Math.min(12,Math.max(1,parseInt(m.value)||1));
    w.hidden=!!o.d;
    box.querySelector('#ci').textContent=o.c+' '+fmt(amt*o.r/100*mo/12);
    box.querySelector('#cs').textContent=(o.d?'Held to maturity ('+o.d+' days)':mo+' month'+(mo>1?'s':''))+' on '+o.c+' '+fmt(amt)+' at '+o.r.toFixed(2)+'% a year';
  }
  fetch('data/money-rates.json').then(function(r){return r.json()}).then(function(D){
    Object.keys(D.countries).forEach(function(k){
      var c=D.countries[k];
      if(c.bills) c.bills.tenors.forEach(function(t){O.push({l:c.name+' · '+t.t+' T-bill',c:c.ccy,r:Math.round(yld(c.bills,t)*100)/100,d:t.days})});
      if(c.deposits) c.deposits.rows.forEach(function(r){O.push({l:c.name+' · '+r.p,c:c.ccy,r:r.rate,d:null})});
    });
    var def=0;O.forEach(function(o,i){var e=document.createElement('option');e.value=i;e.textContent=o.l+' — '+o.r.toFixed(2)+'%';p.appendChild(e);if(o.l==='Nigeria · 364-day T-bill')def=i});
    p.value=def;run();
  }).catch(function(){box.querySelector('#cs').textContent='Rates could not be loaded. See the Money & Rates page.'});
  [p,a,m].forEach(function(e){e.addEventListener('input',run)});
})();
