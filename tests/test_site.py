"""Static-site regression checks; Python standard library only."""

from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Element:
    def __init__(self, tag, attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    def elements(self, tag=None):
        for child in self.children:
            if isinstance(child, Element):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.elements(tag)

    def text(self):
        return "".join(c.text() if isinstance(c, Element) else c for c in self.children)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            raise ValueError(f"Unclosed element: {self.stack[-1].tag}")

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.stack[-1].tag != tag:
            raise ValueError(f"Mismatched closing tag: {tag}, expected {self.stack[-1].tag}")
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {p: Page(p.read_text()) for p in ROOT.rglob("*.html")}
        cls.home = cls.pages[ROOT / "index.html"].root

    def test_internal_links_and_unique_ids(self):
        for path, page in self.pages.items():
            elements = list(page.root.elements())
            ids = [e.attrs["id"] for e in elements if "id" in e.attrs]
            with self.subTest(page=path.name):
                self.assertEqual(len(ids), len(set(ids)), "Duplicate HTML IDs")
            for element in elements:
                href = element.attrs.get("href")
                if not href:
                    continue
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    continue
                target = (ROOT / url.path.lstrip("/") if url.path.startswith("/")
                          else path.parent / url.path) if url.path else path
                if target.is_dir():
                    target /= "index.html"
                with self.subTest(page=path.name, href=href):
                    self.assertTrue(target.is_file(), f"Missing local target: {target}")
                    if url.fragment:
                        target_ids = {e.attrs.get("id") for e in self.pages[target].root.elements()}
                        self.assertIn(unquote(url.fragment), target_ids)

    def test_navigation_stays_in_sync(self):
        expected = None
        for path, page in self.pages.items():
            nav = next(page.root.elements("nav"))
            base = "https://pglayers.github.io/" + str(path.relative_to(ROOT)).removesuffix("index.html")
            links = [(urljoin(base, a.attrs["href"]), " ".join(a.text().split()))
                     for a in nav.elements("a")]
            if expected is None:
                expected = links
            with self.subTest(page=path.name):
                self.assertEqual(links, expected)

    def test_verified_support_counts(self):
        # Snapshot checked against the catalog and both published architectures
        # on 2026-11-20. Update deliberately when refreshing the homepage counts.
        rows = {r.attrs["data-pg"]: [c.text().strip() for c in r.elements("td")]
                for r in self.home.elements("tr") if "data-pg" in r.attrs}
        self.assertEqual(rows, {"17": ["84", "83", "31"],
                                "18": ["84", "83", "31"],
                                "19": ["62", "62", "24"]})
        text = self.home.text()
        self.assertIn("84 extensions in the catalog", text)
        self.assertIn("PostgreSQL 19 GA supported", text)
        self.assertIn("31 on PG17/18 · 24 on PG19", text)
        self.assertIn("83 on PG17/18 · 62 on PG19", text)
        self.assertIn("PG17/18 only, not PG19", text)
        self.assertNotIn("all 80+", text)

    def test_pg19_examples_keep_isolated_paths_and_literal_gucs(self):
        examples = [pre.text() for pre in self.home.elements("pre")]
        self.assertEqual(len(examples), 2)
        dockerfile, pod = examples
        self.assertIn("FROM postgres:19", dockerfile)
        self.assertIn("pgx-pgvector:19 / /extensions/pgvector/", dockerfile)
        self.assertIn(r"/extensions/pgvector/share:\$system", dockerfile)
        self.assertIn(r"/extensions/pgvector/lib:\$libdir", dockerfile)
        self.assertIn("image: postgres:19", pod)
        self.assertIn("pgx-pgvector:19-0.8.7", pod)
        self.assertIn("pgx-postgis:19-3.7.0", pod)
        self.assertIn("/extensions/postgis/share:$system", pod)
        self.assertIn("/extensions/postgis/lib:$libdir", pod)
        self.assertNotIn("$$system", pod)
        self.assertNotIn("...", pod)

    def test_feed_and_historical_post_targets(self):
        feed = ET.parse(ROOT / "feed.xml")
        for item in feed.findall("./channel/item"):
            path = ROOT / urlsplit(item.findtext("link")).path.lstrip("/")
            self.assertIn(path, self.pages)
            self.assertTrue(item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded"))


if __name__ == "__main__":
    unittest.main()
