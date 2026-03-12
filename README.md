# HDMI 연결 도우미

선생님 노트북과 교실 TV 연결 문제를 즉시 해결하는 Windows 프로그램.

## 기능
- HDMI 연결 상태 자동 진단 (5초마다 갱신)
- 원인 분석 및 단계별 해결 방법 안내
- 화면 복제 / 확장 / TV만 / 노트북만 — 버튼 1번으로 즉시 적용
- F11 전체화면, F5 새로고침, 숫자키 1~4 빠른 연결

## 요구사항
- Windows 10 / 11 (64bit)
- 별도 설치 불필요

## 빌드
```
pip install pyinstaller
pyinstaller --onefile --noconsole --name "HDMI연결도우미" hdmi_connector.py
```

## 라이선스
MIT License — 교육 목적 무료 사용 가능
