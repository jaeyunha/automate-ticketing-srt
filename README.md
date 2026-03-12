# SRT 자동 예매 시스템

[English](README.en.md)

SRT(수서고속철도) 잔여석을 자동으로 모니터링하고, 좌석이 나오면 즉시 예매 후 이메일, 데스크톱, 텔레그램으로 알림을 보내는 자동화 도구입니다.

## 기능

- **실시간 잔여석 모니터링** — CLI 플래그로 모든 파라미터 설정 가능
- **다중 좌석 유형 탐지**: 일반실, 예약대기, 특실(선택)
- **자동 재로그인**: 세션 만료 감지 시 자동으로 재인증
- **다채널 알림**: 이메일(SMTP/AppleScript), 데스크톱(macOS/Linux/Windows), 텔레그램(openclaw)
- **안정적인 에러 처리**: 자동 브라우저 재시작, 점진적 백오프
- **백그라운드 실행**: 브라우저가 포커스를 뺏지 않음

## 요구사항

- **Python 3.12+**
- **macOS**, **Linux**, 또는 **Windows**
- **Chrome 브라우저** (원격 디버깅 활성화)
- **uv** 패키지 매니저
- **terminal-notifier** (macOS 전용, `brew install terminal-notifier`)
- **openclaw** (텔레그램 알림용, 선택)

## 설치

```bash
# 1. 의존성 설치
uv sync

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 이메일 및 SMTP 정보 입력

# 3. Chrome 디버깅 모드로 실행 (아래 OS별 안내 참고)
```

### Chrome 디버깅 모드 실행

자동화 시작 전에 Chrome을 원격 디버깅 포트와 함께 실행해야 합니다.
**반드시 기존 Chrome 창을 모두 닫은 후** 아래 명령어를 실행하세요.

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222
# 또는
/opt/google/chrome/google-chrome --remote-debugging-port=9222
```

**Windows (CMD):**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Windows (PowerShell):**
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

> Chrome이 실행되면 SRT 사이트(https://etk.srail.kr)에 로그인해두세요. 자동화가 저장된 세션을 사용합니다.

## 사용법

### 기본 실행 (기본값: 동대구 → 수서)

```bash
uv run run_automation.py
```

### 파라미터 지정

```bash
uv run run_automation.py \
  --departure 동대구 \
  --arrival 수서 \
  --date 20260314 \
  --time 080000 \
  --tickets 2
```

### 도착시간 제한 (12시 이전 도착만)

```bash
uv run run_automation.py --max-arrival 1200
```

### 특실 포함

```bash
uv run run_automation.py --first-class
```

### 전체 플래그

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `--departure` | 동대구 | 출발역 |
| `--arrival` | 수서 | 도착역 |
| `--date` | 20260314 | 출발일 (YYYYMMDD) |
| `--time` | 080000 | 출발시간 (HHMMSS) |
| `--tickets` | 2 | 예매 매수 |
| `--first-class` | 꺼짐 | 특실도 검색 |
| `--max-arrival` | 없음 | 최대 도착시간 (HHMM, 예: 1200) |
| `--max-restarts` | 5 | 최대 브라우저 재시작 횟수 |

## 동작 원리

```
run_automation.py (CLI 진입점)
  └─ main() — 외부 재시도 루프 (최대 5회)
      └─ run_ticket_search()
          ├─ CDP로 브라우저 연결 (localhost:9222)
          ├─ SRT 예매 페이지 이동
          ├─ 폼 입력 (출발역, 도착역, 날짜, 시간, 매수)
          └─ continuous_ticket_search() — 폴링 루프
              ├─ 세션 상태 확인 (만료 시 자동 재로그인)
              ├─ 조회 버튼 클릭
              ├─ 결과 확인: 일반실 → 예약대기 → 특실
              │   ├─ 발견 → 예약하기 클릭, 알림, 종료
              │   └─ 미발견 → 폼 재입력, 반복
              └─ 연속 5회 에러 → 브라우저 재시작
```

### 좌석 검색 우선순위

1. **일반실** (td[7]) — 항상 검색
2. **예약대기** (td[8]) — 항상 검색
3. **특실** (td[6]) — `--first-class` 옵션 시에만

우선순위 순서대로 첫 번째 `예약하기` 링크를 클릭합니다.

### 세션 복구

자동화는 세 가지 페이지 상태를 감지합니다:
- **로그인된 검색 페이지** → 정상 계속
- **로그아웃 상태** → 로그인 페이지로 이동, 로그인 버튼 클릭 (Chrome 저장된 계정 정보 사용), 검색 페이지로 복귀
- **알 수 없는 페이지** → 검색 페이지로 이동 후 폼 재입력

## 알림

티켓 발견 시 세 가지 알림이 동시에 발송됩니다:

| 채널 | 방식 | 플랫폼 |
|------|------|--------|
| 이메일 | SMTP (기본) → AppleScript (macOS 폴백) | 전체 |
| 데스크톱 | terminal-notifier (macOS) / desktop-notifier (Linux/Windows) | 전체 |
| 텔레그램 | openclaw (선택) | 전체 |

이메일 설정은 `.env` 파일에서 관리합니다. `.env.example`을 참고하세요.

## 프로젝트 구조

```
automate-ticketing-srt/
├── main.py                 # 핵심 자동화 로직
├── run_automation.py       # CLI 진입점
├── notification.py         # 데스크톱 알림 (크로스 플랫폼)
├── send_email_smtp.py      # 이메일 (SMTP, 크로스 플랫폼)
├── send_email.py           # 이메일 (macOS AppleScript 폴백)
├── send_imessage.py        # iMessage 알림 (macOS 전용)
├── .env.example            # 환경변수 템플릿
└── pyproject.toml          # 의존성
```

## 로깅

- **콘솔**: 10회마다 상태, 에러, 티켓 발견 이벤트만 출력
- **ticket_automation.log**: 상세 작업 로그
- **automation_runner.log**: 러너 레벨 로그

브라우저 라이브러리의 디버그 출력은 자동으로 억제됩니다.

## 문제 해결

**Chrome 디버깅 연결이 안 될 때**
- 기존 Chrome 창을 모두 닫고 `--remote-debugging-port=9222` 플래그로 다시 실행
- 포트 9222가 사용 중인지 확인: `lsof -i :9222` (macOS/Linux) 또는 `netstat -ano | findstr 9222` (Windows)

**세션이 계속 만료될 때**
- 시작 전에 Chrome에서 SRT 사이트에 로그인되어 있는지 확인
- 자동화가 Chrome의 저장된 계정 정보로 자동 재로그인합니다

**브라우저가 포커스를 뺏을 때**
- 이미 처리됨: `--no-focus-on-navigate` 플래그로 Chrome 실행

**이메일이 안 올 때**
- `.env` 파일에 `NOTIFY_EMAIL`, `SMTP_EMAIL`, `SMTP_PASSWORD` 설정 확인
- Gmail 사용 시 앱 비밀번호 필요: https://myaccount.google.com/apppasswords

**terminal-notifier를 찾을 수 없을 때 (macOS)**
```bash
brew install terminal-notifier
```

## 라이선스

MIT
