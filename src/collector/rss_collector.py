#!/usr/bin/env python3
"""
뉴스 수집 → 로컬 JSON 저장 + 선택적으로 GitHub(main 브랜치) 커밋
ENV                                   설명
───                                   ──────────────────────────
TARGET            mk_economy|hk_it    어떤 피드?
GITHUB_REPO       user/repo           (옵션) 결과를 push 할 레포
GITHUB_TOKEN      <PAT>               위 레포 push 권한 토큰
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import os, json, datetime as dt, argparse
from utils.rss import fetch_rss, RSSFetchError
# PyGithub
from github import Github

import requests

# RSS Feed 목록 정의
FEEDS = {
    # 매일경제 이코노미 RSS 주소
    "mk_economy": "https://www.mk.co.kr/rss/50000001/",

    # 한국경제 IT RSS 주소
    "hk_it":      "https://www.hankyung.com/feed/it",
}

# GitHub에 JSON 파일 업로드
# 정의: PyGithub를 통해 대상 리포지토리에 RSS 데이터를 커밋
# 이유: 수집된 데이터를 버전 관리 및 외부 공유 가능하게 하기 위함
# 확장성: branch, PR 생성 등 GitHub 연동 다양화 가능
# 대체제: git CLI, GitLab API 등
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

# 기사 수 계산이 끝난 후, exporter로 전송
# 정의: 수집된 기사 수를 Prometheus Exporter로 전송 (POST)
# 이유: Exporter가 메모리 기반 메트릭을 제공하고, Prometheus가 이를 스크랩하기 위함
# 확장성: 성공/실패 로그 수집, 실패 시 재시도 등 로직 강화 기능
# 대체제: Pushgateway 사용도 가능하지만, 이 방식이 더 실무와 적합
def push_rss_exporter(target, count):
	try:
		response = requests.post(
			"http://scrap.rss.feed:8000/report",
			json={"target": target, "count": count},
			timeout=5
		)

		print(f"[Exporter] Response: { response.status_code } - { response.text }")

	except Exception as e:
		print(f"[Exporter] Failed to push: {e}")

# 메인 실행 로직
# 정의: parameter로 수집 대상을 받아서 RSS를 수집, 파일 저장, GitHub 업로드, Exporter 전송까지 실행
# 이유: 수동 실행 또는 GitHub Actions, CronJob 등에서 호출되도록 하기 위함
# 확장성: 환경변수 기반 설정, 로그 기록, 기타 알림 기능 추가 가능
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
