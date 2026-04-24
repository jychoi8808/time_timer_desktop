# 🕒 Time Timer (Desktop) — v5

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)

**Time Timer (Desktop)**은 집중력을 높여주는 시각적 타이머 앱입니다. 직관적인 빨간색 다이얼을 통해 남은 시간을 한눈에 파악할 수 있으며, 데스크탑 환경에 최적화된 다양한 편의 기능을 제공합니다.

---

## ✨ 주요 기능 (Key Features)

### 1. 시각적 다이얼 & 커스텀 설정
- **직관적 디자인:** 레퍼런스 이미지를 기반으로 한 세련되고 깔끔한 UI.
- **시간 모드:** 일반적인 60분 모드와 장시간 집중을 위한 120분 모드 지원.
- **다양한 알림음:** '부드러운 차임', '종소리', '파도 음' 등 7가지 고품질 합성 사운드 제공.

### 2. 미니멀 모드 (Minimal Mode / PIP)
- **자동 전환:** 창 크기를 일정 수준(200x250) 이하로 줄이면 불필요한 요소를 제거하고 도넛 모양의 타이머만 남는 미니멀 모드로 변신합니다.
- **스마트 제어:** - **도넛 링:** 드래그를 통해 시간을 직관적으로 설정 가능.
  - **중앙 공간:** 클릭 시 재생/일시정지, 드래그 시 창 이동.
  - **상태 표시:** 일시정지 시 다이얼 색상이 회색으로 변경되어 상태를 즉시 파악 가능.

### 3. 무음 모드 (Silent Mode)
- 소리를 낼 수 없는 환경(도서관, 사무실 등)을 위해 종료 시 화면이 빨간색으로 깜빡이며 알림을 주는 기능을 지원합니다.

### 4. 데스크탑 최적화 UX
- **항상 위(Pin):** 다른 창에 가려지지 않도록 상단 고정 기능 제공 (미니모드 지원).
- **투명도 조절:** 작업 방해를 최소화하기 위해 20%~100% 범위의 창 투명도 설정 가능.
- **프레임리스 디자인:** 테두리 없는 깔끔한 창 디자인과 부드러운 리사이징/드래그 이동.
- **테마 동기화:** 시스템 설정에 따라 라이트/다크 테마가 실시간으로 반영됩니다.

---

## 🚀 시작하기 (Getting Started)

### 요구 사항
- Python 3.8 이상
- PyQt5

### 설치 및 실행
1. 저장소를 클론합니다.
```bash
git clone [https://github.com/jychoi8808/time_timer_desktop.git](https://github.com/jychoi8808/time_timer_desktop.git)
cd time_timer_desktop
```


2. 필요한 패키지를 설치합니다.
```bash
pip install PyQt5
```

3. 앱을 실행합니다.
```bash
python time_timer_desktop.py
```

---

## 🛠 기술 스택 (Tech Stack)

Language: Python
GUI Framework: PyQt5 (Qt Widgets, QPainter, QtMultimedia)
Font: Pretendard (Variable)
Sound Generation: Wave, Struct (Procedural Audio Synthesis)

---
## 📄 라이선스 (License)

이 프로젝트는 MIT 라이선스에 따라 자유롭게 이용 가능합니다.

---
## 👨‍💻 기여자 (Author)

jychoi8808 - GitHub Profile
