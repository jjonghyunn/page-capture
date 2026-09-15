# make_release_notes.py
# 2026-09-15  Jonghyun Park w/ Claude
#
# 태그 이름(vX.Y)을 받아 메인 스크립트 상단 헤더의 그 버전 changelog 를 뽑아
# 릴리스 노트 마크다운으로 출력한다.
#
# 노트 원천을 **헤더 changelog** 로 고정한 이유:
#   커밋 메시지 기반(gh release create --generate-notes 포함)으로 만들면
#   커밋 제목이 그대로 공개 릴리스 노트로 재발행된다. 헤더는 이미 버전별로
#   정리돼 있고 저장소에 올라간 상태 = 검토를 거친 텍스트다.
#
# 사용:
#   python .github/make_release_notes.py v3.9              # 노트를 stdout 으로
#   python .github/make_release_notes.py v3.9 --title      # 릴리스 제목만 stdout 으로

import glob
import os
import re
import sys

# ════════════ 사용자가 바꿔야 하는 부분 ════════════
SCRIPT_GLOB = 'page_capture_*_v*.py'   # 헤더 changelog 를 가진 메인 스크립트
PROJECT_NAME = 'page_capture'
# ════════════ 내부 사용 ════════════
HEADER_LINE = re.compile(r'^#\s*(\d{4}-\d{2}-\d{2})\s+.*?—\s*v(\d+\.\d+)\s+(.*)$')
VER_IN_NAME = re.compile(r'_v(\d+\.\d+)\.py$')


def newest_script():
    """버전 접미사가 가장 높은 메인 스크립트 경로"""
    cands = glob.glob(SCRIPT_GLOB)
    if not cands:
        sys.exit('ERROR: {} 에 맞는 스크립트가 없습니다'.format(SCRIPT_GLOB))

    def key(p):
        m = VER_IN_NAME.search(os.path.basename(p))
        return [int(x) for x in m.group(1).split('.')] if m else [0, 0]

    return max(cands, key=key)


def parse_header(path):
    """{version: {'date': 최초일자, 'entries': [텍스트, ...]}}"""
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('#'):
                break
            m = HEADER_LINE.match(line.rstrip('\n'))
            if not m:
                continue
            date, ver, text = m.group(1), m.group(2), m.group(3).strip()
            e = out.setdefault(ver, {'date': date, 'entries': []})
            e['entries'].append(text)
            e['date'] = min(e['date'], date)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit('사용: make_release_notes.py <tag> [--title]')
    tag = sys.argv[1]
    want_title = '--title' in sys.argv[2:]

    ver = tag[1:] if tag.startswith('v') else tag
    path = newest_script()
    entries = parse_header(path)

    if ver not in entries:
        sys.exit('ERROR: 헤더에 v{} 항목이 없습니다 ({}). '
                 '버전업 시 헤더 changelog 를 먼저 추가하세요.'.format(ver, os.path.basename(path)))

    # 제목 요약 — 헤더 항목의 [라벨] 을 우선 사용 (없으면 첫 항목 앞부분)
    labels = []
    for e in entries[ver]['entries']:
        m = re.match(r'^\[([^\]]+)\]', e)
        if m and m.group(1) not in labels:
            labels.append(m.group(1))
    if labels:
        summary = ' + '.join(labels[:3]) + (' 외' if len(labels) > 3 else '')
    else:
        summary = entries[ver]['entries'][0].split('—')[0].split('(')[0].strip()
        if len(summary) > 60:
            summary = summary[:57].rstrip() + '...'

    if want_title:
        print('{} v{} — {}'.format(PROJECT_NAME, ver, summary))
        return

    body = '\n'.join('- ' + e for e in entries[ver]['entries'])
    print('## {} v{}\n'.format(PROJECT_NAME, ver))
    print('릴리스 시점 파일: `{}`\n'.format(os.path.basename(path)))
    print('### 변경 내역\n')
    print(body)
    print('\n---')
    print('<sub>노트 원천: 스크립트 상단 헤더 changelog</sub>')


if __name__ == '__main__':
    main()
