# Agent Instructions

## Project overview

This is a static website for pglayers (https://pglayers.github.io).
It is hosted on GitHub Pages as a plain static site -- no build step,
no static site generator, no external packages.

## Rules

- **No external packages or static generators.** No npm, no Hugo, no
  Jekyll, no Eleventy. Everything is plain HTML, CSS, and optionally
  vanilla JavaScript.
- **No build step.** Files are served as-is by GitHub Pages.
- **Blog posts are hand-written HTML files** in the `blog/` directory.
- **RSS feed** (`feed.xml`) is maintained manually alongside blog posts.
  When adding a new post, always update `feed.xml` with the new entry.
- **Consistent styling.** Blog pages reuse the same design language as
  `index.html` (dark theme, Inter + JetBrains Mono fonts, CSS variables
  defined in `:root`).
- **Navigation bar must stay in sync across all pages.** The top nav is
  duplicated in `index.html`, `blog/index.html`, and every blog post.
  When changing nav links (adding, removing, or reordering), update all
  pages together.
- **Audience.** Technical but beginner-friendly. Assume readers know
  Docker and PostgreSQL basics but explain pglayers-specific concepts.

## Blog conventions

- Blog index page: `blog/index.html`
- Individual posts: `blog/YYYY-MM-DD-slug.html`
- RSS feed: `feed.xml` (Atom or RSS 2.0, kept at repo root)
- Each post must include: title, date, author, and content.
- **Author is always Ismaël Mejía (@iemejia).** Planet PostgreSQL
  requires individual authorship -- never use a team or project name.
  The author must appear in:
  - The blog post HTML (`.article-meta .author` element)
  - The blog index listing (`blog/index.html`)
  - The RSS feed channel (`<managingEditor>` and `<description>`)
  - Each RSS feed item (`<dc:creator>`)
- **Dates must be 2026-07 or later** and should correspond to the
  current date at time of writing. The feed is syndicated to
  Planet PostgreSQL, which ignores posts with dates in the past.
  Never use placeholder or outdated years in `<pubDate>`,
  `<lastBuildDate>`, filenames, or `<time>` elements.
- **Every post in `feed.xml` must include these three `<category>` elements:**
  `PostgreSQL`, `Docker`, `Containers`. Planet PostgreSQL filters by
  category tags; omitting them may prevent syndication.
- When adding a new blog post:
  1. Create the post HTML file in `blog/`
  2. Add an entry to `blog/index.html`
  3. Add an item to `feed.xml`
- When modifying an existing blog post, always update the corresponding
  `<content:encoded>` in `feed.xml` to match. The HTML post and the RSS
  entry must stay in sync.
- The `<content:encoded>` in `feed.xml` must always contain the **full
  post content as HTML** (not a summary or plain text) so it renders
  correctly in RSS news readers.

## File structure

```
pglayers.github.io/
├── index.html          Landing page
├── feed.xml            RSS feed
├── blog/
│   ├── index.html      Blog listing page
│   └── YYYY-MM-DD-slug.html  Individual posts
└── AGENTS.md           This file
```
