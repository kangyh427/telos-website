/*
 * 파일명: js/referrer-carry.js
 * 설명: 쪽 주소 꼬리표를 플레이 설치 꼬리표로 옮겨 붙임(요청 ND-009 · 2026-11-26 · hq-nainote-dev)
 *  - 쪽 주소에 utm_source · utm_content 가 있으면 그 둘을 이어 한 값으로 만든다
 *      예: ?utm_source=x&utm_content=1125x  →  x_1125x
 *          ?utm_source=kakao_share           →  kakao_share
 *          ?utm_content=1125x                →  1125x
 *  - 그 값을 이 쪽의 구글 플레이 링크 referrer 안 utm_content 로 넣는다
 *    (앱이 설치 표 install_attribution.utm_content 에 그대로 적음 · ND-003)
 *  - 이 쪽에서 /install-parents/ 로 가는 링크에는 utm_content 로 이어 붙여, 다음 쪽에서도 끊기지 않게 한다
 *  - 값이 없으면 아무것도 바꾸지 않는다(지금 그대로)
 *  - 글자는 영문 · 숫자 · _ · - 만 남기고 100자까지 · 개인정보 0 · 입력 칸 0
 * 쓰는 법: <script src="/js/referrer-carry.js"></script> 를 링크보다 아래(쪽 끝)에 둔다
 */
(function () {
  'use strict';

  function clean(v) {
    return (v || '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 100);
  }

  function carryValue(search) {
    var q = new URLSearchParams(search || '');
    var src = clean(q.get('utm_source'));
    var content = clean(q.get('utm_content'));
    if (src && content) return (src + '_' + content).slice(0, 100);
    return content || src;
  }

  function withPlayContent(href, value) {
    var u = new URL(href);
    var ref = new URLSearchParams(u.searchParams.get('referrer') || '');
    ref.set('utm_content', value);
    u.searchParams.set('referrer', ref.toString());
    return u.toString();
  }

  function withPageContent(href, value) {
    var u = new URL(href, location.href);
    if (u.searchParams.get('utm_content')) return href;
    u.searchParams.set('utm_content', value);
    return u.pathname + u.search + u.hash;
  }

  function run() {
    var value = carryValue(location.search);
    if (!value) return;
    var links = document.querySelectorAll('a[href]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      var href = a.getAttribute('href');
      try {
        if (/^https:\/\/play\.google\.com\/store\/apps\/details\?/.test(href)) {
          a.setAttribute('href', withPlayContent(href, value));
        } else if (/^\/install-parents\/(\?|$)/.test(href)) {
          a.setAttribute('href', withPageContent(href, value));
        }
      } catch (e) { /* 주소가 깨졌으면 그 링크는 그대로 둠 */ }
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', run);
    } else {
      run();
    }
  }

  // 시험용(node) · 브라우저에서는 쓰지 않음
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { carryValue: carryValue, withPlayContent: withPlayContent, clean: clean };
  }
})();
