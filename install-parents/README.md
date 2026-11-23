# /install-parents/ · 부모님 폰에 나이노트 깔아 드리는 법 (ND-004 · 2026-11-23)

| 자리 | 꼬리표(referrer) |
|---|---|
| QR 그림 qr-elder.svg (부모님 앱) | utm_source=telos_web · utm_medium=qr · utm_campaign=install_guide |
| 단추 「이 화면이 부모님 폰이라면」 (부모님 앱) | utm_source=telos_web · utm_medium=web · utm_campaign=install_guide |
| 단추 「내 폰에 자녀 앱 받기」 (자녀 앱) | utm_source=telos_web · utm_medium=web · utm_campaign=install_guide_g |

QR 다시 만들기(외부 라이브러리 없음):

    python -I _tools/qr/qr_make.py "<주소>" install-parents/qr-elder.svg
    python -I _tools/qr/qr_check.py install-parents/qr-elder.svg.json   # MATCH True 여야 함 · .json 은 올리지 않음
