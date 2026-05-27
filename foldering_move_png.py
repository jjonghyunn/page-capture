# foldering_move_png.py
# 2026-05-27  Jonghyun Park w/ Claude
# ★★★ MO 파일 먼저 옮기고 실행하기!! ★★★

import os
import shutil
import re

# ════ 사용자가 바꿔야 하는 부분 ════
# 캡처 PNG 가 들어있는 폴더 경로
FOLDER_PATH = r"C:\Users\user_name\Downloads\captures"

# 파일 리스트 가져오기
file_list = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".png")]

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
