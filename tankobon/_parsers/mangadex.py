# coding: utf8

import json
import re
from urllib.parse import urlparse

from tankobon import manga

BASE_URL = "mangadex.org"
API_URL = f"https://{BASE_URL}/api/v2"
RE_ID = re.compile(r"^/title/(\d+)/(\w+)/?(.*)$")


def _parse_id(url: str) -> str:
    return RE_ID.findall(urlparse(url).path)[0][0]


class Parser(manga.Parser):

    domain = BASE_URL

    def __init__(self, *args, **kwargs):

        data = kwargs.get("data") or args[0]
        data["url"] = f"{API_URL}/manga/{_parse_id(data['url'])}"

        super().__init__(*args, **kwargs)

        self.api_data = json.loads(self.soup.text)["data"]

    def chapters(self):

        with self.session.get(f"{self.data['url']}/chapters") as response:
            api_chapters = [
                c
                for c in response.json()["data"]["chapters"]
                if c["language"] == "gb"  # FIXME: multi-language support
            ]
            api_chapters.reverse()

        previous_volume = "0"
        for chapter in api_chapters:
            volume = chapter["volume"]
            if not volume:
                volume = previous_volume
            else:
                previous_volume = volume

            if not chapter["chapter"]:
                # oneshot??
                chapter["chapter"] = "0"

            yield {
                "id": chapter["chapter"],
                "title": chapter["title"],
                # NOTE: data_saver is set to true for now (higher-quality image download keeps getting dropped)
                "url": f"{API_URL}/chapter/{chapter['id']}?saver=true",
                "volume": volume,
            }

    def pages(self, soup):
        chapter_data = json.loads(soup.text)["data"]

        chapter_hash = chapter_data["hash"]
        pages = chapter_data["pages"]
        base_url = chapter_data["server"]

        return [f"{base_url}{chapter_hash}/{page}" for page in pages]

    def title(self):
        return self.api_data["title"]

    def description(self):
        return self.api_data["description"]
