# page_capture_260720_v3.0.py
# 2026-04-17  Jonghyun Park w/ Claude  — v2.0 초기 버전
# 2026-04-20  Jonghyun Park w/ Claude  — v2.1 is_error_page 다국어 에러 감지 강화 + /common/404/ + Chrome ERR 감지
# 2026-04-29  Jonghyun Park w/ Claude  — v2.2 filename에 OUTPUT_DIR 변수 사용 + raw string 적용 + 파일명 정리(두 번째 날짜=캠페인 날짜 제거)
# 2026-05-22  Jonghyun Park w/ Claude  — v2.3 주석/예시 URL sanitize + 도메인 매칭 로직 상수화 (TARGET_DOMAIN / TARGET_DOMAIN_CN / TARGET_BRAND_KEYWORD) + 설정 상수 파일 상단으로 이동
# 2026-06-18  Jonghyun Park w/ Claude  — v2.4 캡처를 ThreadPoolExecutor 로 병렬화 (MAX_WORKERS) + URL 목록 상단 상수(URLS)로 이동
# 2026-06-19  Jonghyun Park w/ Claude  — v2.4 MAX_WORKERS 사양별 권장값 주석 보강
# 2026-07-06  Jonghyun Park w/ Claude  — v2.5 is_error_page 오탐 수정: aiscPrivateError 는 is_displayed 로, ERR_ 문자열은 title 빈 경우로 한정 (정상 페이지가 error_page 로 skip 되던 문제)
# 2026-07-08  Jonghyun Park w/ Claude  — v2.6 perf log 로 메인 문서 HTTP status 감지 추가 (비영어 404 가 is_error_page 를 빠져나가 캡처되던 문제)
# 2026-07-10  Jonghyun Park w/ Claude  — v2.7 perf log 활성화 후 --headless=new 가 빈 흰 창을 띄우는 문제 → --window-position 으로 창을 화면 밖으로 이동
# 2026-07-10  Jonghyun Park w/ Claude  — v2.8 PC 캡처 분기의 미정의 호출 is_sec_path → is_hq_path 로 수정(매 PC 캡처 NameError 로 skip 되던 문제) + OUTPUT_DIR 기본값을 captures 로 정리
# 2026-07-14  Jonghyun Park w/ Claude  — v2.9 unknown(soft-404) 페이지 skip 추가: 메인 도메인이 존재하지 않는 경로에 HTTP 200 + 홈 fallback 을 주는 경우 <meta property="og:url"> 이 비었거나(EMPTY) 아예 없음(MISSING) → is_unknown_page 로 감지해 skip (리다이렉트/HTTP status/기존 error 마커로 안 잡히던 200 케이스)
# 2026-07-20  Jonghyun Park w/ Claude  — v3.0 [버그] ① 출력 폴더 생성을 캡처 시작 전으로 이동(폴더가 없으면 PNG/MHTML 저장이 전량 실패하던 문제) ② URL 주석 필터를 strip 후 판정(들여쓴 '#' 줄이 URL 로 유입) ③ Chrome 생성을 try 안으로(기동 실패 시 결과 집계에서 통째로 누락) ④ bare except → except Exception (Ctrl+C 중단 가능) ⑤ page load/script timeout 추가(멈춘 서버가 워커를 무한 점유하는 것 방지)
# 2026-07-20  Jonghyun Park w/ Claude  — v3.0 [결과기록] 결과를 (url, device) 단위 result_*.csv 로 기록 — 기존 txt 3종은 URL 단위라 'PC 는 정상인데 MO 만 실패' 를 구분 못 했고 error/timeout 은 어디에도 안 남아 재실행 대상 파악이 불가능했다
# 2026-07-20  Jonghyun Park w/ Claude  — v3.0 [로그인화면 skip] 쿠키·팝업 처리 중 JS 로 늦게 로그인 페이지로 이동하는 경우 리다이렉트 판정(get 직후 1회)을 빠져나가 로그인 화면이 캡처물로 저장됐다 → 저장 직전 URL 재확인 + SKIP_URL_KEYWORDS (RECHECK_URL_BEFORE_SAVE)
# 2026-07-20  Jonghyun Park w/ Claude  — v3.0 [속도] 워커별 Chrome 재사용(REUSE_DRIVER) + 이어하기(SKIP_IF_EXISTS: 같은 날 PNG+MHTML 이 있으면 건너뜀) + 일시적 실패만 재시도(RETRY_COUNT) + MHTML 크기 검증(mhtml_failed)
# 2026-07-20  Jonghyun Park w/ Claude  — v3.0 [리다이렉트 정규화] 후행 슬래시만 무시하던 비교를 #fragment·추적파라미터(utm_*/gclid)·www·대소문자·기본포트·http↔https·퍼센트인코딩·쿼리순서까지 무시하도록 변경 (정상 페이지가 리다이렉트로 오탐돼 skip 되던 문제)
# 2026-07-20  Jonghyun Park w/ Claude  — v3.0 [CDP 전체캡처] Page.captureScreenshot(captureBeyondViewport) 경로를 추가했으나 스크롤로 띄운 지연 로딩 이미지가 렌더되기 전에 찍혀 이미지가 빠진 캡처가 나옴 → 기본 OFF(USE_CDP_FULLPAGE=False), 이미지 로딩 완료 대기를 넣기 전까지 켜지 말 것
#
# ── 캡처한 URL 확인법 (저장된 .mhtml) ──────────────────────────────
# 저장된 .mhtml 을 텍스트 에디터(메모장 등)로 열면 맨 위 MIME 헤더 2번째 줄
#   Snapshot-Content-Location: <실제 캡처된 URL>
# 이 Chrome 이 캡처 시점에 기록한 메인 문서 URL (쿼리 파라미터까지 보존).
# Subject = 페이지 타이틀, Date = 캡처 시각도 같이 기록됨.
# ⚠ 본문 안의 href(예: AudioEye skip-link href="...#content")는 JS 가 동적 생성한
#   링크라 보통 일치하긴 하나 정식 기록이 아님 — 반드시 위 헤더를 볼 것.
# (이 스크립트는 driver.current_url 이 요청 URL 과 다르면(리다이렉트) 저장 자체를
#  skip 하므로, Snapshot-Content-Location = 요청한 URL 이 보장됨)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from urllib.parse import urlparse, parse_qsl, urlencode, unquote
import time
from PIL import Image
import io
import re
import os
import json
import csv
import base64
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# ════ 사용자가 바꿔야 하는 부분 (상단 설정) ════
# 저장 경로
OUTPUT_DIR = r"C:\Users\user_name\Downloads\captures"

# 동시에 띄울 헤드리스 Chrome 개수. 브라우저 1개당 ~300-500MB RAM.
# 한계: ① RAM (워커수 × ~0.5GB) ② CPU 논리프로세서 수(초과분은 효과 없이 task당 시간만 늘어남)
#       ③ 대상 서버 throttle(너무 많이 동시 요청 시 리다이렉트/타임아웃 헛 skip ↑)
# → 무한정 못 올림. 보통 "논리프로세서 수" 와 "여유 RAM ÷ 0.5GB" 중 작은 값 근처가 상한.
#
# 사양별 권장값:
#   • 이 PC (6코어/12논리, RAM 31GB)            → 8~10 권장 (현재 작업 기준 10이 적정 상한)
#   • 16GB RAM / 4코어8논리 노트북              → 4~6
#   • 8GB RAM 저사양                            → 2~4 (그 이상은 스왑으로 오히려 느려짐)
#   • 32GB+ / 8코어16논리 이상 데스크탑          → 12~14
# (OneDrive·엑셀·브라우저 등 다른 앱이 떠 있으면 여유 RAM 이 줄어드니 1~2 낮춰 잡을 것)
MAX_WORKERS = 4

# 페이지 로딩 제한 시간(초). 초과하면 그 (url, device) 는 timeout 실패로 기록하고 다음 작업으로 넘어간다.
# (미설정 시 서버가 hang 하면 워커 1개가 무한정 물려 전체 진행이 막힘)
# ⚠ 목적은 "느린 페이지 거르기"가 아니라 "멈춘 서버가 워커를 무한 점유하는 것 막기" — 넉넉히 잡을 것.
#   정상 페이지 단독 로드는 2~5초지만, MAX_WORKERS 개를 동시에 띄우면 CPU·대역폭 경합으로
#   같은 페이지가 10초를 훌쩍 넘긴다(10초로 잡았다가 정상 site 다수가 죽는 것을 확인, 2026-07-20).
PAGE_LOAD_TIMEOUT = 60
# execute_script / execute_async_script 제한 시간(초)
SCRIPT_TIMEOUT = 30

# ── 로그인/인증 화면 캡처 제외 ────────────────────────────────
# 리다이렉트 판정은 driver.get() 직후 1회뿐이라, 쿠키·팝업 처리 중 JS 로 "늦게" 튀는
# 로그인 페이지(/auth/multistore 등)는 판정을 통과한 뒤 이동해 그대로 저장돼 버린다.
# (2026-07-20 확인: 그날 저장분 90개 중 7개가 로그인 화면 — EG/SA/SA_EN/UA/VN)
# True 면 저장 직전에 current_url 을 한 번 더 확인해 걸러낸다.
RECHECK_URL_BEFORE_SAVE = True
# 최종 URL 에 아래 조각이 들어가면 캡처하지 않고 skip (result = login_page)
SKIP_URL_KEYWORDS = ["/auth/", "/login", "/signin", "/sign-in"]

# ── 리다이렉트 판정 정규화 ────────────────────────────────────
# 요청 URL 과 최종 URL 을 비교할 때 "사실상 같은 페이지"인 차이는 무시한다.
# (예전엔 후행 슬래시만 무시해서, #fragment 나 utm_* 가 붙기만 해도 리다이렉트로 보고 skip 했다)
# 아래 파라미터는 페이지 내용과 무관한 추적용이라 비교에서 제외한다.
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "gclid", "fbclid", "msclkid", "igshid", "mc_cid", "mc_eid", "_ga", "_gl",
    "cid", "CID", "campaign", "src", "source",
}
# www. 유무 차이를 무시할지 (www.example.com ↔ example.com 은 같은 페이지로 본다)
IGNORE_WWW_IN_COMPARE = True

# ── 속도 옵션 ────────────────────────────────────────────────
# 워커(스레드)마다 Chrome 을 1개만 띄우고 URL 이 바뀌어도 재사용한다.
# 끄면 예전처럼 (url, device) 마다 새로 기동 — 기동에만 건당 3~10초가 든다.
REUSE_DRIVER = True
# 이미 같은 이름의 PNG+MHTML 이 있으면 건너뛴다 (중단 후 이어하기).
# 파일명에 날짜(%m%d)가 들어가므로 "같은 날 재실행분만" 건너뛴다.
SKIP_IF_EXISTS = True
# 캡처 실패(timeout/error) 시 재시도 횟수. 404·리다이렉트 등 판정 결과는 재시도하지 않는다.
RETRY_COUNT = 1
# 전체 페이지 캡처를 CDP(captureBeyondViewport)로 한다.
# 끄면 기존 방식(PC=창 늘리기 / MO=스크롤 스티칭) 사용.
# ⚠ 현재 False 가 정답 — CDP 는 스크롤로 띄운 레이지 로딩 이미지가 렌더되기 전에 찍혀
#   제품 이미지가 통째로 빠진 캡처가 나온다(2026-07-20 TW/BR/HK MO 에서 확인).
#   높이는 CDP 쪽이 정확하지만(중복 접합·하단 여백 없음) 내용이 비므로 쓸 수 없다.
#   → 이미지 로딩 완료를 기다리는 로직을 넣기 전까지는 켜지 말 것.
USE_CDP_FULLPAGE = False
# CDP 캡처 최대 높이(px). 너무 긴 페이지는 Chrome 렌더 한계·메모리 문제로 잘라낸다.
MAX_CAPTURE_HEIGHT = 30000
# MHTML 최소 크기(byte). 이보다 작으면 저장 실패로 보고 result=mhtml_failed 로 남긴다.
MIN_MHTML_BYTES = 20000
# get() 후 렌더 안정화 대기 상한(초). readyState 가 complete 면 더 안 기다린다.
PAGE_SETTLE_TIMEOUT = 8

# ── 대상 도메인 ──────────────────────────────────────────────
# ⚠ 도메인 문자열을 함수 본문에 직접 쓰지 말 것.
#   여기 상수만 바꾸면 다른 브랜드·사이트에도 그대로 쓸 수 있고,
#   공개 저장소에 올릴 때 이 몇 줄만 교체하면 로직이 안 깨진다.
#   (함수 안에 박아두면 문자열 치환 시 조건이 조용히 항상 False 가 되어
#    get_site_type / is_hq_path / is_unknown_page 가 티 없이 오작동한다)
TARGET_DOMAIN = "example.com"                      # 메인 도메인 (shop./www. 등 서브도메인 포함해 endswith 로 판정)
TARGET_DOMAIN_CN = ("example.com.cn", "example.cn")  # 중국 등 별도 도메인 → sitecode 를 CN 으로
TARGET_BRAND_KEYWORD = "example"                           # 위에 안 걸리는 브랜드 host 판정용 (host 안에 포함되는지)
# soft-404(og:url) 검사 대상 host — 메인 도메인의 루트/www 만 (shop.* 등은 원래 og:url 이 없어 오탐)
OG_CHECK_HOSTS = {TARGET_DOMAIN, f"www.{TARGET_DOMAIN}"}
# 국가 코드 대신 이 경로로 시작하면 본사(HQ) 페이지 — 렌더가 느려 추가 대기가 필요
HQ_SITE_CODE = "hq"

# ── 뷰포트 / User-Agent ──────────────────────────────────────
DESKTOP_VIEWPORT = (1920, 1080)
MOBILE_VIEWPORT = (390, 844)
MOBILE_SCALE = 3          # 모바일 deviceScaleFactor (레티나 배율)
MOBILE_UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 '
             '(KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1')

# 캡처할 URL 목록 (한 줄에 하나, # 로 시작하면 주석 처리)
# https:// 필수 작성 필요
URLS = """
https://www.example.com/nz/offer/campaign-name-gift-ideas
https://www.example.com/vn/offer/campaign-name
"""
# ═══════════════════════════════════════════

# =========================
# 파일명 / 경로 관련 유틸
# =========================
def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]+', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:120] if len(name) > 120 else name

def extract_last_slug(parts):
    for seg in reversed(parts):
        s = seg.strip()
        if not s:
            continue
        s = s.split('?')[0].split('#')[0]
        s = re.sub(r'\.html?$','', s, flags=re.I)
        return s
    return 'page'

def normalize_url_for_compare(u: str) -> str:
    """리다이렉트 판정용 정규화. '사실상 같은 페이지'면 같은 문자열이 되도록 만든다.

    무시하는 차이: 대소문자(scheme/host), 기본 포트, www., #fragment,
                   후행 슬래시, 추적 파라미터(utm_* 등), 쿼리 순서, 퍼센트 인코딩.
    경로 자체가 달라지는 진짜 리다이렉트(/auth/multistore 등)는 그대로 다르게 남는다.
    """
    if not u:
        return ""
    try:
        p = urlparse(u.strip())
        host = (p.hostname or "").lower()
        if IGNORE_WWW_IN_COMPARE and host.startswith("www."):
            host = host[4:]
        # 기본 포트는 표기 차이일 뿐이라 제거
        port = p.port
        if port and not ((p.scheme == "https" and port == 443) or (p.scheme == "http" and port == 80)):
            host = f"{host}:{port}"
        path = unquote(p.path).rstrip("/")
        # 추적 파라미터 제거 + 나머지는 순서 무관하게 정렬
        qs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
              if k.lower() not in {t.lower() for t in TRACKING_PARAMS}]
        query = urlencode(sorted(qs))
        # scheme 은 http/https 차이를 무시 (같은 페이지의 프로토콜 승격일 뿐)
        return f"{host}{path}?{query}" if query else f"{host}{path}"
    except Exception:
        return (u or "").rstrip("/")

def get_site_type(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace('www.', '')
    parts = [p for p in parsed.path.split('/') if p]

    if host in TARGET_DOMAIN_CN:
        if len(parts) <= 1:
            return 'home'
        return extract_last_slug(parts)

    if host.endswith(TARGET_DOMAIN):
        if len(parts) <= 1:
            return 'home'
        return extract_last_slug(parts)

    if TARGET_BRAND_KEYWORD in host:
        if len(parts) == 0:
            return 'home'
        return extract_last_slug(parts)

    st = extract_last_slug(parts) or 'home'
    return st if st else 'home'

def get_page_info(url):
    """사이트코드, 페이지명, sitetype 추출"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/').split('/')

    if any(d in domain for d in TARGET_DOMAIN_CN):
        sitecode = 'CN'
        page_path = '_'.join(p for p in path if p) if path else 'page'

    else:
        sitecode = path[0].upper() if len(path) > 0 and path[0] else 'GLOBAL'
        page_path = '_'.join(p for p in path[1:] if p) if len(path) > 1 else 'page'

    sitetype = get_site_type(url)
    return sitecode, page_path, sitetype

# =========================
# 대기/팝업 관련 유틸
# =========================
def close_popups(driver):
    try:
        close_buttons = [
            "button[aria-label*='close']", "button.close", ".close-button",
            "[class*='close']", "button[title*='Close']", "svg[class*='close']",
        ]
        for selector in close_buttons:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        print("  ✅ 팝업 닫기")
                        time.sleep(1)
            except Exception:
                continue
    except Exception:
        pass

def accept_cookies(driver):
    try:
        time.sleep(3)
        cookie_selectors = [
            "#truste-consent-button",
            "button[id*='accept']", "button[class*='accept']", ".truste-button",
        ]
        for selector in cookie_selectors:
            try:
                for btn in driver.find_elements(By.CSS_SELECTOR, selector):
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        print("  ✅ 쿠키 동의 완료")
                        time.sleep(2)
                        return True
            except Exception:
                continue

        for text in ['Accept All','Accept','Accetta','Continua','동의','수락','Agree']:
            try:
                els = driver.find_elements(By.XPATH, f"//*[contains(., '{text}')]")
                for el in els:
                    if el.is_displayed() and el.tag_name in ['button','a']:
                        driver.execute_script("arguments[0].click();", el)
                        print(f"  ✅ '{text}' 클릭 완료")
                        time.sleep(2)
                        return True
            except Exception:
                continue
        print("  ⚠️ 쿠키 버튼 없음")
        return False
    except Exception as e:
        print(f"  ⚠️ 쿠키 처리 에러: {e}")
        return False

def is_hq_path(url: str) -> bool:
    p = urlparse(url)
    host = p.netloc.lower().replace('www.', '')
    parts = [x for x in p.path.split('/') if x]
    return host.endswith(TARGET_DOMAIN) and len(parts) >= 1 and parts[0] == HQ_SITE_CODE

def wait_dom_settled(driver, timeout=20):
    end = time.time() + timeout
    stable = 0
    last = -1
    while time.time() < end:
        h = driver.execute_script("return document.body ? document.body.scrollHeight : 0")
        if abs(h - last) < 10:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last = h
        time.sleep(0.8)

def wait_key_elements(driver, timeout=15):
    sels = [".cp-hero-kv", ".kv-wrpr", "#gnb", "header", "footer"]
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: any(len(d.find_elements(By.CSS_SELECTOR, s))>0 for s in sels)
        )
    except Exception:
        pass

# =========================
# 에러 페이지 감지
# =========================
# company_name 에러 페이지: <title>error | company_name Gulf</title> 등
# HTTP 에러: <title>502 Bad Gateway</title> 등
_ERROR_TITLE_KEYWORDS = ['error', '404', '502', '503', 'bad gateway', 'page not found', 'not available']

def is_error_page(driver) -> bool:
    """에러/없는 페이지 여부 판단 (title + canonical URL + HQ 전용 요소)"""
    # 1. 영어 title 키워드 (기존)
    try:
        title = driver.title.lower().strip()
        if any(kw in title for kw in _ERROR_TITLE_KEYWORDS):
            return True
    except Exception:
        pass

    # 2. company_name 공통 에러 페이지: canonical URL에 /common/error/ 또는 /common/404/ 포함
    try:
        canonical = driver.execute_script(
            "var el=document.querySelector('link[rel=\"canonical\"]'); return el?el.href:'';"
        )
        if canonical and any(p in canonical for p in ('/common/error/', '/common/404/')):
            return True
    except Exception:
        pass

    # 3. HQ(한국) 전용 에러 구조: aiscPrivateError 요소가 "실제로 표시"된 경우만
    #    ⚠ 정상 HQ 페이지도 이 에러 컨테이너를 hidden 으로 DOM 에 품고 있어,
    #      find_elements(존재 여부)만 보면 정상 페이지가 오탐되어 skip 된다.
    #      → is_displayed() 로 화면에 실제 노출된 경우로 한정.
    try:
        if any(e.is_displayed() for e in driver.find_elements(By.ID, 'aiscPrivateError')):
            return True
    except Exception:
        pass

    # 4. Chrome 브라우저 에러 페이지 (ERR_TOO_MANY_REDIRECTS 등 네트워크 에러)
    #    ⚠ 정상 페이지 본문/스크립트에 ERR_ 문자열이 우연히 있어도 오탐하지 않도록,
    #      Chrome 에러 인터스티셜(=title 이 비어있음)인 경우로 한정.
    try:
        src = driver.page_source
        if src and not (driver.title or '').strip() and any(e in src for e in ('ERR_TOO_MANY_REDIRECTS', 'ERR_CONNECTION', 'ERR_NAME_NOT_RESOLVED', 'ERR_TIMED_OUT')):
            return True
    except Exception:
        pass

    return False

def get_main_document_status(driver, final_url):
    """perf log에서 메인 문서(Document) 응답의 HTTP status 반환. 못 찾으면 None.
    Selenium 은 status 를 직접 안 줘서, chromedriver 의 performance log 로
    Network.responseReceived 이벤트를 파싱해 메인 프레임 응답 코드를 얻는다."""
    def _n(u): return (u or "").split('#')[0].rstrip('/')
    target = _n(final_url)
    status = None
    try:
        for entry in driver.get_log("performance"):
            try:
                msg = json.loads(entry["message"])["message"]
            except Exception:
                continue
            if msg.get("method") != "Network.responseReceived":
                continue
            p = msg.get("params", {})
            if p.get("type") != "Document":           # iframe/XHR 제외, 메인 문서만
                continue
            resp = p.get("response", {})
            if _n(resp.get("url")) == target:          # 최종 문서 url 매칭
                status = resp.get("status")            # 여러 개면 마지막(최종) 사용
    except Exception:
        pass
    return status

def is_unknown_page(driver, url) -> bool:
    """존재하지 않는 캠페인 경로에 대해 메인 도메인이 HTTP 200 + 홈 fallback 을
    돌려주는 "알 수 없는 페이지" 감지. 정상 마케팅 페이지는 <meta property="og:url"> 이
    실제 URL 로 채워지지만, unknown 페이지는 그 값이 비어있거나(EMPTY) 태그가 아예 없다(MISSING).
    → 리다이렉트/HTTP status/기존 error 마커로는 안 잡히는(200) 케이스를 여기서 걸러 skip.
    (기존 캡처 대조: HQ 10 + PS/SG/TH/TR/TW/UA/UZ_RU/UZ_UZ/VN/ZA 22 = 32개 정확히 감지, 정상 87 오탐 0)
    """
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    # 검사 대상은 메인 도메인 루트/www 만 (shop.* / example-partner / *.com.cn 등은
    # 원래 og:url 이 없을 수 있어 제외 — 오탐 방지)
    if host not in OG_CHECK_HOSTS:
        return False
    try:
        og = driver.execute_script(
            "var el=document.querySelector('meta[property=\"og:url\"]');"
            "return el ? (el.getAttribute('content') || '') : '__MISSING__';"
        )
    except Exception:
        return False
    return og == '__MISSING__' or (og or '').strip() == ''

# =========================
# 스크린샷 / 스크롤
# =========================
def screenshot_png(driver): return driver.get_screenshot_as_png()

def looks_blank(png_bytes):
    img = Image.open(io.BytesIO(png_bytes)).convert("L")
    arr = np.array(img)
    if arr.size == 0: return True
    nonwhite = np.sum(arr < 250)
    return (nonwhite / arr.size) < 0.005

def capture_full_page_mobile(driver, width):
    driver.execute_script("window.scrollTo(0,0);")
    time.sleep(2)
    total_height = driver.execute_script("return document.body.scrollHeight")
    vh = driver.execute_script("return window.innerHeight")
    screenshots = []
    offset, overlap = 0, 100
    while offset < total_height:
        driver.execute_script(f"window.scrollTo(0,{offset});")
        time.sleep(2)
        png = driver.get_screenshot_as_png()
        screenshots.append(Image.open(io.BytesIO(png)))
        offset += vh - overlap
        if offset + vh > total_height: break
    if len(screenshots)==1: return screenshots[0]
    fw = screenshots[0].width
    fh = sum(i.height for i in screenshots) - overlap*(len(screenshots)-1)
    final = Image.new('RGB', (fw, fh))
    y = 0
    for i,img in enumerate(screenshots):
        if i>0: img = img.crop((0, overlap, fw, img.height))
        final.paste(img, (0,y))
        y += img.height - (overlap if i<len(screenshots)-1 else 0)
    return final

def smooth_scroll_desktop(driver):
    last = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new = driver.execute_script("return document.body.scrollHeight")
        if new == last: break
        last = new
    return last

# =========================
# Chrome 드라이버 (워커별 재사용)
# =========================
# 태스크는 device 순으로 정렬해 넣으므로, 한 스레드는 대개 같은 device 를 연속 처리한다.
# device 가 바뀌는 순간에만 기존 driver 를 닫고 새로 만든다(= 동시 Chrome 수는 워커 수와 같음).
_tls = threading.local()
_all_drivers = []                 # 종료 시 일괄 정리용
_all_drivers_lock = threading.Lock()

def _build_options(device_type):
    o = Options()
    o.add_argument('--headless=new')
    o.add_argument('--disable-gpu')
    o.add_argument('--no-sandbox')
    o.add_argument('--disable-dev-shm-usage')
    o.add_argument('--hide-scrollbars')
    # perf log(goog:loggingPrefs) 활성화 후 --headless=new 가 빈 창을 띄우는 현상 방지 → 창을 화면 밖으로
    o.add_argument('--window-position=-32000,-32000')
    if device_type == "MO":
        o.add_argument(f'--user-agent={MOBILE_UA}')
        vw, vh = MOBILE_VIEWPORT
    else:
        vw, vh = DESKTOP_VIEWPORT
    o.add_argument(f'--window-size={vw},{vh}')
    # perf log 활성화 → Network.responseReceived 로 메인 문서 HTTP status 획득 (404 감지용)
    o.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return o, vw, vh

def _new_driver(device_type):
    o, vw, vh = _build_options(device_type)
    d = webdriver.Chrome(options=o)
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    d.set_script_timeout(SCRIPT_TIMEOUT)
    if device_type == "MO":
        d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            'width': vw, 'height': vh, 'deviceScaleFactor': MOBILE_SCALE, 'mobile': True
        })
    with _all_drivers_lock:
        _all_drivers.append(d)
    return d, vw, vh

def get_driver(device_type):
    """이 스레드가 쓸 driver 를 돌려준다. REUSE_DRIVER 면 재사용, 아니면 매번 새로."""
    if not REUSE_DRIVER:
        return _new_driver(device_type)
    cur = getattr(_tls, "driver", None)
    if cur is not None and getattr(_tls, "device", None) == device_type:
        try:
            # 세션이 살아있는지 확인 (죽었으면 예외 → 새로 만든다)
            _ = cur.current_url
            # ── URL 간 상태 격리 ──
            # 쿠키를 남기면 쿠키배너 클릭 여부·로그인 상태가 다음 URL 판정을 바꾼다.
            # perf log 도 비워야 다음 URL 의 HTTP status 를 잘못 읽지 않는다.
            try: cur.delete_all_cookies()
            except Exception: pass
            try: cur.get_log("performance")   # 읽어서 비움
            except Exception: pass
            return cur, _tls.vw, _tls.vh
        except Exception:
            _quit_driver(cur)
    elif cur is not None:
        _quit_driver(cur)                     # device 가 바뀌면 닫고 새로
    d, vw, vh = _new_driver(device_type)
    _tls.driver, _tls.device, _tls.vw, _tls.vh = d, device_type, vw, vh
    return d, vw, vh

def _quit_driver(d):
    if d is None:
        return
    try:
        d.quit()
    except Exception:
        pass
    with _all_drivers_lock:
        if d in _all_drivers:
            _all_drivers.remove(d)

def drop_thread_driver():
    """현재 스레드의 driver 를 버린다 (세션이 깨졌을 때 다음 시도에서 새로 만들도록)."""
    _quit_driver(getattr(_tls, "driver", None))
    _tls.driver = None

def quit_all_drivers():
    with _all_drivers_lock:
        drivers = list(_all_drivers)
    for d in drivers:
        _quit_driver(d)

# =========================
# CDP 전체 페이지 캡처
# =========================
def capture_fullpage_cdp(driver):
    """CDP 로 전체 페이지를 한 번에 캡처해 PNG bytes 반환. 실패하면 None.
    스크롤 스티칭(조각 합성)·창 크기 늘리기를 모두 대체한다."""
    try:
        m = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        size = m.get("cssContentSize") or m.get("contentSize") or {}
        w = int(size.get("width") or 0)
        h = int(size.get("height") or 0)
        if w <= 0 or h <= 0:
            return None
        if h > MAX_CAPTURE_HEIGHT:
            print(f"  ⚠️ 페이지가 너무 김({h}px) → {MAX_CAPTURE_HEIGHT}px 로 잘라 캡처")
            h = MAX_CAPTURE_HEIGHT
        res = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
        })
        data = res.get("data") or ""
        return base64.b64decode(data) if data else None
    except Exception as e:
        print(f"  ⚠️ CDP 캡처 실패 → 기존 방식으로 대체: {e}")
        return None

def build_output_paths(url, device_type, timestamp):
    """이 (url, device) 가 저장될 PNG/MHTML 경로. 브라우저 없이 계산 가능해야
    resume(이미 있으면 skip) 판정을 기동 전에 할 수 있다."""
    sitecode, page_path, _ = get_page_info(url)
    parsed = urlparse(url)
    # 쿼리 파라미터 있는 경우 파일명에 포함
    # (ex: ES_PC_offer_black-friday_page_category-tv-audio_1112.png / 없으면 ES_PC_offer_black-friday_page_1112.png)
    query_part = parsed.query.replace('=', '-').replace('&', '_') if parsed.query else ''
    if query_part:
        base = safe_filename(f'{sitecode}_{device_type}_{page_path}_page_{query_part}_{timestamp}.png')
    else:
        base = safe_filename(f'{sitecode}_{device_type}_{page_path}_page_{timestamp}.png')
    png = f"{OUTPUT_DIR}/{base}"
    return png, png[:-4] + ".mhtml"

def wait_page_settled(driver, timeout=None):
    """readyState 가 complete 될 때까지만 기다린다 (고정 sleep 대체)."""
    timeout = PAGE_SETTLE_TIMEOUT if timeout is None else timeout
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        pass

# =========================
# 메인 캡처 함수
# =========================
def capture_page(url, device_type):
    """캡처 1건 수행. 결과를 dict 로 반환 (result_*.csv 한 행에 대응).
    result: ok / redirected / error_page / unknown_page / timeout / error"""
    sitecode, page_path, sitetype = get_page_info(url)
    page_name = safe_filename(f"{sitecode}_{page_path}")
    timestamp = datetime.now().strftime("%m%d")

    # ── 결과 기록용 — 어느 디바이스가 왜 skip 됐는지 사후 검수 가능하게 남긴다 ──
    started = time.time()
    info = {"url": url, "device": device_type, "sitecode": sitecode, "result": "",
            "final_url": "", "http_status": "", "title": "", "detail": "", "elapsed": 0.0}

    def _ret(result, detail=""):
        info["result"] = result
        info["detail"] = detail
        info["elapsed"] = round(time.time() - started, 1)
        return info

    # ── 이어하기(resume) — 이미 받은 건 브라우저를 띄우지도 않는다 ──
    png_path, mhtml_path = build_output_paths(url, device_type, timestamp)
    if SKIP_IF_EXISTS and os.path.exists(png_path) and os.path.exists(mhtml_path):
        print(f"  ⏩ 이미 있음 → skip: {os.path.basename(png_path)}")
        return _ret("exists", "PNG/MHTML 이미 존재")

    # ⚠ Chrome 확보도 try 안에서 — 기동 자체가 실패해도 결과 집계를 타게 한다
    #   (밖에 두면 예외가 capture_page 밖으로 튀어 그 작업이 결과에서 통째로 사라짐)
    driver = None
    try:
        driver, vw, vh = get_driver(device_type)
        print(f"  📸 {device_type} 버전 캡처 중...")
        driver.get(url)
        wait_page_settled(driver)

        # ── 리다이렉트 감지 ──────────────────────────────────────
        final_url = driver.current_url
        info["final_url"] = final_url
        try:
            info["title"] = (driver.title or "").strip()
        except Exception:
            pass
        _norm = normalize_url_for_compare   # 추적파라미터·fragment·www 등 무시하고 비교
        def _login_hit(u):
            """로그인/인증 화면 URL 이면 걸린 키워드를 돌려준다 (아니면 None)"""
            if not RECHECK_URL_BEFORE_SAVE:
                return None
            return next((k for k in SKIP_URL_KEYWORDS if k in (u or "").lower()), None)

        # 로그인 화면은 리다이렉트보다 먼저 판정 — 같은 skip 이라도 사유를 구분해 따로 집계한다
        _hit = _login_hit(final_url)
        if _hit:
            print(f"  🔒 로그인/인증 화면 감지 → skip")
            print(f"      이동: {final_url}")
            return _ret("login_page", f"URL 에 '{_hit}' 포함")
        if _norm(final_url) != _norm(url):
            print(f"  ⏭️  리다이렉트 감지 → skip")
            print(f"      원본: {url}")
            print(f"      이동: {final_url}")
            return _ret("redirected", "final_url != url")

        # ── HTTP 상태코드 감지 (404/5xx) — 언어·마크업 무관 ──────
        # Selenium 은 status 를 직접 안 줘서 perf log 로 메인 문서 응답 status 확인.
        # HQ 처럼 한국어 error 페이지라 is_error_page 가 못 잡는 진짜 404 를 잡는다.
        status = get_main_document_status(driver, final_url)
        info["http_status"] = "" if status is None else status
        if status is not None and status >= 400:
            print(f"  ⛔ HTTP {status} 감지 → skip")
            return _ret("error_page", f"HTTP {status}")

        # ── 에러 페이지 감지 (404 / 502 / company_name error 등) ─────
        if is_error_page(driver):
            print(f"  ⛔ 에러 페이지 감지 (title: '{driver.title}') → skip")
            return _ret("error_page", "is_error_page")

        # ── unknown(soft-404) 페이지 감지 (HTTP 200 인데 og:url 없음 → 홈 fallback) ─
        # 존재하지 않는 캠페인 경로가 200 을 주고 홈 컨텐츠를 렌더해 위 감지들을 다 빠져나가는 케이스.
        if is_unknown_page(driver, final_url):
            print(f"  ⛔ unknown 페이지 감지 (og:url 비었음/없음, title: '{driver.title}') → skip")
            return _ret("unknown_page", "og:url EMPTY/MISSING")

        close_popups(driver)
        accept_cookies(driver)
        time.sleep(2)
        close_popups(driver)

        # ── 저장 직전 URL 재확인 (지연 리다이렉트 / 로그인 화면 차단) ──────
        # 위 리다이렉트 판정은 get() 직후 1회뿐이라, 쿠키·팝업 처리 중 JS 로 늦게 이동하는
        # 로그인 페이지가 그대로 저장된다(캡처된 mhtml 의 Snapshot-Content-Location 으로 확인 가능).
        if RECHECK_URL_BEFORE_SAVE:
            cur = driver.current_url
            hit = _login_hit(cur)
            if hit:
                info["final_url"] = cur
                print(f"  🔒 로그인/인증 화면 감지(저장 직전) → skip")
                print(f"      이동: {cur}")
                return _ret("login_page", f"저장 직전 재확인 · URL 에 '{hit}' 포함")
            if _norm(cur) != _norm(url):
                info["final_url"] = cur
                print(f"  ⏭️  지연 리다이렉트 감지(저장 직전) → skip")
                print(f"      이동: {cur}")
                return _ret("redirected", "저장 직전 재확인에서 이동 감지")

        filename, mhtml_filename = png_path, mhtml_path

        if is_hq_path(url):
            wait_dom_settled(driver)
            wait_key_elements(driver)

        png = None
        if USE_CDP_FULLPAGE:
            # 레이지 로딩 이미지를 띄우려면 한 번은 끝까지 훑어야 한다
            smooth_scroll_desktop(driver)
            driver.execute_script("window.scrollTo(0,0)")
            png = capture_fullpage_cdp(driver)

        if png is None:
            # ── 기본 경로: 기존 방식 (PC=창 늘리기 / MO=스크롤 스티칭) ──
            if device_type == "MO":
                # capture_full_page_mobile 이 스스로 끝까지 스크롤하며 찍으므로
                # 여기서 smooth_scroll_desktop 을 또 돌리면 시간만 두 배로 든다.
                img = capture_full_page_mobile(driver, vw)
                img.save(filename, 'PNG', optimize=True)
            else:
                total_h = smooth_scroll_desktop(driver)
                driver.set_window_size(vw, min(total_h + 200, MAX_CAPTURE_HEIGHT))
                time.sleep(2)
                png = screenshot_png(driver)

        if png is not None:
            # blank 재시도는 PC/MO 공통 적용 (예전엔 PC 에만 있었다)
            retry = 2
            while looks_blank(png) and retry > 0:
                print("  ⚠️ 화면이 비어 보여 재시도...")
                time.sleep(4)
                wait_dom_settled(driver)
                png2 = capture_fullpage_cdp(driver) if USE_CDP_FULLPAGE else None
                png = png2 if png2 is not None else screenshot_png(driver)
                retry -= 1
            with open(filename, "wb") as f:
                f.write(png)
        print(f"  ✅ 저장: {filename}")

        # ── MHTML 저장 ────────────────────────────────────────
        # fallback 으로 창을 늘렸다면 원래 뷰포트로 복원 (그 상태로 CDP 호출 시 blank 발생)
        if device_type != "MO":
            driver.set_window_size(vw, vh)
        driver.execute_script("window.scrollTo(0,0)")
        result = driver.execute_cdp_cmd("Page.captureSnapshot", {"format": "mhtml"})
        mhtml_data = result.get("data", "")
        if not mhtml_data or len(mhtml_data) < MIN_MHTML_BYTES:
            # PNG 는 남았는데 MHTML 만 실패한 경우 — 결과와 산출물이 어긋나지 않게 따로 표시
            print(f"  ⚠️ MHTML 이 비었거나 너무 작음({len(mhtml_data)}B)")
            return _ret("mhtml_failed", f"mhtml {len(mhtml_data)}B < {MIN_MHTML_BYTES}B")
        with open(mhtml_filename, "wb") as mf:  # bytes 쓰기 (텍스트 모드 시 blank 가능)
            mf.write(mhtml_data.encode("utf-8"))
        print(f"  ✅ MHTML 저장: {mhtml_filename}")
        return _ret("ok")

    except TimeoutException as e:
        # PAGE_LOAD_TIMEOUT / SCRIPT_TIMEOUT 초과 — 실패로 확정하고 다음 작업으로
        print(f"  ⏱️  타임아웃({PAGE_LOAD_TIMEOUT}초) → skip: {url}")
        # 재사용 driver 는 로딩이 걸린 채로 남아 다음 URL 까지 망칠 수 있으니 로딩을 끊는다
        try:
            driver.execute_script("window.stop();")
        except Exception:
            drop_thread_driver()
        return _ret("timeout", str(e).split('\n')[0][:200])
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback; traceback.print_exc()
        # 재사용 중인 driver 가 깨졌을 수 있으니 버린다 (다음 작업은 새 Chrome 으로)
        drop_thread_driver()
        return _ret("error", f"{type(e).__name__}: {e}".split('\n')[0][:200])
    finally:
        # 재사용 모드에선 여기서 닫지 않는다 (전체 종료 시 quit_all_drivers 로 일괄 정리)
        if driver is not None and not REUSE_DRIVER:
            _quit_driver(driver)

# =========================
# 여러 URL 병렬 캡처
# =========================
def capture_urls(urls, max_workers=MAX_WORKERS):
    # ⚠ 저장 폴더는 반드시 캡처 시작 "전"에 만든다.
    #   (예전엔 모든 캡처가 끝난 뒤에 만들어서, 폴더가 없으면 PNG/MHTML 저장이 전량 실패했다)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if isinstance(urls,str):
        # strip 을 먼저 하고 '#' 판정 — 안 그러면 "  # 주석" 처럼 들여쓴 주석줄이 URL 로 들어간다
        _lines = [u.strip() for u in urls.split('\n')]
        urls = [u for u in _lines if u and not u.startswith('#')]
    # (url, device) 단위 태스크 — PC/MO 는 서로 독립이라 각각 별도 브라우저로 병렬 처리
    # ⚠ device 로 묶어서 넣는다: driver 재사용 시 한 스레드가 같은 device 를 연속 처리해야
    #   device 가 바뀔 때마다 Chrome 을 새로 띄우는 일이 없다.
    tasks = [(u, dev) for dev in ("PC", "MO") for u in urls]
    print(f"\n🚀 총 {len(urls)}개 페이지 × (PC/MO) = {len(tasks)}개 작업 병렬 캡처 시작 (동시 {max_workers}개)\n")

    results = {}            # url -> {device: result 문자열}
    rows = []               # result_*.csv 용 (url, device) 단위 상세 행
    progress = {"n": 0}
    lock = threading.Lock()

    # 일시적 실패(네트워크/타임아웃/세션 끊김)만 재시도. 404·리다이렉트 등 "판정 결과"는 재시도해도 같다.
    RETRYABLE = {"timeout", "error", "mhtml_failed"}

    def _run(task):
        u, dev = task
        info = capture_page(u, dev)
        for attempt in range(1, RETRY_COUNT + 1):
            if info["result"] not in RETRYABLE:
                break
            print(f"  🔁 재시도 {attempt}/{RETRY_COUNT} ({info['result']}): {dev} {u}")
            drop_thread_driver()          # 깨진 세션을 물고 재시도하지 않도록
            info = capture_page(u, dev)
            info["detail"] = (info["detail"] + f" | retry {attempt}").strip(" |")
        with lock:
            progress["n"] += 1
            # 스레드 로그가 섞이므로 완료 라인만 lock 으로 묶어 깔끔히 출력
            print(f"  ✔ [{progress['n']}/{len(tasks)}] {dev} {u} → {info['result']}")
        return info

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(_run, t) for t in tasks]
            for fut in as_completed(futures):
                try:
                    info = fut.result()
                except Exception as e:
                    # capture_page 안에서 다 잡히지만, 예기치 못한 경우까지 행으로 남긴다
                    print(f"  ❌ 태스크 에러: {e}")
                    rows.append({"url": "", "device": "", "sitecode": "", "result": "task_error",
                                 "final_url": "", "http_status": "", "title": "",
                                 "detail": f"{type(e).__name__}: {e}"[:200], "elapsed": 0.0})
                    continue
                rows.append(info)
                results.setdefault(info["url"], {})[info["device"]] = info["result"]
    finally:
        # 재사용하던 Chrome 을 모두 닫는다 (중단·예외로 빠져나가도 좀비가 안 남게)
        quit_all_drivers()

    # 입력 순서대로 skip / error 집계 (PC·MO 중 하나라도 해당되면 1번만 기록)
    skipped_urls = []     # 리다이렉트로 skip된 URL
    error_page_urls = []  # 에러 페이지로 skip된 URL
    unknown_page_urls = []  # unknown(soft-404, og:url 없음) 으로 skip된 URL
    login_page_urls = []  # 로그인/인증 화면으로 skip된 URL
    for u in urls:
        vals = tuple(results.get(u, {}).values())
        if "redirected" in vals:
            skipped_urls.append(u)
        elif "login_page" in vals:
            login_page_urls.append(u)
        elif "error_page" in vals:
            error_page_urls.append(u)
        elif "unknown_page" in vals:
            unknown_page_urls.append(u)

    ts = datetime.now().strftime("%m%d_%H%M")

    # ── (url, device) 단위 상세 결과 CSV ──────────────────────
    # txt 3종은 URL 단위라 "PC 는 정상인데 MO 만 리다이렉트" 같은 경우를 구분 못 하고,
    # error/timeout 은 아예 어느 txt 에도 안 남아 재실행 대상 파악이 불가능했다.
    csv_path = f"{OUTPUT_DIR}/result_{ts}.csv"
    _cols = ["url", "device", "sitecode", "result", "final_url", "http_status", "title", "detail", "elapsed"]
    _order = {u: i for i, u in enumerate(urls)}
    rows.sort(key=lambda r: (_order.get(r.get("url", ""), 10**9), r.get("device", "")))
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as cf:
        w = csv.DictWriter(cf, fieldnames=_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    _cnt = Counter(r.get("result", "") for r in rows)
    print(f"📄 결과 CSV {len(rows)}행 → {csv_path}")
    print("   " + " / ".join(f"{k}:{v}" for k, v in sorted(_cnt.items())))

    # ── skip된 URL을 txt 파일로 저장 ──────────────────────────
    if skipped_urls:
        skip_path = f"{OUTPUT_DIR}/skipped_redirect_{ts}.txt"
        with open(skip_path, "w", encoding="utf-8") as f:
            f.write("\n".join(skipped_urls) + "\n")
        print(f"⏭️  리다이렉트 skip {len(skipped_urls)}개 → {skip_path}")

    # ── 에러 페이지 URL을 txt 파일로 저장 ─────────────────────
    if error_page_urls:
        err_path = f"{OUTPUT_DIR}/skipped_error_page_{ts}.txt"
        with open(err_path, "w", encoding="utf-8") as f:
            f.write("\n".join(error_page_urls) + "\n")
        print(f"⛔ 에러 페이지 skip {len(error_page_urls)}개 → {err_path}")

    # ── 로그인/인증 화면 URL을 txt 파일로 저장 ────────────────
    if login_page_urls:
        login_path = f"{OUTPUT_DIR}/skipped_login_page_{ts}.txt"
        with open(login_path, "w", encoding="utf-8") as f:
            f.write("\n".join(login_page_urls) + "\n")
        print(f"🔒 로그인 화면 skip {len(login_page_urls)}개 → {login_path}")

    # ── unknown(soft-404) 페이지 URL을 txt 파일로 저장 ────────
    if unknown_page_urls:
        unk_path = f"{OUTPUT_DIR}/skipped_unknown_page_{ts}.txt"
        with open(unk_path, "w", encoding="utf-8") as f:
            f.write("\n".join(unknown_page_urls) + "\n")
        print(f"⛔ unknown 페이지 skip {len(unknown_page_urls)}개 → {unk_path}")

    print("✨ 모든 캡처 완료!")


if __name__ == "__main__":
    capture_urls(URLS)
