import requests, xml.etree.ElementTree as ET, datetime as dt

TARGET_COUNT = 3

def fetch_rss(url: str) -> list[dict]:
    """RSS → [{title, link, pub_date}] 최신 TARGET_COUNT개 반환"""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = root.findall("./channel/item")[:TARGET_COUNT]
    out = []
    for it in items:
        out.append({
            "title": it.findtext("title"),
            "link":  it.findtext("link"),
            "pub_date": it.findtext("pubDate"),
            "fetched_at": dt.datetime.utcnow().isoformat()
        })
    return out

