# Guewen Heslan — personal academic website

Static website (plain HTML / CSS / JS, no build step), ready for GitHub Pages.
English by default, French version under `/fr/`.

## Structure

```
index.html, research.html, cv.html, teaching.html   English pages
fr/…                                                French pages (same file names)
404.html                                            Not-found page
assets/css/style.css                                Design tokens, layout, animations
assets/js/main.js                                   Theme toggle, menu, scroll reveal, page transitions
assets/img/favicon.svg
.nojekyll                                           Serve files as-is (no Jekyll processing)
```

When you edit a page, edit its counterpart in the other language too
(`cv.html` ↔ `fr/cv.html`, etc.).

## Deploy on GitHub Pages

1. Create a repository named **`<username>.github.io`** (recommended: the site is then served at the root,
   which the 404 page expects).
2. Push the contents of this folder to the `main` branch:
   ```bash
   git init
   git add .
   git commit -m "Initial website"
   git branch -M main
   git remote add origin https://github.com/<username>/<username>.github.io.git
   git push -u origin main
   ```
3. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → `main` / `(root)`**.

`docs/` (the source PDF CV, which contains a phone number) and `docs_not_in_the_site/` (unsubmitted
working papers) are excluded by `.gitignore` and are never published.

## Preview locally

```bash
python -m http.server 8000
```
then open <http://localhost:8000>.
