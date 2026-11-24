# Daily fruit Reels — runbook

Three ~25–35-second vertical videos per day for Instagram account **talant_arystanov**
(Windsor.ai connector `instagram`, account id `17841469113945711`), Russian voice-over (voice: Ruslan), one per slot.
Topic: **польза фруктов и ягод** (since 2026-11-24; earlier tech episodes stay in `episodes.md`).

| Slot | Publish (Asia/Bishkek) | Rubric (`header`) | What a good episode looks like |
|---|---|---|---|
| `fruit` | **19:00** | Фрукт дня | One fruit/berry: hook, nutrients per 100 g (2–4 tiles), 2–3 benefits, «Кому осторожно», finale. |
| `myth` | **20:00** | Миф или факт? | One popular claim («Бананы на ночь мешают похудеть», «Яблочные косточки полезны»…): statement → verdict МИФ / ФАКТ / ЧАСТИЧНО → short evidence → what to do. |
| `compare` | **21:00** | Сравнение | Compare 3–5 fruits on one nutrient (vitamin C, fibre, sugar, potassium, calories) with `compare` bars, or a local-fruit episode («Наше родное»: урюк, облепиха, яблоки, дыня, черешня…), or how to choose/store a fruit. |

Each scheduled run handles **only its own slot**. Videos are hosted on GitHub Pages:
`https://talantbey.github.io/kg-v-cifrah/videos/<file>.mp4`.

## Backlog first

If `episodes/backlog/<slot>-*/episode.json` exists, use the oldest one instead of making a new episode:
re-verify its facts quickly, `git mv` it to `episodes/YYYY-MM-DD-<slot>/`, then continue from step 3.

## Video format

- `"theme": "fresh"`, `"speed"` 0.88–0.95, total **25–35 s** (`make.py` prints it and `voice: ru_RU-ruslan-medium.onnx`;
  if another voice is used, say so in the final message). 4–6 scenes. Scene types (see `tools/fruits.py`):
  - `fruit` — hero/hook: `fruit` (vector kind), `name`, `kicker`, `lines` (2 short hook lines), `highlight`.
  - `nutrients` — `title`, `subtitle` ("по данным USDA"), up to 4 `tiles` {value, decimals, unit, label, note, color}, `active` per part.
  - `myth` — `statement`, `verdict` (МИФ / ФАКТ / ЧАСТИЧНО), `body`, `fruit`, `verdict_at_part`, `body_at_part`.
  - `compare` — `title`, `subtitle`, `rows` {label, value, fruit, text, best}, `unit`.
  - `caution` — `title`, `items` (1–3 short lines).
  - `finale` — `fruits` (3 kinds), `cta`, `sub`, `save`, `source`, `disclaimer`.
  - Generic `list` (benefits/steps), `fact`, `bars`, `donut`, `counter` also work in this theme.
- Vector fruit kinds: apple, green_apple, orange, tangerine, lemon, lime, grapefruit, orange_half, lemon_half, kiwi, banana,
  pomegranate, pomegranate_seeds, apricot, peach, plum, grapes, grapes_green, cherry, strawberry, pear, watermelon, melon,
  persimmon, sea_buckthorn, currant, avocado, mango (`python3 tools/fruits.py /tmp/f.png` draws them all). Prefer fruits in this list.
- Every scene has `"desc"` (Russian) and `"prompt"`: a detailed English AI-video prompt ending with the shared style line:
  `Premium 3D food animation, deep green background with warm orange and fresh green rim light, cinematic lighting, macro lens, shallow depth of field, juicy realistic textures, water droplets, smooth slow camera dolly, consistent fresh style, vertical 9:16, no text, no logos, no watermarks.`
- `"package"`: `title`, `hook`, `problem`, `solution`, `steps`, `compatibility` (variety / form, e.g. «зелёный киви, свежий»), `source`.
- `"caption"`: hook + emoji, 2–3 short lines of facts, caution line if any, «Не является медицинской рекомендацией.»,
  `Источники: …`, «Сохрани и подпишись», then **5–8 hashtags**.
- Reference episode: `episodes/backlog/fruit-kiwi/episode.json` (after it is used, the latest dated fresh episode).

## Real photos (Wikimedia Commons)

- Fruits are drawn from **real photo cut-outs** in `assets/photos/<kind>/main.png` when they exist (hero scene also uses
  a blurred `bg.jpg` behind; middle scenes show the episode's main fruit peeking from a corner). Otherwise the vector fruit is used.
  `python3 tools/photos.py list` shows the library and credits.
- If the episode's main fruit has no photo yet, add one **before rendering**:
  1. `python3 tools/photos.py search <kind> "<english query>" --n 12` (e.g. `persimmon "persimmon fruit white background"`).
     Only CC0 / Public domain / CC BY are downloaded (no BY-SA, NC, ND).
  2. LOOK at `assets/photos/<kind>/cand/sheet.png`. Choose a clean, sharp, colour photo of the fruit itself (whole or cut),
     ideally on a plain background. Reject: paintings/illustrations, old black-and-white photos, text/labels/stickers/logos,
     people, markets/crowded piles, wrong variety. If nothing fits, try another query once; if still nothing, use the vector.
  3. `python3 tools/photos.py pick <kind> <number>` → cut-out + `meta.json` (author, licence, link). Look at the cut-out on a
     still frame; if the background removal is bad, pick another candidate.
  4. Commit `assets/photos/<kind>/` (main.png, bg.jpg, meta.json) with the episode.
- Kind names: use the vector names from the list above when they match (apple, kiwi, orange…), so vector fallback works;
  a new kind name (e.g. `fig`) is fine once it has a photo.
- Photo credits are added automatically: in the finale («Фото: …») and in `caption.txt`. **Publish `caption.txt`**, not the raw
  `"caption"` field. Wikimedia may answer 429 (rate limit) — the tool waits and retries; don't hammer it.

## Health-content rules (strict)

- Nutrient numbers: **USDA FoodData Central** (say which entry, raw/fresh, per 100 g; prefer SR Legacy, keep one entry per
  episode). "% нормы" only from FDA Daily Values (vitamin C 90 mg, potassium 4700 mg, fibre 28 g, …) and say «≈».
- Benefits: only what official bodies (WHO/ВОЗ, NIH ODS, NHS, EFSA, Harvard T.H. Chan) or peer-reviewed human studies
  (PubMed/PMC) support. Word it carefully: «помогает», «связан с», «в исследовании…» — never «лечит», «излечивает»,
  «защищает от рака», «сжигает жир», «выводит токсины».
- Add «Кому осторожно» when relevant (allergy, drug interactions such as grapefruit, diabetes and sugar, kidney disease and
  potassium, reflux and citrus) — but only cautions that a source states.
- Myths: a verdict must be backed by a source; if evidence is mixed, use «ЧАСТИЧНО».
- If a fact or number can't be verified today, leave it out or pick another topic. No fake precision.
- Don't repeat a subject from `episodes.md` in the last 60 days (any slot).
- TTS text: numbers as words in the right case; «витамин Цэ»; abbreviations spelled out or replaced
  («по данным Минсельхоза США» instead of USDA). Subtitles ≤ 45 characters per part, normal spelling.

## Steps

1. `bash tools/setup.sh`
2. Research and write `episodes/YYYY-MM-DD-<slot>/episode.json`.
3. `python3 tools/make.py episodes/YYYY-MM-DD-<slot> --stills` → look at `stills/sheet.png`; fix overlaps, clipped or tiny text,
   empty-looking scenes (make the first card/item appear at part 0). Duration must be 25–35 s.
4. `python3 tools/make.py episodes/YYYY-MM-DD-<slot> --reuse-audio` → `video.mp4`, `package.md`, `subtitles.srt`. Spot-check 3 frames.
5. Copy to `videos/YYYY-MM-DD-<slot>-<latin-slug>.mp4`; delete files in `videos/` older than 14 days.
   Commit `episode.json`, `package.md`, `subtitles.srt`, `caption.txt`, any new `assets/photos/<kind>/` and the video; `git pull --rebase origin main`; push (retry once on conflict).
6. Wait for GitHub Pages: poll `https://api.github.com/repos/Talantbey/kg-v-cifrah/deployments` until the deployment for
   your pushed sha (or a newer one) has status `success`. github.io itself is not reachable from the sandbox.
7. Wait until the slot's publish time (if already past, go on). Publish with Windsor `execute_action`:
   connector `instagram`, action `create_video_post`, account `17841469113945711`,
   params `{video_url, caption: <contents of episodes/YYYY-MM-DD-<slot>/caption.txt>, share_to_feed: true, thumb_offset: 1500}`.
   On failure retry once after 2 minutes; if it still fails, tell the user and give the video URL.
8. Append a row to `episodes.md` (date, slot, rubric, subject, video path, media id); pull --rebase, commit, push.
9. Send the user a short message in Kyrgyz: slot, title, main facts, sources, media id.
