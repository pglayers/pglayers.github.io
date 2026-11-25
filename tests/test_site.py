"""Static-site regression checks; Python standard library only."""

from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
import re
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
        dates = [parsedate_to_datetime(i.findtext("pubDate")) for i in feed.findall("./channel/item")]
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertGreaterEqual(parsedate_to_datetime(feed.findtext("./channel/lastBuildDate")), dates[0])
        for item in feed.findall("./channel/item"):
            path = ROOT / urlsplit(item.findtext("link")).path.lstrip("/")
            self.assertIn(path, self.pages)
            content = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
            self.assertTrue(content)
            Page(content)
            self.assertTrue(item.findtext("{http://purl.org/dc/elements/1.1/}creator").startswith("Ismaël Mejía"))
            self.assertTrue({"PostgreSQL", "Docker", "Containers"}.issubset(
                {category.text for category in item.findall("category")}))

    def test_pg19_post_and_feed_have_identical_full_html(self):
        filename = "2026-11-25-postgresql-19-support.html"
        source = (ROOT / "blog" / filename).read_text()
        marker = '<div class="article-body" id="post-content">'
        self.assertIn(marker, source)
        content = source.split(marker, 1)[1].split("\n        </div>\n    </article>", 1)[0].strip()
        feed = ET.parse(ROOT / "feed.xml")
        item = next(i for i in feed.findall("./channel/item")
                    if i.findtext("link").endswith(filename))
        self.assertEqual(item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded").strip(), content)
        self.assertEqual(item.findtext("title"), "PostgreSQL 19 is now supported in pglayers")
        self.assertEqual(parsedate_to_datetime(item.findtext("pubDate")).date().isoformat(), "2026-11-25")
        post = self.pages[ROOT / "blog" / filename].root
        self.assertEqual(next(post.elements("time")).attrs["datetime"], "2026-11-25")

    def test_pg19_post_preserves_approved_draft(self):
        draft_path = ROOT / "drafts" / "2026-11-25-postgresql-19-support.md"
        if not draft_path.exists():
            self.skipTest("The local Markdown draft is not part of the published site")
        draft = draft_path.read_text()
        post = self.pages[ROOT / "blog" / "2026-11-25-postgresql-19-support.html"].root
        headings = re.findall(r"^## (.+)$", draft, re.MULTILINE)
        self.assertEqual([h.text() for h in post.elements("h2")], headings)
        blocks = re.findall(r"^```\w*\n(.*?)\n```", draft, re.MULTILINE | re.DOTALL)
        self.assertEqual([pre.text() for pre in post.elements("pre")], blocks)
        content = next(e for e in post.elements("div") if e.attrs.get("id") == "post-content")

        def plain(text):
            text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
            return " ".join(text.replace("**", "").replace("`", "").split())

        paragraphs = []
        current = []
        in_code = False
        for line in draft.splitlines() + [""]:
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if not line.strip():
                if current:
                    paragraphs.append(plain(" ".join(current)))
                    current = []
            elif not line.startswith(("#", "- ", "|", "*By ")):
                current.append(line)
        self.assertEqual([" ".join(p.text().split()) for p in content.elements("p")], paragraphs)
        self.assertEqual([" ".join(li.text().split()) for li in content.elements("li")],
                         [plain(line[2:]) for line in draft.splitlines() if line.startswith("- ")])


if __name__ == "__main__":
    unittest.main()
