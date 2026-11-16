# Daily tech Reels — runbook

Three ~20–35-second vertical videos per day for Instagram account **talant_arystanov**
(Windsor.ai connector `instagram`, account id `17841469113945711`), Russian voice-over, one per slot:

| Slot | Publish (Asia/Bishkek) | Rubric (`header`) | Topics |
|---|---|---|---|
| `pc` | **19:00** | Фишки Windows / Фишки ПК | Computers, Windows, laptops, keyboard shortcuts (also macOS when clearly marked) |
| `phone` | **20:00** | Фишки смартфонов | iPhone (iOS), Android, Samsung (One UI) |
| `web` | **21:00** | Интернет и AI | Browsers, useful websites, AI tools, apps |

Each scheduled run handles **only its own slot**. Videos are hosted on GitHub Pages:
`https://talantbey.github.io/kg-v-cifrah/videos/<file>.mp4`.

## Backlog first

If `episodes/backlog/<slot>-*/episode.json` exists, use the oldest one instead of making a new episode:
re-verify its facts quickly, `git mv` it to `episodes/YYYY-MM-DD-<slot>/`, then continue from step 3.

## Video format (every episode)

- `"theme": "tech"`, `"speed"` 0.88–0.95 (voice: Ruslan, male — `make.py` prints `voice: ru_RU-ruslan-medium.onnx`; if it falls back to another voice, mention it in the final message), total **20–35 s** (`make.py` prints it). 4–6 scenes:
  1. `hook` — viral title in 2–3 short lines (≤ 2 s of voice), `highlight` key words, `icon`, `chip` = compatibility (e.g. "Windows 10 · 11", "iPhone · iOS 17+", "Android 14 · Samsung").
  2. `problem` — the pain in one line (+ optional body).
  3. Solution demo — `keys` (shortcut), `phone` (settings path with taps/toggles, 4–6 rows per screen),
     or `laptop` (window/browser with `address`, `screens`, `snip`, `toast`, `keys`).
  4. Optional second demo scene, or `list` = step-by-step (3–4 cards, `head` + `text`).
  5. `cta` — "Подпишись", `sub`, `save` ("Сохрани, чтобы не забыть"), `source` ("Источник: …").
- Every scene has `"desc"` (what happens, Russian) and `"prompt"`: a detailed English prompt for an AI video
  generator (Veo/Kling/Runway) ending with the shared style line:
  `Premium 3D animation, dark navy blue background with cyan and violet neon rim light, cinematic lighting, shallow depth of field, smooth slow camera dolly, consistent tech style, vertical 9:16, no text, no logos, no watermarks.`
- `"package"`: `title` (viral), `hook`, `problem`, `solution`, `steps` (list), `compatibility`, `source`.
- `"caption"`: hook line + emoji, the steps in 1–3 short lines, compatibility, «Сохрани и подпишись», `Источник: …`, then **5–8 relevant hashtags**.
- Reference: `episodes/backlog/pc-screenshot/episode.json` (or the latest dated tech episode) and `tools/tech.py` for fields.

## Content rules

- Instructions must be **real and verifiable today**: confirm with official docs first
  (support.microsoft.com, support.apple.com, support.google.com / Android Help, samsung.com support, the vendor's own help pages),
  otherwise reputable tech media. Name the exact menu path as it appears in Russian UI when known; if the Russian label
  is uncertain, use the wording from the official Russian help page. Always state OS / version compatibility.
- Never invent features, menu items or shortcuts. If something can't be verified, leave it out (or pick another topic).
- Don't repeat a subject from `episodes.md` in the last 60 days (any slot).
- TTS text (first item of each part): spell out what the voice must say — «Вин», «Шифт», «Контрол», «Вэ», «Эс»,
  «Пэйнт», «Гугл Хром», «Вай-фай», «Ай-Оэс», numbers as words. Subtitle (second item) uses normal spelling.
- Keep subtitles ≤ 45 characters per part. No brand logos drawn; brand names as plain text are fine. Neutral tone.

## Steps

1. `bash tools/setup.sh`
2. Research and write `episodes/YYYY-MM-DD-<slot>/episode.json`.
3. `python3 tools/make.py episodes/YYYY-MM-DD-<slot> --stills` → look at `stills/sheet.png`; fix overlaps, clipped or tiny
   text, wrong steps. For `phone`/`laptop` scenes also render 2–3 extra moments with `engine.draw` and look at them.
   Duration must be 20–35 s.
4. `python3 tools/make.py episodes/YYYY-MM-DD-<slot> --reuse-audio` → `video.mp4`, `package.md`, `subtitles.srt`.
   Spot-check 3 frames.
5. Copy to `videos/YYYY-MM-DD-<slot>-<latin-slug>.mp4`; delete files in `videos/` older than 14 days.
   Commit `episode.json`, `package.md`, `subtitles.srt` and the video; `git pull --rebase origin main`; push.
   (Other slots run about an hour apart and push to the same repo — always rebase before pushing; retry once on conflict.)
6. Wait for GitHub Pages: poll `https://api.github.com/repos/Talantbey/kg-v-cifrah/deployments` until the deployment for
   your pushed sha (or a newer one) has status `success`. github.io itself is not reachable from the sandbox.
7. Wait until the slot's publish time (if already past, go on). Publish with Windsor `execute_action`:
   connector `instagram`, action `create_video_post`, account `17841469113945711`,
   params `{video_url, caption, share_to_feed: true, thumb_offset: 1200}`.
   On failure retry once after 2 minutes; if it still fails, tell the user and give the video URL.
8. Append a row to `episodes.md` (date, slot, rubric, subject, video path, media id); pull --rebase, commit, push.
9. Send the user a short message in Kyrgyz: slot, title, compatibility, source, media id.
