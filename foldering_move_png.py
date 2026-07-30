# foldering_move_png.py
# 2026-05-27  Jonghyun Park w/ Claude
# 2026-07-30  Jonghyun Park w/ Claude  — .png 만 옮기던 것을 .mhtml 도 함께 옮기도록 수정.
#   메인 스크립트의 이어하기(already_captured)는 sitecode 하위폴더에 PNG 와 MHTML 이 **둘 다**
#   있어야 skip 하므로, PNG 만 옮기면 MHTML 이 루트에 남아 판정이 항상 False → 재실행이 전량
#   재캡처가 된다(v3.4 이어하기가 무력화됨). 두 확장자를 같이 옮겨 그 전제를 지킨다.
# ★★★ MO 파일 먼저 옮기고 실행하기!! ★★★

import os
import shutil
import re

# ════ 사용자가 바꿔야 하는 부분 ════
# 캡처 PNG / MHTML 이 들어있는 폴더 경로
FOLDER_PATH = r"C:\Users\user_name\Downloads\captures"

# ════ 내부 사용 ════
# 정리 대상 확장자 — 메인 스크립트가 (url, device) 당 PNG + MHTML 을 한 쌍으로 저장한다.
TARGET_EXTS = (".png", ".mhtml")

# 파일 리스트 가져오기
file_list = [f for f in os.listdir(FOLDER_PATH) if f.endswith(TARGET_EXTS)]

# 정리 시작
for file_name in file_list:
    # PC 또는 MO 앞까지 추출 (공백이나 언더바 포함)
    match = re.match(r"(.+?)[ _](PC|MO)", file_name)
    if match:
        folder_name = match.group(1).replace(" ", "_")  # 공백 → 언더바 처리
        dest_folder = os.path.join(FOLDER_PATH, folder_name)

        # 폴더 없으면 생성
        os.makedirs(dest_folder, exist_ok=True)

        # 파일 이동
        src_path = os.path.join(FOLDER_PATH, file_name)
        dest_path = os.path.join(dest_folder, file_name)
        shutil.move(src_path, dest_path)
        print(f"Moved: {file_name} -> {folder_name}/")
    else:
        print(f"Skipped: {file_name}")
