# page_capture  
<sub>2026-06-18  Jonghyun Park w/ Claude</sub>  

Selenium 기반 웹 페이지 전체 캡처 자동화 도구입니다.  
PC / MO(모바일) 뷰를 각각 캡처하여 지정 폴더에 PNG 및 MHTML로 저장합니다.
URL이 많을 때는 `MAX_WORKERS` 개의 헤드리스 Chrome을 동시에 띄워 병렬로 캡처합니다.

## 파일 구성

| 파일 | 설명 |
|---|---|
| `page_capture_260618_v2.4.py` | 메인 캡처 스크립트 (단일 파일로 관리, 날짜는 최신 변경 시점) |
| `foldering_move_png.py` | 캡처된 PNG를 사이트코드별 하위 폴더로 정리 |

> 파일명은 `page_capture_YYMMDD_v메이저.마이너.py` 형식 — `YYMMDD`는 최신 변경 시점, `v메이저.마이너`는 변경 단위. 캠페인별 날짜는 파일명에 포함하지 않음 (의미 없는 suffix가 됨).

## 사용 방법

### 1. 설정 상수 수정
스크립트 상단의 `# 사용자가 바꿔야 하는 부분` 섹션에 출력 경로, 동시 실행 개수, 캡처 대상 도메인, URL 목록을 본인 환경에 맞게 변경합니다.

```python
OUTPUT_DIR = r"C:\Users\your_name\Downloads\captures"

MAX_WORKERS = 4                                      # 동시에 띄울 헤드리스 Chrome 개수 (1개당 ~300-500MB RAM, 보통 4~8)

TARGET_DOMAIN = "example.com"                        # 메인 글로벌 도메인
TARGET_DOMAIN_CN = ("example.com.cn", "example.cn")  # 중국 사이트 — 별도 사이트코드 'CN' 부여
TARGET_BRAND_KEYWORD = "example"                     # host 안에 이 키워드 들어가면 같은 브랜드로 인식
```

### 2. URL 목록 수정
스크립트 상단 `URLS` 상수에 캡처할 URL을 한 줄에 하나씩 입력합니다 (`#` 로 시작하면 주석 처리). URL 수 × (PC/MO) 작업이 `MAX_WORKERS` 개씩 병렬 처리됩니다.

### 3. 직접 실행

```bash
python page_capture_260618_v2.4.py
```

### 4. 작업 스케줄러 등록 (창 없이 백그라운드 실행)

> **`pythonw.exe` 사용 권장**  
> `python.exe`는 실행 시 cmd 창이 팝업됩니다.  
> 같은 경로의 `pythonw.exe`를 사용하면 창이 전혀 뜨지 않습니다.

#### CLI 등록

```bat
schtasks /create /tn page_capture ^
  /tr "\"C:\Python3xx\pythonw.exe\" \"C:\Users\user_name\...\page_capture_260618_v2.4.py\"" ^
  /sc daily /st 09:00 /it /f
```

#### GUI 등록

1. `taskschd.msc` 실행
2. **작업 만들기** → 일반 탭: 이름 입력, "사용자가 로그온할 때만 실행" 선택
3. **트리거** 탭 → 새로 만들기 → 반복 주기 설정
4. **동작** 탭 → 새로 만들기:
   - 프로그램/스크립트: `C:\Python3xx\pythonw.exe` (창 없이 실행; 일반 python.exe 쓰면 cmd 창 팝업됨)
   - 인수 추가: `"C:\Users\user_name\OneDrive - company_name\...\page_capture_260618_v2.4.py"`
5. **조건** 탭 → 전원 섹션 → **"AC 전원이 연결된 경우에만 작업 시작" 체크 해제**

### 5. PNG 정리
캡처 완료 후 `foldering_move_png.py`를 실행하면  
사이트코드별 하위 폴더로 자동 분류됩니다.

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

## License

MIT
