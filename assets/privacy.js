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
    if (banner) { banner.hidden = false; banner.querySelector('button').focus(); }
  }
  function renderBanner() {
    var banner = document.createElement('section');
    banner.id = 'amb-consent-banner';
    banner.className = 'amb-consent-banner';
    banner.setAttribute('role', 'region');
    banner.setAttribute('aria-label', 'Cookie and analytics preferences');
    banner.innerHTML = '<div class="amb-consent-copy"><strong>Your privacy matters.</strong><p>With your permission, Africa Money Brief uses Google Analytics to understand visits and improve the website. Analytics is off unless you accept. <a href="' + (location.pathname.indexOf('/archive/') !== -1 ? '../' : '') + 'privacy.html">Read our Privacy &amp; Cookies Notice</a>.</p></div><div class="amb-consent-actions"><button type="button" data-amb-choice="rejected">Reject analytics</button><button type="button" class="amb-accept" data-amb-choice="accepted">Accept analytics</button></div>';
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
