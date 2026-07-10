# page_capture  
<sub>2026-07-10  Jonghyun Park w/ Claude</sub>  

Selenium 기반 웹 페이지 전체 캡처 자동화 도구입니다.  
PC / MO(모바일) 뷰를 각각 캡처하여 지정 폴더에 PNG 및 MHTML로 저장합니다.
URL이 많을 때는 `MAX_WORKERS` 개의 헤드리스 Chrome을 동시에 띄워 병렬로 캡처합니다.

## 파일 구성

| 파일 | 설명 |
|---|---|
| `page_capture_260710_v2.7.py` | 메인 캡처 스크립트 (단일 파일로 관리, 날짜는 최신 변경 시점) |
| `foldering_move_png.py` | 캡처된 PNG를 사이트코드별 하위 폴더로 정리 |

> 파일명은 `page_capture_YYMMDD_v메이저.마이너.py` 형식 — `YYMMDD`는 최신 변경 시점, `v메이저.마이너`는 변경 단위. 캠페인별 날짜는 파일명에 포함하지 않음 (의미 없는 suffix가 됨).

## 사용 방법

### 1. 설정 상수 수정
스크립트 상단의 `# 사용자가 바꿔야 하는 부분` 섹션에 출력 경로, 동시 실행 개수, 캡처 대상 도메인, URL 목록을 본인 환경에 맞게 변경합니다.

```python
OUTPUT_DIR = r"C:\Users\your_name\Downloads\captures"

MAX_WORKERS = 4                                      # 동시 헤드리스 Chrome 수 (1개당 ~300-500MB RAM). 사양별 권장값은 스크립트 주석 참고 (16GB→4~6, 32GB→8~10)

TARGET_DOMAIN = "example.com"                        # 메인 글로벌 도메인
TARGET_DOMAIN_CN = ("example.com.cn", "example.cn")  # 중국 사이트 — 별도 사이트코드 'CN' 부여
TARGET_BRAND_KEYWORD = "example"                     # host 안에 이 키워드 들어가면 같은 브랜드로 인식
```

### 2. URL 목록 수정
스크립트 상단 `URLS` 상수에 캡처할 URL을 한 줄에 하나씩 입력합니다 (`#` 로 시작하면 주석 처리). URL 수 × (PC/MO) 작업이 `MAX_WORKERS` 개씩 병렬 처리됩니다.

### 3. 직접 실행

```bash
python page_capture_260710_v2.7.py
```

### 4. 작업 스케줄러 등록 (창 없이 백그라운드 실행)

> **`pythonw.exe` 사용 권장**  
> `python.exe`는 실행 시 cmd 창이 팝업됩니다.  
> 같은 경로의 `pythonw.exe`를 사용하면 창이 전혀 뜨지 않습니다.

#### CLI 등록

```bat
schtasks /create /tn page_capture ^
  /tr "\"C:\Python3xx\pythonw.exe\" \"C:\Users\user_name\...\page_capture_260710_v2.7.py\"" ^
  /sc daily /st 09:00 /it /f
```

#### GUI 등록

1. `taskschd.msc` 실행
2. **작업 만들기** → 일반 탭: 이름 입력, "사용자가 로그온할 때만 실행" 선택
3. **트리거** 탭 → 새로 만들기 → 반복 주기 설정
4. **동작** 탭 → 새로 만들기:
   - 프로그램/스크립트: `C:\Python3xx\pythonw.exe` (창 없이 실행; 일반 python.exe 쓰면 cmd 창 팝업됨)
   - 인수 추가: `"C:\Users\user_name\OneDrive - company_name\...\page_capture_260710_v2.7.py"`
5. **조건** 탭 → 전원 섹션 → **"AC 전원이 연결된 경우에만 작업 시작" 체크 해제**

### 5. PNG 정리
캡처 완료 후 `foldering_move_png.py`를 실행하면  
사이트코드별 하위 폴더로 자동 분류됩니다.

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

- 사이트코드는 host 의 국가 경로에서 자동 추출 (`TARGET_DOMAIN_CN` 매칭이면 `CN`).
- 리다이렉트/에러로 스킵된 URL 은 `skipped_redirect_{ts}.txt` / `skipped_error_page_{ts}.txt` 로 기록됩니다.
- 캡처 후 `foldering_move_png.py` 를 돌리면 위 PNG 들이 사이트코드별 하위 폴더로 정리됩니다.

## 요구사항

### 파이썬 패키지

```bash
pip install selenium Pillow numpy
```

### ChromeDriver

설치된 Chrome 브라우저 버전과 동일한 ChromeDriver가 필요합니다.

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
| v2.5 | 2026-07-06 | `is_error_page` 오탐 수정 (정상 페이지가 error로 skip 되던 문제) |
| v2.6 | 2026-07-08 | perf log로 메인 문서 HTTP status 감지 추가 (비영어 404가 `is_error_page`를 빠져나가 캡처되던 문제) |
| v2.7 | 2026-07-10 | perf log 활성화 후 `--headless=new` 가 빈 창을 띄우는 문제 → `--window-position` 으로 창을 화면 밖으로 이동 |

> 상세 이력은 메인 스크립트 헤더 주석 참고. 파일은 단일 파일로 관리되며 버전업 시 rename + 헤더 갱신.

## License

MIT
