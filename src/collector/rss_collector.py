#!/usr/bin/env python3
"""
뉴스 수집 → 로컬 JSON 저장 + 선택적으로 GitHub(main 브랜치) 커밋
ENV                                   설명
───                                   ──────────────────────────
TARGET            mk_economy|hk_it    어떤 피드?
GITHUB_REPO       user/repo           (옵션) 결과를 push 할 레포
GITHUB_TOKEN      <PAT>               위 레포 push 권한 토큰
"""

import os, json, pathlib, datetime as dt, argparse, sys
from utils.rss import fetch_rss, RSSFetchError
# PyGithub
from github import Github

FEEDS = {
    # 매일경제 경제 RSS 주소
    "mk_economy": "https://www.mk.co.kr/rss/30100041/",

    # 한국경제 IT RSS 주소
    "hk_it":      "https://www.hankyung.com/feed/it",
}

def push_to_github(repo_full: str, dst_path: str, data: list[dict]):
    gh = Github(os.environ["GITHUB_TOKEN"])
    repo = gh.get_repo(repo_full)

    body = json.dumps(data, ensure_ascii=False, indent=2)
    msg  = f"chore(rss): update {dst_path}"
    try:
        contents = repo.get_contents(dst_path)
        repo.update_file(contents.path, msg, body, contents.sha, branch="main")
    # 파일이 없으면 새로 만듦
    except Exception:
        repo.create_file(dst_path, msg, body, branch="main")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=os.getenv("TARGET"))
    parser.add_argument("--limit",  type=int, default=3)
    args = parser.parse_args()
    if not args.target or args.target not in FEEDS:
        sys.exit("TARGET 파라미터(mk_economy|hk_it)가 필요함")

    try:
        items = fetch_rss(FEEDS[args.target], args.limit)
    except RSSFetchError as e:
        sys.exit(str(e))

    today = dt.date.today().isoformat()
    out_dir  = pathlib.Path("data", today)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.target}.json"
    out_file.write_text(json.dumps(items, ensure_ascii=False, indent=2))

    # GitHub 업로드(옵션)
    if os.getenv("GITHUB_REPO") and os.getenv("GITHUB_TOKEN"):
        push_to_github(os.environ["GITHUB_REPO"], str(out_file), items)

if __name__ == "__main__":
    main()
