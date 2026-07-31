# Time Timer (Desktop) — Tauri 재설계 문서

기존 PyQt5 단일 파일 앱(`time_timer_desktop.py`)을 **Tauri + React + TypeScript** 기반으로 재구축하기 위한 설계 문서.

---

## 1. 목표

- 웹 기술(HTML/CSS/SVG/Canvas)로 지금보다 세련되고 부드러운 디자인·애니메이션을 구현한다.
- 기존 기능을 모두 유지하면서, 데스크톱 유틸리티로서의 완성도(상주·단축키·영속화)를 끌어올린다.
- 가벼운 배포(수 MB)와 낮은 메모리 사용을 위해 Electron 대신 Tauri를 택한다.

## 2. 기술 스택

| 영역 | 선택 | 비고 |
|------|------|------|
| 셸/백엔드 | **Tauri 2.x** (Rust) | 창 제어, 트레이, 전역 단축키, 네이티브 알림 |
| 프론트엔드 | **React 18 + TypeScript** | 컴포넌트 기반 UI |
| 번들러 | **Vite** | Tauri 공식 템플릿 기본값 |
| 스타일 | **Tailwind CSS + CSS 변수 테마** | 라이트/다크 테마를 CSS 변수로 전환 |
| 애니메이션 | **CSS transition + Framer Motion(선택)** | 다이얼/모드 전환 부드럽게 |
| 다이얼 렌더 | **SVG** | 파이 섹터·눈금·핸드를 벡터로, 크기 무관 선명 |
| 사운드 | **Web Audio API** | 기존처럼 파형 즉석 합성(외부 파일 무의존) |
| 상태관리 | **Zustand**(경량) 또는 React Context | 타이머/설정 상태 |

### 사전 준비물 (현재 PC 미설치 — 설치 필요)
- **Node.js LTS** (npm 포함) — 프론트엔드 빌드
- **Rust toolchain** (`rustup`) — Tauri 백엔드 컴파일
- **Microsoft C++ Build Tools (MSVC)** — Rust 링킹(Windows)
- **WebView2 런타임** — Windows 11에는 기본 탑재(대개 불필요)

## 3. 기능 명세

### 핵심 4

1. **항상 위 / 플로팅**
   - Tauri `alwaysOnTop(true)` 기본 ON, 토글 가능.
   - 프레임리스(`decorations: false`) + 투명 배경 + 둥근 모서리.

2. **미니모드**
   - 일정 크기 미만으로 줄이면 자동 전환(현재 200×250 임계값 계승), 또는 트레이/단축키로 즉시 토글.
   - 미니모드: 부가 UI 숨김, 다이얼(도넛)만 표시, 다이얼 클릭=시작/정지, 바깥 드래그=이동.

3. **가림 방지 — 두 모드 사용자 선택**
   - **(A) 반투명 전환**: 커서가 창 위에 오면 지정 투명도(예: 25%)로 낮아지고, 벗어나면 복귀. 창은 계속 상호작용 가능.
   - **(B) 완전 클릭 통과**: 커서가 오면 `set_ignore_cursor_events(true)`로 창을 통과시켜 뒤 작업을 그대로 조작. 창을 다시 조작하려면 전역 마우스 추적으로 "벗어남" 감지 후 복귀 → **Rust 측 전역 마우스 위치 폴링 필요**.
   - **(C) 수동 투명도 슬라이더**: 자동 반응 없이 사용자가 20~100% 직접 조절(현재 기능 계승).
   - 세 방식은 설정에서 선택. A/B는 상호배타, C는 기본 투명도로 병존.

4. **종료 알림 — 소리 / 무소음 깜빡임**
   - Web Audio로 알림음 합성(부드러운 차임 등 기존 7종 포팅).
   - 무음 모드: 창 배경 붉은 깜빡임(CSS 애니메이션으로 부드럽게).
   - OS 네이티브 알림과 병행 가능(아래 8번).

### 추가 4

5. **뽀모도로 / 커스텀 사이클**
   - 사용자가 **구간을 자유롭게 정의**: 각 구간의 이름·길이·색상.
   - 반복 횟수, "N세트 후 긴 휴식" 규칙, 자동 다음 구간 진행 여부.
   - 프리셋 저장/불러오기(예: "집중 50/휴식 10").
   - 데이터 모델은 §4 참조.

6. **전역 단축키 + 시스템 트레이**
   - 전역 단축키(설정에서 커스터마이즈): 시작/일시정지, 리셋, 미니모드 토글, 창 표시/숨김.
   - 트레이 아이콘: 좌클릭=창 토글, 우클릭 메뉴=시작/정지·리셋·미니모드·종료. 창 닫기 시 트레이 상주.

7. **설정·창 상태 영속화**
   - 창 위치/크기/미니모드 여부, 알림음·투명도·테마·가림방지 모드, 뽀모도로 프리셋·마지막 값 저장.
   - Tauri `Store` 플러그인(JSON 파일) 사용. 앱 시작 시 복원.

8. **OS 네이티브 알림**
   - 타이머 종료 시 Windows 토스트 배너(`notification` 플러그인).
   - 알림 클릭 시 창을 앞으로(focus).

## 4. 설정 데이터 모델 (개략)

```ts
type OcclusionMode = 'semi-transparent' | 'click-through' | 'manual';

interface Settings {
  alwaysOnTop: boolean;
  theme: 'system' | 'light' | 'dark';
  opacity: number;                 // 0.2 ~ 1.0 (수동 기본 투명도)
  occlusion: {
    mode: OcclusionMode;
    hoverOpacity: number;          // A 모드에서 커서 올릴 때 투명도
  };
  sound: { enabled: boolean; name: string; volume: number };
  silentFlash: boolean;            // 무음 깜빡임
  osNotification: boolean;
  maxMinutes: 60 | 120;
  hotkeys: Record<'startPause'|'reset'|'toggleMini'|'toggleWindow', string>;
  pomodoro: {
    enabled: boolean;
    autoAdvance: boolean;
    longBreakEvery: number;        // N 세트마다 긴 휴식
    segments: PomodoroSegment[];
  };
}

interface PomodoroSegment {
  id: string;
  label: string;                   // "집중", "휴식" 등 사용자 지정
  minutes: number;
  color: string;
}

interface WindowState { x: number; y: number; w: number; h: number; minimal: boolean; }
```

## 5. 프로젝트 구조 (예정)

```
time_timer_desktop/
├─ src/                        # React 프론트엔드
│  ├─ components/
│  │  ├─ TimerDial.tsx         # SVG 다이얼 (호버·드래그·핸드·파이)
│  │  ├─ MiniMode.tsx
│  │  ├─ SettingsPage/…
│  │  └─ PomodoroEditor.tsx
│  ├─ hooks/                   # useTimer, useTheme, useOcclusion …
│  ├─ audio/                   # Web Audio 합성 (기존 레시피 포팅)
│  ├─ store/                   # Zustand 상태 + 영속화 브릿지
│  └─ styles/                  # Tailwind + 테마 변수
├─ src-tauri/                  # Rust 백엔드
│  ├─ src/main.rs              # 창·트레이·단축키·전역 마우스 폴링(클릭통과 복귀)
│  ├─ tauri.conf.json          # 창 옵션, 권한(capabilities)
│  └─ Cargo.toml
├─ (레거시) time_timer_desktop.py  # 참고용 보존 or 별도 브랜치 이동
└─ package.json
```

## 6. 필요한 Tauri 권한/플러그인
- `window` (always-on-top, decorations, transparent, ignore-cursor-events, set size/position)
- `tray-icon`, `global-shortcut`, `notification`, `store`
- 전역 마우스 위치 감지는 플러그인 부재 시 Rust 크레이트(예: `device_query`)로 폴링.

## 7. 구현 순서 (제안 단계)
1. **툴체인 설치** (Node LTS, Rust, MSVC Build Tools) — 사용자 환경 준비.
2. **스캐폴딩**: `create-tauri-app`(React+TS) 생성, 레거시 py 보존, 창 프레임리스·투명·항상위 기본형 띄우기.
3. **다이얼 이식**: SVG 다이얼(파이/눈금/핸드/호버/드래그) + 카운트다운 로직 + Web Audio 알림.
4. **미니모드 + 가림방지**: 크기 기반 전환, 반투명 A / 클릭통과 B / 수동 C.
5. **설정 페이지 + 영속화**: Store 연동, 테마/투명도/사운드.
6. **뽀모도로 에디터**: 커스텀 구간·프리셋·자동 진행.
7. **트레이 + 전역 단축키 + OS 알림**.
8. **패키징**: `tauri build`로 Windows 인스톨러(.msi/.exe) 생성.

## 8. 열린 결정 사항
- 레거시 PyQt 코드: repo에 보존 vs `legacy` 브랜치로 이동.
- 상태관리: Zustand 도입 vs Context만으로 충분.
- 애니메이션: Framer Motion 도입 여부(번들 크기 vs 개발 편의).
