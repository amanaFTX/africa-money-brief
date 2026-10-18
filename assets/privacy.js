/* AMB basic consent: no Google tag is loaded until analytics opt-in. */
(function () {
  'use strict';
  var KEY = 'amb_analytics_consent_v1';
  var ID = 'G-ZS3YZ0NVMK';
  var loaded = false;
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied'
  });
  window.gtag('set', 'allow_google_signals', false);
  window.gtag('set', 'allow_ad_personalization_signals', false);
  function readChoice() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function saveChoice(choice) {
    try { window.localStorage.setItem(KEY, choice); } catch (e) { /* choice lasts for this page */ }
  }
  function enableAnalytics() {
    if (loaded) return;
    loaded = true;
    window.gtag('consent', 'update', { analytics_storage: 'granted', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });
    window.gtag('js', new Date());
    window.gtag('config', ID, { allow_google_signals: false, allow_ad_personalization_signals: false });
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ID);
    document.head.appendChild(script);
  }
  function clearGaCookies() {
    document.cookie.split(';').forEach(function (part) {
      var name = part.split('=')[0].trim();
      if (!/^_ga(?:_|$)/.test(name)) return;
      var host = location.hostname;
      var domains = ['', host, '.' + host, 'africamoneybrief.com', '.africamoneybrief.com'];
      domains.forEach(function (domain) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + (domain ? '; domain=' + domain : '') + '; SameSite=Lax';
      });
    });
  }
  function setChoice(choice) {
    saveChoice(choice);
    if (choice === 'accepted') enableAnalytics();
    else {
      window.gtag('consent', 'update', { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });
      clearGaCookies();
      if (loaded) { window.location.reload(); return; }
    }
    var banner = document.getElementById('amb-consent-banner');
    if (banner) banner.hidden = true;
  }
  function showBanner() {
    var banner = document.getElementById('amb-consent-banner');
    if (banner) { banner.hidden = false; banner.querySelector('.amb-accept').focus(); }
  }
  function renderBanner() {
    var banner = document.createElement('section');
    banner.id = 'amb-consent-banner';
    banner.className = 'amb-consent-banner';
    banner.setAttribute('role', 'region');
    banner.setAttribute('aria-label', 'Cookie and analytics preferences');
    var base = location.pathname.indexOf('/archive/') !== -1 ? '../' : '';
    banner.innerHTML = '<div class="amb-consent-main"><div class="amb-consent-copy"><strong>This website uses cookies</strong><p>We use Google Analytics, only if you allow it, to understand visits and improve the website. Click &quot;OK&quot; to allow Google Analytics or click &quot;Reject&quot; to reject it. See our <a href="' + base + 'privacy.html">Privacy &amp; Cookies Notice</a>.</p></div><div class="amb-consent-actions"><button type="button" data-amb-choice="rejected">Reject</button><button type="button" class="amb-accept" data-amb-choice="accepted" aria-label="OK, accept analytics">OK</button></div></div><button type="button" class="amb-consent-more" aria-expanded="false" aria-controls="amb-consent-details">Show details <span aria-hidden="true">&rsaquo;</span></button><div class="amb-consent-details" id="amb-consent-details" hidden><ul><li><b>Necessary:</b> the site works without any cookies from us.</li><li><b>Analytics (optional, off by default):</b> Google Analytics counts visits and pages viewed. Ads and ad personalisation stay off.</li><li>You can change your choice at any time with <b>Cookie settings</b> in the footer.</li></ul></div>';
    var more = banner.querySelector('.amb-consent-more'), det = banner.querySelector('.amb-consent-details');
    more.addEventListener('click', function () {
      var open = det.hidden; det.hidden = !open; more.setAttribute('aria-expanded', String(open));
      more.firstChild.nodeValue = open ? 'Hide details ' : 'Show details ';
    });
    banner.addEventListener('click', function (e) {
      var button = e.target.closest('[data-amb-choice]');
      if (button) setChoice(button.getAttribute('data-amb-choice'));
    });
    document.body.appendChild(banner);
    banner.hidden = readChoice() === 'accepted' || readChoice() === 'rejected';
    document.addEventListener('click', function (e) {
      if (e.target.closest('[data-amb-cookie-settings]')) { e.preventDefault(); showBanner(); }
    });
  }
  if (readChoice() === 'accepted') enableAnalytics();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderBanner);
  else renderBanner();
})();
