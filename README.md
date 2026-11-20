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

Run the static checks with Python's standard library (no install needed):

```sh
python3 -m unittest discover -s tests -v
```

## Updating extension counts and PostgreSQL support

The homepage distinguishes the total extension catalog, layers available for
each PostgreSQL major, and extensions actually included in a profile image.
Check `extensions/`, `profiles/`, and the APT-version record in the pglayers
repository, then verify the published image labels
(`org.pglayers.extensions.count`, `.included`, and `.missing`) for **both**
amd64 and arm64. A profile can exclude a runtime-conflicting extension even
when its individual layer exists.

Update the hero, stats, support table and verification date, profile badges,
and the count snapshot in `tests/test_site.py` together. Keep each example's
PostgreSQL major consistent with its layer tags and filesystem layout.
Historical posts retain their original release context; if editing a post,
also synchronize its full HTML in `feed.xml`.

## Adding a blog post

1. Create `blog/YYYY-MM-DD-slug.html`
2. Add an entry to `blog/index.html`
3. Add an item to `feed.xml` (include full HTML content in
   `<content:encoded>` and the required category tags)

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md)
for details.
