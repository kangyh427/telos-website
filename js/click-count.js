/* 누름 세기(2026-11-27 · hq-nainote-dev · ND-014) · 개인정보 0
 * - 플레이 스토어로 가는 링크를 누르면 app_store_click (ND-006 과 같은 이름)
 *   link_position = 그 링크 referrer 의 utm_campaign (예: home_elder_top · kongdak_haru)
 * - 설치 안내 한 장(/install-parents/)으로 가는 링크를 누르면 install_guide_click
 *   link_position = 그 링크 주소의 utm_campaign (예: home_to_install)
 * - 이미 자기 세기가 있는 쪽(data-click-pos 가 붙은 링크)은 건드리지 않음(두 번 세지 않게)
 */
(function () {
  function cut(v) { return (v || '(none)').slice(0, 100); }

  function playPosition(url) {
    try {
      var ref = url.searchParams.get('referrer') || '';
      var inner = new URLSearchParams(ref);
      return cut(inner.get('utm_campaign'));
    } catch (err) { return '(none)'; }
  }

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || a.hasAttribute('data-click-pos')) return;
    if (typeof gtag !== 'function') return;
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return; }

    if (url.hostname === 'play.google.com') {
      gtag('event', 'app_store_click', {
        link_position: playPosition(url),
        app_id: cut(url.searchParams.get('id')),
        page_path: location.pathname,
        transport_type: 'beacon'
      });
    } else if (url.hostname === location.hostname && url.pathname.indexOf('/install-parents/') === 0) {
      gtag('event', 'install_guide_click', {
        link_position: cut(url.searchParams.get('utm_campaign')),
        page_path: location.pathname,
        transport_type: 'beacon'
      });
    }
  });
})();
