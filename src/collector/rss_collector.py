import os, json, pathlib, datetime as dt
from utils.rss import fetch_rss
from github import Github            # PyGithub
import requests

FEEDS = {
    "mk_economy": "https://www.mk.co.kr/rss/30100041/",
    "hankyung_it": "https://www.hankyung.com/feed/it"
}

def push_to_github(repo_full, path, data):
    gh = Github(os.environ["GITHUB_TOKEN"])
    repo = gh.get_repo(repo_full)
    try:
        contents = repo.get_contents(path)
        sha = contents.sha
    except:
        sha = None
    repo.create_file(
        path, f"data: {path}", json.dumps(data, ensure_ascii=False, indent=2),
        sha=sha, branch="main"
    )

def main():
    target = os.environ.get("TARGET") or os.sys.argv[1]
    feed_url = FEEDS[target]
    today = dt.date.today().isoformat()
    out_path = f"data/{today}/{target}.json"

    items = fetch_rss(feed_url)
    pathlib.Path(f"data/{today}").mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(items, fp, ensure_ascii=False, indent=2)

    push_to_github(os.environ["GITHUB_REPO"], out_path, items)

if __name__ == "__main__":
    main()
