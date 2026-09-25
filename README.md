# SXF / AI

A zero-cost static AI news radar for **sxf.si**.

- Static HTML/CSS/JS.
- GitHub Actions refreshes `data/news.json` every 3 hours.
- Uses free public RSS/Atom feeds from primary sources.
- No database, paid API, or AI model required.

## Free deployment
Connect this repository to Cloudflare Pages, leave the build command blank, deploy the repository root, then attach `sxf.si`.
