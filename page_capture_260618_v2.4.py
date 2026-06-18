# page_capture_260618_v2.4.py
# 2026-04-17  user_id w/ Claude  — v2.0 초기 버전
# 2026-04-20  user_id w/ Claude  — v2.1 is_error_page 다국어 에러 감지 강화 + /common/404/ + Chrome ERR 감지
# 2026-04-29  user_id w/ Claude  — v2.2 filename에 OUTPUT_DIR 변수 사용 + raw string 적용 + 파일명 정리(두 번째 날짜=캠페인 날짜 제거)
# 2026-05-22  user_id w/ Claude  — v2.3 주석/예시 URL sanitize + 도메인 매칭 로직 상수화 (TARGET_DOMAIN / TARGET_DOMAIN_CN / TARGET_BRAND_KEYWORD) + 설정 상수 파일 상단으로 이동
# 2026-06-18  user_id w/ Claude  — v2.4 캡처를 ThreadPoolExecutor 로 병렬화 (MAX_WORKERS) + URL 목록 상단 상수(URLS)로 이동
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from urllib.parse import urlparse
import time
from PIL import Image
import io
import re
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# ════════════════════════════════════════
# 사용자가 바꿔야 하는 부분
# ════════════════════════════════════════
# 캡처 출력 경로
OUTPUT_DIR = r"C:\Users\user_name\Downloads\test_png_260417"

# 동시에 띄울 헤드리스 Chrome 개수. 브라우저 1개당 ~300-500MB RAM.
# RAM·CPU 여유에 맞춰 조정 (보통 4~8, 16GB RAM 이면 4~6 권장)
MAX_WORKERS = 4

# 캡처 대상 도메인 — 본인 환경의 브랜드/기업 도메인으로 변경
TARGET_DOMAIN = "example.com"                        # 메인 글로벌 도메인 (host.endswith 매칭)
TARGET_DOMAIN_CN = ("example.com.cn", "example.cn")  # 중국 사이트 — 별도 사이트코드 'CN' 부여
TARGET_BRAND_KEYWORD = "example"                     # host 안에 이 키워드 들어가면 같은 브랜드로 인식

# 캡처할 URL 목록 (한 줄에 하나, # 로 시작하면 주석 처리)
URLS = """
https://www.example.com/nz/offer/campaign-name-gift-ideas
https://www.example.com/vn/offer/campaign-name
"""

# ════════════════════════════════════════
# 내부 사용
# ════════════════════════════════════════

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
            except:
                continue
    except:
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
            except:
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
            except:
                continue
        print("  ⚠️ 쿠키 버튼 없음")
        return False
    except Exception as e:
        print(f"  ⚠️ 쿠키 처리 에러: {e}")
        return False

def is_sec_path(url: str) -> bool:
    p = urlparse(url)
    host = p.netloc.lower().replace('www.', '')
    parts = [x for x in p.path.split('/') if x]
    return host.endswith(TARGET_DOMAIN) and len(parts) >= 1 and parts[0] == 'sec'

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
    except:
        pass

# =========================
# 에러 페이지 감지
# =========================
# company_name 에러 페이지: <title>error | company_name Gulf</title> 등
# HTTP 에러: <title>502 Bad Gateway</title> 등
_ERROR_TITLE_KEYWORDS = ['error', '404', '502', '503', 'bad gateway', 'page not found', 'not available']

def is_error_page(driver) -> bool:
    """에러/없는 페이지 여부 판단 (title + canonical URL + SEC 전용 요소)"""
    # 1. 영어 title 키워드 (기존)
    try:
        title = driver.title.lower().strip()
        if any(kw in title for kw in _ERROR_TITLE_KEYWORDS):
            return True
    except:
        pass

    # 2. company_name 공통 에러 페이지: canonical URL에 /common/error/ 또는 /common/404/ 포함
    try:
        canonical = driver.execute_script(
            "var el=document.querySelector('link[rel=\"canonical\"]'); return el?el.href:'';"
        )
        if canonical and any(p in canonical for p in ('/common/error/', '/common/404/')):
            return True
    except:
        pass

    # 3. SEC(한국) 전용 에러 구조: aiscPrivateError 요소 존재
    try:
        if driver.find_elements(By.ID, 'aiscPrivateError'):
            return True
    except:
        pass

    # 4. Chrome 브라우저 에러 페이지 (ERR_TOO_MANY_REDIRECTS 등 네트워크 에러)
    try:
        src = driver.page_source
        if src and any(e in src for e in ('ERR_TOO_MANY_REDIRECTS', 'ERR_CONNECTION', 'ERR_NAME_NOT_RESOLVED', 'ERR_TIMED_OUT')):
            return True
    except:
        pass

    return False

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
# 메인 캡처 함수
# =========================
def capture_page(url, device_type):
    sitecode, page_path, sitetype = get_page_info(url)
    page_name = safe_filename(f"{sitecode}_{page_path}")
    timestamp = datetime.now().strftime("%m%d")

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--hide-scrollbars')

    if device_type == "MO":
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        chrome_options.add_argument(f'--user-agent={ua}')
        vw, vh = 390, 844
    else:
        vw, vh = 1920, 1080
    chrome_options.add_argument(f'--window-size={vw},{vh}')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"  📸 {device_type} 버전 캡처 중...")
        if device_type=="MO":
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width':vw,'height':vh,'deviceScaleFactor':3,'mobile':True
            })
        driver.get(url)
        time.sleep(5)

        # ── 리다이렉트 감지 ──────────────────────────────────────
        final_url = driver.current_url
        def _norm(u): return u.rstrip('/')  # 후행 슬래시 무시 비교
        if _norm(final_url) != _norm(url):
            print(f"  ⏭️  리다이렉트 감지 → skip")
            print(f"      원본: {url}")
            print(f"      이동: {final_url}")
            return "redirected"

        # ── 에러 페이지 감지 (404 / 502 / company_name error 등) ─────
        if is_error_page(driver):
            print(f"  ⛔ 에러 페이지 감지 (title: '{driver.title}') → skip")
            return "error_page"

        close_popups(driver)
        accept_cookies(driver)
        time.sleep(2)
        close_popups(driver)

        # 파일명 구성: 쿼리 파라미터 있는 경우 포함 (ex: ES_PC_offer_campaign-name_page_category-tv-audio_1112.png 파라미터 없는건 ES_PC_offer_campaign-name_page_1112.png)
        parsed = urlparse(url)
        query_part = parsed.query.replace('=', '-').replace('&', '_') if parsed.query else ''
        if query_part:
            filename = f"{OUTPUT_DIR}/{safe_filename(f'{sitecode}_{device_type}_{page_path}_page_{query_part}_{timestamp}.png')}"
        else:
            filename = f"{OUTPUT_DIR}/{safe_filename(f'{sitecode}_{device_type}_{page_path}_page_{timestamp}.png')}"

        if device_type=="MO":
            img = capture_full_page_mobile(driver, vw)
            img.save(filename,'PNG',optimize=True,quality=95)
        else:
            if is_sec_path(url):
                time.sleep(5)
                wait_dom_settled(driver)
                wait_key_elements(driver)
            total_h = smooth_scroll_desktop(driver)
            driver.set_window_size(vw,total_h+200)
            time.sleep(2)
            png = screenshot_png(driver)
            retry=2
            while looks_blank(png) and retry>0:
                print("  ⚠️ 화면이 비어 보여 재시도...")
                time.sleep(4)
                wait_dom_settled(driver)
                png = screenshot_png(driver)
                retry-=1
            with open(filename,"wb") as f: f.write(png)
        print(f"  ✅ 저장: {filename}")
        # ── MHTML 저장 ────────────────────────────────────────
        # PNG용으로 전체 높이로 늘린 창을 원래 뷰포트로 복원 (그 상태로 CDP 호출 시 blank 발생)
        if device_type != "MO":
            driver.set_window_size(vw, vh)
        driver.execute_script("window.scrollTo(0,0)")
        time.sleep(2)  # 재렌더링 대기
        mhtml_filename = filename.replace('.png', '.mhtml')
        result = driver.execute_cdp_cmd("Page.captureSnapshot", {"format": "mhtml"})
        mhtml_data = result.get("data", "")
        with open(mhtml_filename, "wb") as mf:  # bytes 쓰기 (텍스트 모드 시 blank 가능)
            mf.write(mhtml_data.encode("utf-8"))
        print(f"  ✅ MHTML 저장: {mhtml_filename}")
        return "ok"

    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback; traceback.print_exc()
        return "error"
    finally:
        driver.quit()

# =========================
# 여러 URL 병렬 캡처
# =========================
def capture_urls(urls, max_workers=MAX_WORKERS):
    if isinstance(urls,str):
        urls=[u.strip() for u in urls.split('\n') if u.strip() and not u.startswith('#')]
    # (url, device) 단위 태스크 — PC/MO 는 서로 독립이라 각각 별도 브라우저로 병렬 처리
    tasks = [(u, dev) for u in urls for dev in ("PC", "MO")]
    print(f"\n🚀 총 {len(urls)}개 페이지 × (PC/MO) = {len(tasks)}개 작업 병렬 캡처 시작 (동시 {max_workers}개)\n")

    results = {}            # url -> {device: result}
    progress = {"n": 0}
    lock = threading.Lock()

    def _run(task):
        u, dev = task
        r = capture_page(u, dev)
        with lock:
            progress["n"] += 1
            # 스레드 로그가 섞이므로 완료 라인만 lock 으로 묶어 깔끔히 출력
            print(f"  ✔ [{progress['n']}/{len(tasks)}] {dev} {u} → {r}")
        return u, dev, r

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_run, t) for t in tasks]
        for fut in as_completed(futures):
            try:
                u, dev, r = fut.result()
            except Exception as e:
                print(f"  ❌ 태스크 에러: {e}")
                continue
            results.setdefault(u, {})[dev] = r

    # 입력 순서대로 skip / error 집계 (PC·MO 중 하나라도 해당되면 1번만 기록)
    skipped_urls = []     # 리다이렉트로 skip된 URL
    error_page_urls = []  # 에러 페이지로 skip된 URL
    for u in urls:
        vals = tuple(results.get(u, {}).values())
        if "redirected" in vals:
            skipped_urls.append(u)
        elif "error_page" in vals:
            error_page_urls.append(u)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%m%d_%H%M")

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

    print("✨ 모든 캡처 완료!")

if __name__ == "__main__":
    capture_urls(URLS)
