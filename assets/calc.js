/* AMB earnings estimator. Rates are source-dated, not live. */
(function () {
  'use strict';
  var box = document.getElementById('amb-calc');
  if (!box) return;

  var product = box.querySelector('#cp');
  var amount = box.querySelector('#ca');
  var months = box.querySelector('#cm');
  var monthsWrap = box.querySelector('#cmw');
  var interest = box.querySelector('#ci');
  var summary = box.querySelector('#cs');
  var options = [];

  var meta = document.createElement('div');
  meta.id = 'amb-rate-meta';
  meta.style.cssText = 'font-size:12px;line-height:1.55;color:#aebfd1;margin-top:8px';
  var warning = document.createElement('div');
  warning.id = 'amb-rate-warning';
  warning.style.cssText = 'font-size:12px;line-height:1.55;color:#f5c84c;margin-top:6px';
  summary.insertAdjacentElement('afterend', meta);
  meta.insertAdjacentElement('afterend', warning);

  function fmt(n) {
    return n.toLocaleString('en-US', { maximumFractionDigits: 0 });
  }

  function billYield(bill, tenor) {
    if (bill.basis !== 'discount') return tenor.rate;
    var fraction = tenor.rate / 100 * tenor.days / 365;
    return fraction >= 1 ? NaN : (1 / (1 - fraction) - 1) * 365 / tenor.days * 100;
  }

  function daysOld(dateString) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString || '')) return null;
    var today = new Date();
    var utcToday = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
    var stamp = Date.parse(dateString + 'T00:00:00Z');
    return Number.isFinite(stamp) ? Math.max(0, Math.floor((utcToday - stamp) / 86400000)) : null;
  }

  function applicableRate(item, balance) {
    if (!item.tiers || !item.tiers.length) return item.rate;
    var tiers = item.tiers.slice().sort(function (a, b) { return a.min - b.min; });
    if (balance < tiers[0].min) return null;
    var rate = tiers[0].rate;
    tiers.forEach(function (tier) {
      if (balance >= tier.min) rate = tier.rate;
    });
    return rate;
  }

  function sourceInfo(item) {
    meta.textContent = 'Rate effective: ' + (item.date || 'not specified') +
      ' · Source: ' + (item.source || 'not specified') + '. ';
    if (item.url && /^https:\/\//.test(item.url)) {
      var link = document.createElement('a');
      link.href = item.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'View source ↗';
      link.style.color = '#f5c84c';
      meta.appendChild(link);
    }
  }

  function calculate() {
    if (!options.length) return;
    var item = options[Number(product.value)];
    if (!item) return;
    var balance = Number(amount.value);
    var period = item.days ? item.days / 365 : Math.max(1, Math.min(12, Number(months.value) || 1)) / 12;
    monthsWrap.hidden = Boolean(item.days);
    sourceInfo(item);

    var notices = [];
    var age = daysOld(item.date);
    if (age === null) notices.push('Rate date unavailable; verify before relying on this estimate.');
    else if (age > (item.days ? 14 : 30)) notices.push('OLDER DATA: rate is ' + age + ' days old. Check current rates before investing.');
    if (item.pending) notices.push('Primary-source verification is pending for this rate.');
    if (item.average) notices.push('Banking-system average, not a rate offered to an individual customer.');

    if (!Number.isFinite(balance) || balance <= 0) {
      interest.textContent = '—';
      summary.textContent = 'Enter a positive investment amount.';
    } else {
      var rate = applicableRate(item, balance);
      if (rate === null) {
        interest.textContent = 'Not eligible';
        summary.textContent = 'Published ' + item.label + ' tiers start at ' +
          item.currency + ' ' + fmt(item.tiers[0].min) + '. No interest estimate is available for this amount.';
      } else if (!Number.isFinite(rate) || rate < 0) {
        interest.textContent = '—';
        summary.textContent = 'Rate unavailable; please check the source.';
      } else {
        var earned = balance * rate / 100 * period;
        interest.textContent = item.currency + ' ' + fmt(earned);
        summary.textContent = (item.days ? 'Held to maturity (' + item.days + ' days)' :
          Math.max(1, Math.min(12, Number(months.value) || 1)) + ' month(s)') +
          ' on ' + item.currency + ' ' + fmt(balance) + ' at ' + rate.toFixed(2) +
          '% per year' + (item.tiers ? ' (balance-specific tier)' : '') + '.';
      }
    }
    warning.textContent = notices.join(' ');
    warning.hidden = !notices.length;
  }

  fetch('data/money-rates.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('Rate data request failed');
      return response.json();
    })
    .then(function (data) {
      Object.keys(data.countries || {}).forEach(function (key) {
        var country = data.countries[key];
        if (country.bills) {
          country.bills.tenors.forEach(function (tenor) {
            options.push({
              label: country.name + ' · ' + tenor.t + ' T-bill',
              currency: country.ccy,
              rate: billYield(country.bills, tenor),
              days: tenor.days,
              date: country.bills.auction,
              source: country.bills.src,
              url: country.bills.src_url,
              pending: /pending|relayed|secondary relay/i.test(country.bills.src || ''),
              average: false
            });
          });
        }
        if (country.deposits) {
          country.deposits.rows.forEach(function (row) {
            options.push({
              label: country.name + ' · ' + row.p,
              currency: country.ccy,
              rate: row.rate,
              tiers: row.tiers,
              days: null,
              date: country.deposits.date,
              source: country.deposits.src,
              url: country.deposits.src_url,
              pending: false,
              average: /average/i.test(country.deposits.kind || '') || /average/i.test(row.p)
            });
          });
        }
      });

      var defaultIndex = 0;
      options.forEach(function (item, index) {
        var option = document.createElement('option');
        option.value = String(index);
        var rateText = item.tiers && item.tiers.length
          ? Math.min.apply(null, item.tiers.map(function (t) { return t.rate; })).toFixed(2) +
            '–' + Math.max.apply(null, item.tiers.map(function (t) { return t.rate; })).toFixed(2) + '% (tiered)'
          : item.rate.toFixed(2) + '%';
        option.textContent = item.label + ' — ' + rateText;
        product.appendChild(option);
        if (item.label === 'Nigeria · 364-day T-bill') defaultIndex = index;
      });
      product.value = String(defaultIndex);
      calculate();
    })
    .catch(function () {
      interest.textContent = '—';
      summary.textContent = 'Rates could not be loaded. See the Money & Rates page.';
      warning.textContent = 'No calculation was performed because the rate dataset is unavailable.';
    });

  [product, amount, months].forEach(function (input) {
    input.addEventListener('input', calculate);
    input.addEventListener('change', calculate);
  });
})();
