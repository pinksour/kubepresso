"""RSS pharsing util - 예외처리 포함"""
import requests, feedparser, datetime as dt

MAX_ITEMS = 5
TIMEOUT = 10	# seconds

class RSSFetchError(RuntimeError):
	...

RSS_HEADERS = {
	"User-Agent": (
		"kubepresso-rss/1.0"
		"(+https://github.com/pinksour/kubepresso)"
	)
}

def fetch_rss(url: str, limit: int = MAX_ITEMS) -> list[dict]:
	try:
		resp = requests.get(
			url,
			headers=RSS_HEADERS,
			timeout=TIMEOUT,
		)

		if resp.headers.get("cf-mitigated") == "challenge":
			ray = resp.headers.get("cf-ray", "unknown")
			raise RSSFetchError(
				f"Cloudflare challenge 발생: status={resp.status_code}, cf-ray={ray}"
			)
			
		resp.raise_for_status()
		
	except requests.RequestException as e:
		raise RSSFetchError(f"HTTP failed: {e}") from e

	feed = feedparser.parse(resp.content)
	if feed.bozo:
		raise RSSFetchError(f"RSS Pharsing Error: {feed.bozo_exception}")

	items = []
	for entry in feed.entries[:limit]:
		items.append(
			{
				"title":      getattr(entry, "title", "").strip(),
				"link":       getattr(entry, "link", ""),
				"pub_date":   getattr(entry, "published", ""),
				"fetched_at": dt.datetime.utcnow().isoformat() + "Z",
			}
		)
	if not items:
		raise RSSFetchError("항목 0개 반환 – 피드 URL 확인 필요")
	return items
