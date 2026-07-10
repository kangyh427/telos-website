/*
================================================================================
 파일명: js/main.js
 저장소 경로: kangyh427/telos-website/js/main.js
 설명: 텔로스 케어 랜딩 인터랙션 (헤더 스크롤 · 모바일 네비 · 문의 모달 · 리빌)
 버전: 2.0.0
 작성일: 2026.07.10
 변경이력:
   - 2026.07.10 (v2.0.0): 케어 랜딩 전용으로 재작성.
                          / 기존 index.html 인라인 모달 스크립트를 본 파일로 통합
                          / 문의 트리거를 .js-contact-open 다중 바인딩으로 일반화
                          / data-contact-topic(general/b2g/waitlist)별 모달 안내 문구 분기
                          / IntersectionObserver 기반 스크롤 리빌 추가(폴백 포함)
 설계 원칙:
   - 각 기능을 독립 모듈(IIFE)로 분리 → 한 기능이 실패해도 다른 기능에 영향 없음
   - 필수 DOM 요소가 없으면 해당 모듈만 조용히 종료(방어적 프로그래밍)
================================================================================
*/
(function () {
    'use strict';

    /* --------------------------------------------------------- */
    /* 모듈 1) 헤더 스크롤 상태 (배경/색상 전환)                  */
    /* --------------------------------------------------------- */
    (function headerScroll() {
        var header = document.getElementById('header');
        if (!header) return;
        var THRESHOLD = 40;
        function onScroll() {
            if (window.scrollY > THRESHOLD) header.classList.add('scrolled');
            else header.classList.remove('scrolled');
        }
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    })();

    /* --------------------------------------------------------- */
    /* 모듈 2) 모바일 네비 토글 (열기/닫기 · 접근성 aria)          */
    /* --------------------------------------------------------- */
    (function mobileNav() {
        var toggle = document.getElementById('navToggle');
        var nav = document.getElementById('nav');
        if (!toggle || !nav) return;

        function setOpen(open) {
            nav.classList.toggle('active', open);
            toggle.classList.toggle('active', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
        }
        toggle.addEventListener('click', function () {
            setOpen(!nav.classList.contains('active'));
        });
        // 메뉴 내 링크 클릭 시 자동 닫기
        nav.addEventListener('click', function (e) {
            if (e.target.closest('a')) setOpen(false);
        });
        // ESC 로 닫기
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && nav.classList.contains('active')) setOpen(false);
        });
    })();

    /* --------------------------------------------------------- */
    /* 모듈 3) 문의 모달 (수신경로: contact@telos.it.kr)          */
    /*  - .js-contact-open 요소 클릭 시 열림                       */
    /*  - data-contact-topic 값에 따라 안내 문구 분기             */
    /*  - 닫기: X / 배경 / ESC, 이메일 클립보드 복사              */
    /* --------------------------------------------------------- */
    (function contactModal() {
        var modal    = document.getElementById('contactModal');
        var btnClose = document.getElementById('contactModalClose');
        var btnCopy  = document.getElementById('contactModalCopyBtn');
        var titleEl  = document.getElementById('contactModalTitle');
        var descEl   = document.getElementById('contactModalDesc');
        var triggers = document.querySelectorAll('.js-contact-open');

        if (!modal || !btnClose || !btnCopy || !descEl || triggers.length === 0) return;

        var EMAIL = 'contact@telos.it.kr';
        var lastTrigger = null;

        // 토픽별 모달 안내 문구 (기존 수신경로는 동일, 문맥만 안내)
        var TOPICS = {
            general:  { title: '문의하기',        desc: '아래 이메일 주소로 문의해 주세요. 어떤 주제든 환영합니다.' },
            b2g:      { title: '도입 문의',        desc: '지자체·복지관 도입 문의는 아래 이메일로 보내 주세요. 소속·이용 규모를 함께 남겨 주시면 빠르게 안내드립니다.' },
            waitlist: { title: '보호자 대기자 등록', desc: '출시 소식과 대기자 안내를 받으시려면 아래 이메일로 연락처를 남겨 주세요.' }
        };

        function openModal(trigger) {
            lastTrigger = trigger || null;
            var topic = (trigger && trigger.getAttribute('data-contact-topic')) || 'general';
            var t = TOPICS[topic] || TOPICS.general;
            if (titleEl) titleEl.textContent = t.title;
            descEl.textContent = t.desc;

            modal.classList.add('is-open');
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            setTimeout(function () { btnClose.focus(); }, 50);
        }

        function closeModal() {
            modal.classList.remove('is-open');
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
            resetCopy();
            if (lastTrigger && typeof lastTrigger.focus === 'function') lastTrigger.focus();
        }

        function resetCopy() {
            btnCopy.textContent = '복사';
            btnCopy.classList.remove('is-copied');
        }

        function markCopied() {
            btnCopy.textContent = '복사됨 ✓';
            btnCopy.classList.add('is-copied');
            setTimeout(resetCopy, 2000);
        }

        function copyEmail() {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(EMAIL).then(markCopied).catch(fallbackCopy);
            } else {
                fallbackCopy();
            }
        }
        function fallbackCopy() {
            try {
                var ta = document.createElement('textarea');
                ta.value = EMAIL; ta.setAttribute('readonly', '');
                ta.style.position = 'absolute'; ta.style.left = '-9999px';
                document.body.appendChild(ta);
                ta.select(); document.execCommand('copy');
                document.body.removeChild(ta);
                markCopied();
            } catch (e) { btnCopy.textContent = '복사 실패'; }
        }

        // 트리거 바인딩(여러 개)
        triggers.forEach(function (el) {
            el.addEventListener('click', function () { openModal(el); });
        });
        btnClose.addEventListener('click', closeModal);
        btnCopy.addEventListener('click', copyEmail);
        modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
        });
    })();

    /* --------------------------------------------------------- */
    /* 모듈 4) 스크롤 리빌 (.reveal → .is-visible)                */
    /*  - IntersectionObserver 미지원 시 전체 즉시 표시(폴백)     */
    /* --------------------------------------------------------- */
    (function scrollReveal() {
        var items = document.querySelectorAll('.reveal');
        if (items.length === 0) return;

        if (!('IntersectionObserver' in window)) {
            items.forEach(function (el) { el.classList.add('is-visible'); });
            return;
        }
        var io = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

        items.forEach(function (el) { io.observe(el); });
    })();

})();
