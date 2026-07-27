# page_capture  
<sub>2026-07-24  Jonghyun Park w/ Claude</sub>  

Selenium 기반 웹 페이지 전체 캡처 자동화 도구입니다.  
PC / MO(모바일) 뷰를 각각 캡처하여 지정 폴더에 PNG 및 MHTML로 저장합니다.
URL이 많을 때는 `MAX_WORKERS` 개의 헤드리스 Chrome을 동시에 띄워 병렬로 캡처합니다.

## 파일 구성

| 파일 | 설명 |
|---|---|
| `page_capture_260724_v3.5.py` | 메인 캡처 스크립트 (단일 파일로 관리, 날짜는 최신 변경 시점) |
| `foldering_move_png.py` | 캡처된 PNG를 사이트코드별 하위 폴더로 정리 |

> 파일명은 `page_capture_YYMMDD_v메이저.마이너.py` 형식 — `YYMMDD`는 최신 변경 시점, `v메이저.마이너`는 변경 단위. 캠페인별 날짜는 파일명에 포함하지 않음 (의미 없는 suffix가 됨).

## 사용 방법

### 1. 설정 상수 수정
스크립트 상단의 `# 사용자가 바꿔야 하는 부분` 섹션에 출력 경로, 동시 실행 개수, 캡처 대상 도메인, URL 목록을 본인 환경에 맞게 변경합니다.

```python
OUTPUT_DIR = r"C:\Users\user_name\Downloads\captures"

MAX_WORKERS = 4                                      # 동시 헤드리스 Chrome 수 (1개당 ~300-500MB RAM). 사양별 권장값은 스크립트 주석 참고 (16GB→4~6, 32GB+→12~14)

TARGET_DOMAIN = "example.com"                        # 메인 글로벌 도메인
TARGET_DOMAIN_CN = ("example.com.cn", "example.cn")  # 중국 사이트 — 별도 사이트코드 'CN' 부여
TARGET_BRAND_KEYWORD = "example"                     # host 안에 이 키워드 들어가면 같은 브랜드로 인식
HQ_SITE_CODE = "hq"                                  # 본사(HQ) path 세그먼트 — 이 사이트만 렌더가 무거워 PC 캡처 시 추가 대기
```

### 2. URL 목록 수정
스크립트 상단 `URLS` 상수에 캡처할 URL을 한 줄에 하나씩 입력합니다 (`#` 로 시작하면 주석 처리). URL 수 × (PC/MO) 작업이 `MAX_WORKERS` 개씩 병렬 처리됩니다.

### 3. 직접 실행

```bash
python page_capture_260724_v3.5.py
```

### 4. 작업 스케줄러 등록 (창 없이 백그라운드 실행)

> **`pythonw.exe` 사용 권장**  
> `python.exe`는 실행 시 cmd 창이 팝업됩니다.  
> 같은 경로의 `pythonw.exe`를 사용하면 창이 전혀 뜨지 않습니다.

#### CLI 등록

```bat
schtasks /create /tn page_capture ^
  /tr "\"C:\Python3xx\pythonw.exe\" \"C:\Users\user_name\...\page_capture_260724_v3.5.py\"" ^
  /sc daily /st 09:00 /it /f
```

#### GUI 등록

1. `taskschd.msc` 실행
2. **작업 만들기** → 일반 탭: 이름 입력, "사용자가 로그온할 때만 실행" 선택
3. **트리거** 탭 → 새로 만들기 → 반복 주기 설정
4. **동작** 탭 → 새로 만들기:
   - 프로그램/스크립트: `C:\Python3xx\pythonw.exe` (창 없이 실행; 일반 python.exe 쓰면 cmd 창 팝업됨)
   - 인수 추가: `"C:\Users\user_name\OneDrive - company_name\...\page_capture_260724_v3.5.py"`
5. **조건** 탭 → 전원 섹션 → **"AC 전원이 연결된 경우에만 작업 시작" 체크 해제**

### 5. PNG 정리
캡처 완료 후 `foldering_move_png.py`를 실행하면  
사이트코드별 하위 폴더로 자동 분류됩니다.

> ⚠️ **MO(모바일) 파일을 먼저 옮긴 뒤 실행하세요.** 정리 스크립트는 PC/MO 를 구분하지 않으므로, 같은 폴더에 섞여 있으면 의도치 않게 함께 분류됩니다.

> 참고: `foldering_move_png.py` 는 `.png` 만 이동합니다. 함께 저장된 `.mhtml` 은 `OUTPUT_DIR` 에 그대로 남으므로 필요 시 수동 정리하세요.

## 입력 · 출력 예시

**입력** — 스크립트 상단 `URLS` 에 한 줄에 하나씩 (빈 줄 / `#` 시작은 무시):

```python
URLS = """
https://www.example.com/nz/offer/campaign-name-gift-ideas
https://www.example.com/vn/offer/campaign-name
# https://www.example.com/au/offer/old-page   ← 주석 처리되어 스킵
"""
```

**출력** — URL 1개당 PC / MO 뷰 각각 PNG + MHTML 이 `OUTPUT_DIR` 에 저장됩니다.
파일명 형식: `{사이트코드}_{PC|MO}_{경로}_page_{쿼리}_{날짜}.png` (쿼리 없으면 `_{쿼리}` 생략, `{날짜}`는 캡처일 `MMDD`)

```
NZ_PC_offer_campaign-name-gift-ideas_page_0706.png
NZ_MO_offer_campaign-name-gift-ideas_page_0706.png
VN_PC_offer_campaign-name_page_0706.png
VN_MO_offer_campaign-name_page_0706.png
```

- 사이트코드는 URL path 의 첫 국가 세그먼트에서 추출 (`/nz/` → `NZ`). `TARGET_DOMAIN_CN` 매칭 도메인은 host 기준으로 `CN`, path 가 없으면 `GLOBAL` 로 fallback.
- **기본 산출물은 `_daily_report.xlsx` 하나뿐입니다(v3.5).** 아래 `_result_latest.csv` / `_run_latest.log` / `_skipped_*.txt` 는 기본적으로 폴더에 남지 않습니다 — 필요하면 각 플래그를 켜세요.
- 리다이렉트/에러/unknown/로그인 으로 스킵된 URL 개수는 콘솔에 찍힙니다. `WRITE_SKIPPED_TXT=True` 로 두면 `_skipped_redirect.txt` / `_skipped_error_page.txt` / `_skipped_unknown_page.txt` / `_skipped_login_page.txt` 로도 남습니다(기본 `False` — 같은 정보가 리포트 '이슈' 열에 이미 있음).
- **`_result_latest.csv`** 에는 `(url, device)` 단위로 `result / final_url / http_status / title / detail / elapsed` 가 남습니다. 이 CSV 는 `write_daily_report` 의 입력 원본이라 **실행 중에는 항상 생성**되지만, 완주하면 리포트 갱신 후 삭제됩니다(`KEEP_RESULT_CSV=False`). 크래시로 중단되면 남아서 그 시점까지의 판정을 볼 수 있습니다. 남겨두려면 `KEEP_RESULT_CSV=True`.
- 같은 날 다시 실행하면 이미 있는 PNG+MHTML 은 건너뜁니다(`SKIP_IF_EXISTS`). 중단 후 이어받기가 목적이며, 다시 받고 싶으면 파일을 지우거나 옵션을 끄면 됩니다. 캡처물을 `foldering_move_png.py` 로 sitecode 폴더에 옮긴 뒤에도 `{OUTPUT_DIR}/{SITECODE}/` 를 함께 확인하므로 이어하기가 계속 동작합니다(v3.4).
- 캡처 후 `foldering_move_png.py` 를 돌리면 위 PNG 들이 사이트코드별 하위 폴더로 정리됩니다.
- **`_run_latest.log`** 에 실행 로그가 남습니다(`LOG_TO_FILE`, **기본 `False`(끔) — v3.5**). 작업 스케줄러에서 `pythonw` 로 돌리면 콘솔 출력이 버려지므로, hang·실패·지연을 나중에 추적하려면 `LOG_TO_FILE=True` 로 켠 뒤 이 파일을 보세요. `STACK_DUMP_INTERVAL` 을 0 보다 크게 두면 그 주기로 전체 스레드 스택도 남지만 **기본값은 0(끔)** 입니다 — v3.4 참고.
- **`_daily_report.xlsx`** 는 날짜별 결과를 한 파일에 누적합니다. A열 = URL, **최신 날짜가 항상 B~D열**(PC / MO / 이슈)이고 이전 날짜는 오른쪽(E~G, H~J …)으로 밀립니다. 같은 날 다시 실행하면 그 날짜 블록을 덮어씁니다. 저장된 칸은 초록, 문제 있는 칸은 빨강으로 칠해집니다. **실행 중에도 `REPORT_FLUSH_EVERY` 건마다 갱신**되므로, 중간에 프로세스가 죽어도 그 시점까지의 결과가 남습니다.
- 산출물 파일명은 전부 고정(언더바 접두)이라 날짜별로 쌓이지 않습니다 — 이력은 `_daily_report.xlsx` 한 파일이 갖습니다. 파일명을 바꾸려면 `RESULT_CSV_NAME` / `RUN_LOG_NAME` / `SKIPPED_TXT_NAMES` / `DAILY_REPORT_NAME` 을, **어떤 산출물을 남길지는** `LOG_TO_FILE` / `WRITE_SKIPPED_TXT` / `KEEP_RESULT_CSV` 를 보세요(v3.5, 셋 다 기본 OFF → 폴더엔 리포트만).
- `PREFILTER_HTTP` 가 켜져 있으면 캡처 전에 URL 상태코드를 먼저 확인해, `404`/`5xx` 는 브라우저를 띄우지 않고 `error_page` 로 확정합니다(대상이 수백 개일 때 실행 시간이 크게 줄어듭니다). 판정 결과는 동일하게 `_result_latest.csv` 에 남고 `detail` 에 `사전 확인` 이라고 표시됩니다.

## 요구사항

### 파이썬 패키지

```bash
pip install selenium Pillow numpy requests openpyxl
# 또는
pip install -r requirements.txt
```

### ChromeDriver

Selenium 4.6+ 의 **Selenium Manager**가 설치된 Chrome 버전에 맞는 ChromeDriver를 자동으로 내려받아 관리하므로, 보통 수동 설치가 필요 없습니다. (코드도 `webdriver.Chrome(options=...)` 로 드라이버 경로를 지정하지 않음)

버전 불일치 등으로 자동 해결이 실패할 때만 수동 배치:

1. Chrome 버전 확인 (`chrome://settings/help`)
2. https://googlechromelabs.github.io/chrome-for-testing/ 에서 동일 버전 다운로드
3. `chromedriver.exe`를 PATH에 추가하거나 스크립트와 같은 폴더에 배치

## 변경 이력

| 버전 | 날짜 | 변경 |
|---|---|---|
| v2.0 | 2026-04-17 | 초기 버전 |
| v2.1 | 2026-04-20 | `is_error_page` 다국어 에러 감지 강화 + `/common/404/` + Chrome ERR 감지 |
| v2.2 | 2026-04-29 | filename에 `OUTPUT_DIR` 변수 사용 + raw string 적용 + 파일명 정리 |
| v2.3 | 2026-05-22 | 주석/예시 URL sanitize + 도메인 매칭 로직 상수화 (`TARGET_DOMAIN` / `TARGET_DOMAIN_CN` / `TARGET_BRAND_KEYWORD`) + 설정 상수 상단 이동 |
| v2.4 | 2026-06-18 | 캡처를 `ThreadPoolExecutor`로 병렬화 (`MAX_WORKERS`) + URL 목록 상단 상수(`URLS`)로 이동 |
| v2.4 | 2026-06-19 | `MAX_WORKERS` 사양별 권장값 주석 보강 |
| v2.5 | 2026-07-06 | `is_error_page` 오탐 수정 (정상 페이지가 error로 skip 되던 문제) |
| v2.6 | 2026-07-08 | perf log로 메인 문서 HTTP status 감지 추가 (비영어 404가 `is_error_page`를 빠져나가 캡처되던 문제) |
| v2.7 | 2026-07-10 | perf log 활성화 후 `--headless=new` 가 빈 창을 띄우는 문제 → `--window-position` 으로 창을 화면 밖으로 이동 |
| v2.8 | 2026-07-10 | PC 캡처 분기의 미정의 호출 `is_sec_path` → `is_hq_path` 로 수정 (매 PC 캡처가 `NameError` 로 skip 되던 문제) + `OUTPUT_DIR` 기본값 `captures` 로 정리 |
| v2.9 | 2026-07-14 | unknown(soft-404) 페이지 skip 추가 — 메인 도메인이 존재하지 않는 경로에 HTTP 200 + 홈 fallback 을 줄 때 `<meta property="og:url">` 이 비었거나 없음을 `is_unknown_page` 로 감지해 skip (리다이렉트/HTTP status/error 마커로 안 잡히던 케이스) + `skipped_unknown_page_{ts}.txt` 기록 |
| v3.0 | 2026-07-20 | **버그**: 출력 폴더 생성을 캡처 시작 전으로 이동(폴더가 없으면 저장이 전량 실패), URL 주석 필터를 `strip()` 후 판정(들여쓴 `#` 줄이 URL 로 유입), Chrome 생성을 `try` 안으로(기동 실패 시 결과 집계에서 누락), `except:` → `except Exception:`(Ctrl+C 중단 가능), page load/script timeout 추가 |
| v3.0 | 2026-07-20 | **결과기록**: `(url, device)` 단위 `result_{ts}.csv` 추가 — 디바이스별 skip 사유·최종 URL·HTTP status·소요시간 기록 |
| v3.0 | 2026-07-20 | **로그인 화면 skip**: 쿠키·팝업 처리 중 늦게 로그인 페이지로 이동하는 경우 초기 리다이렉트 판정을 빠져나가 로그인 화면이 캡처물로 저장되던 문제 → 저장 직전 URL 재확인 + `SKIP_URL_KEYWORDS` (`RECHECK_URL_BEFORE_SAVE`) |
| v3.0 | 2026-07-20 | **속도**: 워커별 Chrome 재사용(`REUSE_DRIVER`), 이어하기(`SKIP_IF_EXISTS`), 일시적 실패만 재시도(`RETRY_COUNT`), MHTML 크기 검증(`MIN_MHTML_BYTES`) |
| v3.0 | 2026-07-20 | **리다이렉트 정규화**: 후행 슬래시만 무시하던 비교를 `#fragment`·추적 파라미터(`utm_*`/`gclid`)·`www.`·대소문자·기본 포트·`http↔https`·퍼센트 인코딩·쿼리 순서까지 무시하도록 변경 — 정상 페이지가 리다이렉트로 오탐돼 skip 되던 문제 |
| v3.0 | 2026-07-20 | **CDP 전체캡처(기본 OFF)**: `Page.captureScreenshot(captureBeyondViewport)` 경로 추가. 높이는 정확하지만 스크롤로 띄운 지연 로딩 이미지가 렌더되기 전에 찍혀 이미지가 빠진 캡처가 나오므로 `USE_CDP_FULLPAGE=False` 가 기본. 이미지 로딩 완료 대기를 구현하기 전까지 켜지 말 것 |
| v3.1 | 2026-07-21 | **인증 게이트 skip 보강**: `SKIP_URL_KEYWORDS` 에 `/registration` 추가 — "메일 주소를 넣으면 접근 링크를 보내준다"는 인증 게이트 페이지가 URL 에 `/login` 이 없어 v3.0 의 로그인 skip 을 통과해 캡처물로 저장되던 문제 |
| v3.2 | 2026-07-22 | **MO 스티칭 재작성**: 겹침 보정이 CSS px 값을 device px 자리에 써서 이음새마다 내용이 중복되고, 캔버스가 커진 만큼 하단이 검정으로 남던 버그 수정(실측 75,492px 페이지에서 중복·검정 약 12%). 이제 각 컷을 "실제 스크롤 위치 × 배율" 자리에 붙여 단위 혼동 자체가 생기지 않음 |
| v3.2 | 2026-07-22 | **스티키 반복 제거**: `NEUTRALIZE_STICKY` 로 스티칭 동안 `position:fixed/sticky` 를 `static` 으로 바꾸고 저장 전 전량 원복(MHTML 은 원본 상태 보존). JS 가 스크롤마다 위치를 다시 잡는 사이트를 위해 결과 픽셀에서 스티키 바 높이를 직접 재는 `_sticky_band` 추가 + `MOBILE_STITCH_OVERLAP` / `MOBILE_MAX_SHOTS`(상한 도달 시 잘린 높이 경고) 상수화 |
| v3.2 | 2026-07-22 | **타임아웃**: `PAGE_LOAD_TIMEOUT` 60 → 120 (무거운 페이지는 단독 실행에서도 90초를 넘겨 통째로 누락됐음) + `CDP_TIMEOUT` 신설 — `set_page_load_timeout`/`set_script_timeout` 은 CDP 에 적용되지 않아 `Page.captureSnapshot` 무응답 시 워커가 영구 대기하고 결과 CSV 기록까지 막혔다(실제 4시간 점유) → `cdp_with_timeout` 으로 감싸고 초과 시 그 건만 `mhtml_failed` 로 포기 |
| v3.2 | 2026-07-22 | **결과 CSV 증분 기록**: 캡처 1건이 끝날 때마다 `result_{ts}.csv` 에 append (예전엔 전부 끝난 뒤 한 번에 써서 중간에 멈추면 그날 판정 결과가 통째로 유실). 완주하면 마지막에 입력 URL 순서로 정렬해 다시 씀 |
| v3.3 | 2026-07-22 | **hang 원인 제거**: `driver.quit()` 이 응답 없는 chromedriver 를 상대로 **타임아웃 없는** HTTP 요청(`send_remote_shutdown_command` → `is_connectable`)을 걸어 영구 대기하던 문제. 이 경로는 page load/script/CDP 타임아웃이 전혀 감시하지 못해, 그 태스크는 결과 행조차 남기지 못한 채 사라졌다 → 별도 스레드로 `quit()` 하고 `QUIT_TIMEOUT` 초과 시 chromedriver 프로세스를 직접 종료 |
| v3.3 | 2026-07-22 | **진단**: 파일 로그(`run_{ts}.log`)로 출력 미러링 + `STACK_DUMP_INTERVAL` 마다 전체 스레드 스택 덤프. 스케줄러가 `pythonw` 로 돌리면 콘솔 출력이 버려져 hang 원인 추적이 불가능했다 (이 로그를 넣은 첫 실행에서 위 원인이 특정됐다) |
| v3.3 | 2026-07-22 | **신뢰성**: 태스크 하드 데드라인(`TASK_DEADLINE_MO`/`_PC`) — 감시 스레드가 상한 초과 워커의 드라이버를 끊어 전체 실행이 물리는 것을 막음 + 시작 시 이전 실행 잔재(headless chrome/chromedriver) 정리 |
| v3.3 | 2026-07-22 | **속도**: HTTP 사전 필터(`PREFILTER_HTTP`) — 404/5xx 는 브라우저 없이 확정. 실측상 워커시간의 58%가 죽은 URL 확인에 쓰였고 대상 URL 의 84%가 PC·MO 양쪽 死였다. `403` 은 봇 차단일 수 있어 제외하고, soft-404 는 기존 og:url 검사가 계속 담당 |
| v3.3 | 2026-07-22 | **산출물**: 일일 리포트 `daily_report.xlsx` — 최신 날짜가 항상 B~D열(PC/MO/이슈)이고 과거 날짜는 오른쪽으로 밀림(같은 날 재실행은 덮어쓰기). MO 하단 흰 여백 트림(`TRIM_TRAILING_BLANK`) |
| v3.4 | 2026-07-23 | **크래시**: `STACK_DUMP_INTERVAL` 기본 OFF. 이 기능을 켠 뒤 access violation(`0xC0000005`) 이 2회 발생했고 둘 다 "덤프 출력 도중"이었다. 하드 크래시는 `finally` 도 실행되지 않아, 절반쯤에서 죽으면 큐 뒤쪽이 통째로 결번되고 산출물도 하나도 안 남는다(실제로 하루치 캡처의 27%가 그렇게 빠졌다). hang 추적은 run 로그 + 데드라인 감시로 충분 |
| v3.4 | 2026-07-23 | **산출물**: 날짜별 `result_*.csv` / `run_*.log` 누적을 폐지하고 고정명·언더바 접두로 통일 — `_daily_report.xlsx` / `_result_latest.csv` / `_run_latest.log` / `_skipped_*.txt` |
| v3.4 | 2026-07-23 | **리포트 내구성**: `write_daily_report` 가 메모리 `rows` 대신 result CSV 를 읽고 `REPORT_FLUSH_EVERY` 건마다 중간 저장. 예전엔 완주해야만 리포트가 생겨, 중간에 죽으면 "어디까지 됐는지" 조차 남지 않았다 |
| v3.4 | 2026-07-23 | **이어하기**: `already_captured()` — `SKIP_IF_EXISTS` 가 `OUTPUT_DIR` 루트만 보던 탓에 foldering 후에는 이어하기가 무력화돼 재실행이 전량 재캡처가 됐다. 이제 `{OUTPUT_DIR}/{SITECODE}/` 도 확인 |
| v3.5 | 2026-07-24 | **산출물 축소**: 폴더에 `_daily_report.xlsx` 하나만 남긴다. `LOG_TO_FILE` 기본 OFF(`_run_latest.log` 미생성) / `WRITE_SKIPPED_TXT=False`(`_skipped_*.txt` 미생성, 개수는 콘솔) / `KEEP_RESULT_CSV=False`(`_result_latest.csv` 는 리포트 입력으로 실행 중엔 유지하다 완주 후 삭제). 셋 다 켜면 종전 동작. 크래시 시엔 CSV 가 남아 사후 추적 가능 |

> 상세 이력은 메인 스크립트 헤더 주석 참고. 파일은 단일 파일로 관리되며 버전업 시 rename + 헤더 갱신.

## License

MIT
