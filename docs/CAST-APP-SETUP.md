# Sharing the mixer with the cast — one-time setup

`docs/index.html` is a plain static page: no Claude account needed to use it.
It reads the song data and audio straight from your own Google Drive folder
(`Guys and Dolls/lbal`) at runtime, using Google's public Drive API. Three
one-time steps, all in your own accounts, get it live.

## 1. Share the Drive folder

Open the `lbal` folder in Drive → **Share** → **General access** → change
"Restricted" to **"Anyone with the link"**, role **Viewer**. This is what
makes the folder loadable by a page with no sign-in — anyone who has the
folder's contents (config + real audio rendered from your show's own vocal
book and piano score, both derived from copyrighted material) reachable if
they get the link, not just people you've personally added, so treat the
folder link the same way you'd treat a rehearsal recording link: fine to
hand to the cast, not something to post publicly.

## 2. Create a Google Drive API key

The page calls Drive's REST API directly from the browser, which needs an
API key (not sign-in — that's what lets it work with no per-viewer login).

1. Go to [Google Cloud Console](https://console.cloud.google.com/) →
   create a new project (or reuse one) → **APIs & Services** → **Library**
   → enable the **Google Drive API**.
2. **APIs & Services** → **Credentials** → **Create credentials** →
   **API key**.
3. Click the new key → **Restrict key**:
   - **API restrictions**: restrict to **Google Drive API** only.
   - **Application restrictions**: **Websites**, and add your GitHub Pages
     URL from step 3 below (e.g. `terryspitz.github.io/rehearse-the-show/*`).
   This means the key only works from your hosted page and only for reading
   Drive — it's not a secret in the usual sense (it'll be visible in the
   page's source to anyone who opens it), the restriction is what keeps it
   safe to publish.
4. Copy the key, open `docs/index.html` in this repo, find the line near
   the top of the `<script>`:
   ```js
   const API_KEY = "PASTE_YOUR_GOOGLE_DRIVE_API_KEY_HERE";
   ```
   and paste your key in place of the placeholder. Commit and push (or edit
   directly in GitHub's web UI and commit there).

## 3. Turn on GitHub Pages

Repo → **Settings** → **Pages** → **Build and deployment** → **Source**:
"Deploy from a branch" → pick this branch (or `main`, once merged) and the
`/docs` folder → **Save**. GitHub gives you a URL like
`https://terryspitz.github.io/rehearse-the-show/` — that's the link to hand
the cast.

## What the cast will see

Real audio rendered from your show's own MIDI (soundfont synth, not a
recording) for Sky (solo), Tenor, Bass and Piano, with the same live
mixer/tempo/loop controls as the Bach demo prototype. A few things worth
telling them up front, since the page states these but they're easy to miss:

- **Tempo is a placeholder.** Neither scan of the score has a printed
  metronome mark, so the render tempo is a starting guess — use the Tempo
  control to dial in the real pace.
- **Piano and vocals may drift a bar or two mid-song.** They come from two
  separately-scanned, separately-OCR'd sources with different bar counts
  (176 vocal vs 190 piano — see `docs/vocal-midi-accuracy.md`); they're
  aligned at the top of the song and at the Freely/Brightly section
  boundary, not bar-by-bar throughout.
- **No lyrics yet** — not preserved through the MIDI export step used to
  build this render.
- **Treat it as a rehearsal aid, not ground truth** — this is machine
  transcription from your production's own vocal book and piano score;
  known issues (bass line accuracy especially) are in
  `docs/vocal-midi-accuracy.md` and `docs/omr-evaluation.md`.

## Updating later

Re-running the render pipeline and re-uploading files to the same Drive
folder is all that's needed to refresh the cast's copy — the page always
fetches live from Drive, so there's nothing to redeploy except the audio/
score files themselves.
