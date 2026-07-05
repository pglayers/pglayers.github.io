# pglayers.github.io

Static website for [pglayers](https://pglayers.github.io) -- pre-built
PostgreSQL extensions as stackable Docker layers.

## Structure

```
index.html          Landing page
feed.xml            RSS feed (syndicated to Planet PostgreSQL)
blog/
  index.html        Blog listing
  YYYY-MM-DD-*.html Individual posts
```

## Development

No build step, no static site generator, no external packages. Files are
served as-is by GitHub Pages.

To preview locally, use any static file server:

```sh
python3 -m http.server 8000
```

## Adding a blog post

1. Create `blog/YYYY-MM-DD-slug.html`
2. Add an entry to `blog/index.html`
3. Add an item to `feed.xml` (include full HTML content in
   `<content:encoded>` and the required category tags)

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md)
for details.
