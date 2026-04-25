/**
 * ================================================================================
 * 파일명: js/main.js
 * 설명: 주식회사 텔로스 (TELOS) 공식 홈페이지 JavaScript
 * 버전: 1.0.0
 * 작성일: 2026.04.25
 * 기능:
 *   1. 스크롤 시 헤더 스타일 변경
 *   2. 모바일 메뉴 토글
 *   3. 부드러운 스크롤 (네비게이션 클릭 시)
 *   4. 메뉴 클릭 시 모바일 메뉴 닫기
 * 변경이력:
 *   - 2026.04.25 (v1.0.0): 초기 버전 작성
 * ================================================================================
 */

(function() {
    'use strict';
    
    // ========================================================
    // DOM 요소 선택 (전역 캐싱으로 성능 최적화)
    // ========================================================
    const header = document.getElementById('header');
    const nav = document.getElementById('nav');
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.querySelectorAll('.nav-list a');
    
    // ========================================================
    // 1. 스크롤 시 헤더 스타일 변경
    // ========================================================
    /**
     * 스크롤 위치에 따라 헤더에 'scrolled' 클래스 추가/제거
     * 100px 이상 스크롤 시 헤더 배경 표시
     */
    let scrollTimer = null;
    function handleScroll() {
        if (scrollTimer !== null) {
            clearTimeout(scrollTimer);
        }
        
        // 디바운싱: 스크롤 이벤트 부하 감소
        scrollTimer = setTimeout(function() {
            if (window.scrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }, 10);
    }
    
    // passive 옵션으로 스크롤 성능 개선
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // ========================================================
    // 2. 모바일 메뉴 토글
    // ========================================================
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            nav.classList.toggle('active');
            navToggle.classList.toggle('active');
            
            // 접근성: aria-label 업데이트
            const isActive = nav.classList.contains('active');
            navToggle.setAttribute('aria-label', isActive ? '메뉴 닫기' : '메뉴 열기');
            
            // 모바일 메뉴 열렸을 때 body 스크롤 잠금
            if (isActive) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
    }
    
    // ========================================================
    // 3. 네비게이션 링크 클릭 시 모바일 메뉴 자동 닫기
    // ========================================================
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (nav.classList.contains('active')) {
                nav.classList.remove('active');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-label', '메뉴 열기');
                document.body.style.overflow = '';
            }
        });
    });
    
    // ========================================================
    // 4. 외부 클릭 시 모바일 메뉴 닫기
    // ========================================================
    document.addEventListener('click', function(event) {
        const isClickInsideNav = nav.contains(event.target);
        const isClickOnToggle = navToggle.contains(event.target);
        
        if (!isClickInsideNav && !isClickOnToggle && nav.classList.contains('active')) {
            nav.classList.remove('active');
            navToggle.classList.remove('active');
            navToggle.setAttribute('aria-label', '메뉴 열기');
            document.body.style.overflow = '';
        }
    });
    
    // ========================================================
    // 5. ESC 키로 모바일 메뉴 닫기 (접근성)
    // ========================================================
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && nav.classList.contains('active')) {
            nav.classList.remove('active');
            navToggle.classList.remove('active');
            navToggle.setAttribute('aria-label', '메뉴 열기');
            document.body.style.overflow = '';
        }
    });
    
    // ========================================================
    // 6. 페이지 로드 시 초기 상태 확인
    // ========================================================
    // 페이지 새로고침 시 스크롤 위치에 따라 헤더 스타일 적용
    window.addEventListener('load', function() {
        handleScroll();
    });
    
})();
