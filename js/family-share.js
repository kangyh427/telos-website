/*
 * 파일명: js/family-share.js
 * 설명: 「가족 단톡방에 이 안내 보내기」 단추(요청 ND-007 · 2026-11-25 · hq-nainote-dev)
 *  - 폰: 브라우저 공유 창(navigator.share · 카카오톡을 고를 수 있음)
 *  - 공유 창이 없으면 주소를 복사하고 「주소 복사됨」을 보여 줌
 *  - 누르면 구글 애널리틱스 이벤트 share_click 하나(ND-006 과 같은 태그 G-RXELWTCRMJ)
 *  - 카카오 SDK · 앱 키 · 로그인 쓰지 않음 · 개인정보 0 · 입력 칸 0
 * 쓰는 법: <button type="button" data-share-pos="자리 이름">…</button>
 *         + 같은 부모 안 <p class="share-status" aria-live="polite"></p>
 */
(function () {
  'use strict';

  var SHARE_URL = 'https://www.telos.it.kr/install-parents/?utm_source=kakao_share&utm_medium=social&utm_campaign=v013';
  var SHARE_TITLE = '부모님 폰에 나이노트 깔아 드리는 법';
  var SHARE_TEXT = '부모님 댁에서 이 화면을 띄우고 부모님 폰 카메라로 QR 코드를 비추면 됩니다. 나이노트는 무료입니다.';

  var q = new URLSearchParams(location.search);
  function tag(name) { return (q.get(name) || '(none)').slice(0, 100); }

  function send(pos, method) {
    if (typeof gtag !== 'function') return;
    gtag('event', 'share_click', {
      link_position: pos,
      share_method: method,
      utm_content: tag('utm_content'),
      page_utm_campaign: tag('utm_campaign'),
      transport_type: 'beacon'
    });
  }

  function say(btn, msg) {
    var box = btn.parentNode && btn.parentNode.querySelector('.share-status');
    if (box) box.textContent = msg;
  }

  function copyFallback(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  function copy(btn) {
    var line = SHARE_TEXT + ' ' + SHARE_URL;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(line).then(function () {
        say(btn, '주소 복사됨 · 가족 단톡방에 붙여 넣어 주세요.');
      }, function () {
        say(btn, copyFallback(line) ? '주소 복사됨 · 가족 단톡방에 붙여 넣어 주세요.' : '복사가 안 됩니다. 이 주소를 보내 주세요: ' + SHARE_URL);
      });
    } else {
      say(btn, copyFallback(line) ? '주소 복사됨 · 가족 단톡방에 붙여 넣어 주세요.' : '복사가 안 됩니다. 이 주소를 보내 주세요: ' + SHARE_URL);
    }
  }

  document.addEventListener('click', function (e) {
    var btn = e.target && e.target.closest ? e.target.closest('[data-share-pos]') : null;
    if (!btn) return;
    e.preventDefault();
    var pos = btn.getAttribute('data-share-pos');
    if (navigator.share) {
      send(pos, 'share');
      navigator.share({ title: SHARE_TITLE, text: SHARE_TEXT, url: SHARE_URL }).catch(function (err) {
        // 사람이 공유 창을 닫은 것(AbortError)은 그대로 둠 · 그 밖의 실패만 복사로
        if (!err || err.name !== 'AbortError') copy(btn);
      });
    } else {
      send(pos, 'copy');
      copy(btn);
    }
  });
})();
