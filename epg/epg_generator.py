from lxml import etree
import requests

EPG_SOURCES = [
    "https://www.open-epg.com/files/indonesia2.xml.gz",
    "https://raw.githubusercontent.com/dbghelp/StarHub-TV-EPG/refs/heads/main/starhub.xml"
]

OUTPUT = "../epg.xml"

def main():
    root = etree.Element("tv")

    for url in EPG_SOURCES:
        try:
            data = requests.get(url, timeout=30).content
            if url.endswith(".gz"):
                import gzip
                data = gzip.decompress(data)

            tree = etree.fromstring(data)
            for elem in tree:
                root.append(elem)
        except Exception as e:
            print("EPG source error:", url, e)

    etree.ElementTree(root).write(
        OUTPUT,
        encoding="utf-8",
        xml_declaration=True
    )

    print("[EPG] epg.xml updated")

if __name__ == "__main__":
    main()
