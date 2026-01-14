import requests, gzip
from lxml import etree

EPG_OUTPUT = "epg.xml"

EPG_SOURCES = [
    "https://www.open-epg.com/files/indonesia2.xml.gz",
    "https://raw.githubusercontent.com/dbghelp/StarHub-TV-EPG/refs/heads/main/starhub.xml",
    "https://epg.pw/xmltv/epg_ID.xml",
    "http://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
]

# kata kunci sepakbola
KEYWORDS = [
    " vs ", " v ",
    "liga", "league",
    "premier",
    "champions", "ucl", "uefa",
    "world cup", "copa",
    "afc", "fifa"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def is_soccer(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in KEYWORDS)

def load_xml(url):
    r = requests.get(url, headers=HEADERS, timeout=40)
    r.raise_for_status()
    data = r.content
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return etree.fromstring(data)

def main():
    tv = etree.Element("tv", generator_info_name="Soccer Only EPG")
    channel_ids = set()

    for url in EPG_SOURCES:
        try:
            root = load_xml(url)

            for pr in root.findall("programme"):
                title_el = pr.find("title")
                if title_el is None or not title_el.text:
                    continue

                if not is_soccer(title_el.text):
                    continue

                ch_id = pr.get("channel")
                if ch_id and ch_id not in channel_ids:
                    channel_ids.add(ch_id)
                    ch = etree.SubElement(tv, "channel", id=ch_id)
                    etree.SubElement(ch, "display-name").text = ch_id

                tv.append(pr)

            print(f"[OK] Soccer filtered from {url}")
        except Exception as e:
            print(f"[SKIP] {url} -> {e}")

    with open(EPG_OUTPUT, "wb") as f:
        f.write(etree.tostring(
            tv,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        ))

    print("[DONE] epg.xml (soccer only)")

if __name__ == "__main__":
    main()
