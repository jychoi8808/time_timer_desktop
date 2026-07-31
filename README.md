# Time Timer (Desktop)

Google의 Time Timer 제품에서 영감을 받은 반응형 데스크탑 타이머입니다.
**Tauri 2 + React + TypeScript**로 구축되어 가볍고(수 MB) 세련된 UI를 제공합니다.

> 이전 PyQt5 버전은 [`legacy/`](./legacy) 폴더에 보존되어 있습니다.
> 설계 문서는 [`DESIGN.md`](./DESIGN.md) 참고.

## 주요 기능

### ⏱ 시각적 카운트다운
설정한 시간만큼 빨간 면적(SVG 파이)이 표시되고, 시간이 흐를수록 부드럽게 줄어듭니다.
다이얼을 클릭·드래그해 시간을 설정하며(12시=0, 시계방향, 1분 스냅), 호버 시 미리보기를 보여줍니다.
창을 리사이즈해도 다이얼은 항상 1:1 원형 비율을 유지하고 눈금·숫자·텍스트가 비례 스케일됩니다.

### 📌 항상 위 / 플로팅
📌 버튼으로 항상 위 고정을 켜고 끕니다(기본 ON). 프레임리스 + 투명 배경 + 둥근 모서리.

### 🔎 미니모드 (PIP)
창을 200×250px보다 작게 줄이면 자동으로 도넛형 미니모드로 전환됩니다.
- 다이얼 클릭 = 시작/정지
- 도넛 밴드 드래그 = 시간 설정
- 그 외 영역 드래그 = 창 이동

### 🫥 가림 방지 (3가지 모드, 설정에서 선택)
- **수동**: 투명도 슬라이더로만 조절
- **반투명 전환**: 커서를 창 위에 올리면 반투명해지고, 벗어나면 복귀
- **완전 클릭 통과**: 커서를 올리면 창이 마우스를 통과시켜 뒤 작업을 그대로 조작 (Rust 전역 커서 감지)

### 🔔 종료 알림
- **알림음 7종** (부드러운 차임/도미솔 상승/종소리/디지털 비프/딩동/알람 시계/파도 음) — Web Audio로 즉석 합성, 외부 파일 무의존
- **무음 모드**: 소리 대신 화면을 붉게 깜빡임
- **OS 네이티브 알림**: 시스템 알림 배너

### 🍅 커스텀 뽀모도로
고정 규칙이 아니라 **구간을 자유롭게 구성**합니다.
- 각 구간의 이름·길이·색상 직접 지정, 추가/삭제/순서 변경
- 자동 진행(구간 종료 시 다음 구간 자동 시작) / 전체 반복 토글
- 실행 중 현재 구간과 진행상황 표시(`집중 · 2/4`), 다이얼 색이 구간 색으로

### ⌨ 전역 단축키 + 시스템 트레이
- `Ctrl+Shift+Space` 시작/정지 · `Ctrl+Shift+R` 리셋 · `Ctrl+Shift+T` 창 표시/숨김 (창 포커스 불필요)
- 트레이 아이콘 좌클릭=창 열기, 우클릭 메뉴=열기/시작·정지/리셋/종료
- 창 닫기(✕)는 종료가 아니라 **트레이로 숨김** (완전 종료는 트레이 "종료")

### 💾 설정·창 상태 영속화
알림음·투명도·가림방지·뽀모도로 등 모든 설정과 창 위치·크기를 저장해 재실행 시 복원합니다
(`settings.json`, `window.json`).

## 개발 환경 준비

- **Node.js LTS** (권장: [fnm](https://github.com/Schniz/fnm) 등 사용자 레벨 버전 매니저)
- **Rust** (rustup) + **MSVC C++ Build Tools** (Windows 링커)
- WebView2 (Windows 11 기본 탑재)

## 실행 (개발)

```bash
npm install
npm run tauri dev
```

## 빌드 (배포용 설치 파일)

```bash
npm run tauri build
```

Windows 설치 파일(.msi / .exe)이 `src-tauri/target/release/bundle/` 아래에 생성됩니다.

## 프로젝트 구조

```
src/                     # React 프론트엔드
  components/            # TimerDial, SettingsPage, PomodoroEditor, ResizeHandles, Toggle
  hooks/                 # useTimer, useOcclusion, useWindowPersistence, useGlobalShortcuts
  audio/sounds.ts        # Web Audio 알림음 합성
  pomodoro/types.ts      # 뽀모도로 데이터 모델
  settings/useSettings.ts# 설정 타입·기본값·영속화
src-tauri/               # Rust 백엔드
  src/lib.rs             # 트레이, 클릭통과 커서 폴링, 플러그인 등록
  capabilities/          # Tauri 권한
  tauri.conf.json        # 창 옵션(프레임리스·투명·항상위)
legacy/                  # 이전 PyQt5 버전 (참고용 보존)
```

## 커스터마이즈

- **테마/색상**: `src/App.css`, `src/components/*.css`의 CSS 변수(`--red`, `--dial-face` 등). 라이트/다크 자동 대응.
- **미니모드 임계값**: `src/App.tsx`의 `MIN_W` / `MIN_H`.
- **알림음 추가**: `src/audio/sounds.ts`의 `recipes`.
- **기본 단축키**: `src/settings/useSettings.ts`의 `DEFAULT_HOTKEYS`.
