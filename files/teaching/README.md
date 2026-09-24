# Course materials

One folder per course (the folder name is the course `slug` in `content/teaching.toml`).

To publish a document:

1. Copy the file here, e.g. `files/teaching/statistics/td1.pdf`
2. Add an entry under the course in `content/teaching.toml`:

   ```toml
   [[courses.materials]]
   title = { en = "Tutorial 1 — Descriptive statistics", fr = "TD 1 — Statistique descriptive" }
   file = "files/teaching/statistics/td1.pdf"
   kind = "exercises"   # slides | exercises | solutions | exam | reading | other
   date = "2026-09"
   ```
3. Run `python src/build.py`, then commit and push.
