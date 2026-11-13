# Daily Reel — runbook

One ~60-second vertical infographic video per day for Instagram account **talant_arystanov**
(Windsor.ai connector `instagram`, account id `17841469113945711`), with a Russian narrator,
published at **21:00 Asia/Bishkek**.

Videos are hosted on GitHub Pages of this repo: `https://talantbey.github.io/kg-v-cifrah/videos/<file>.mp4`.

## Topic by weekday (Asia/Bishkek date)

| Day | Rubric (header) | What a good episode looks like |
|---|---|---|
| Mon | Кыргызстан в цифрах · <тема> | One dataset about Kyrgyzstan: prices, wages, exchange rate, exports, budget, tourism, energy… Animated counter + bars/donut/scale. |
| Tue | Финансовая грамотность | One practical topic: deposit vs. inflation, how a loan's real rate works, budgeting rule, a fraud scheme. Education, never advice on specific products. |
| Wed | Английский · 5 слов | 5 useful English words around one theme, each with transcription in Russian letters, meaning, short example. |
| Thu | История и легенды | A Kyrgyz history episode or a Manas episode retold in your own words; timeline scene for dates. |
| Fri | Наука · а вы знали? | 3–5 surprising, verifiable facts on one theme (space, body, nature). |
| Sat | AI и технологии | Practical tips: phone security, useful AI tools, how to spot deepfakes/scams. |
| Sun | Кыргызстан в цифрах · <тема> | Same as Monday, different dataset. |

Check `episodes.md` first and do not repeat a subject used in the last 60 days.

## Content rules

- Narration and on-screen text are **Russian**. Length **52–63 s** total (`make.py` prints it). 6–8 scenes: first `title`, last `outro` with the source.
- Every number and fact must come from a source found **today** via web search; prefer official sources
  (stat.gov.kg — Нацстатком, nbkr.kg — Нацбанк, minfin.kg, gov.kg, WHO/UN/NASA, peer-reviewed or major media).
  Never invent or estimate figures. If a figure can't be verified, drop it. Name the source in the outro and caption.
- TTS text (first item of each part) must have **numbers written as words** in the correct grammatical case,
  and abbreviations spelled out for the voice (ООН → «О О Эн», ВВП → «вэ вэ пэ», СМС → «эс эм эс»).
  The subtitle (second item) uses normal digits/abbreviations.
- English words: the voice can't pronounce English; in TTS write the Russian-letter transcription
  (e.g. «ризилиенс»), show the real word on screen.
- Keep parts short (one clause each, ≤ 45 characters of subtitle) — subtitles are timed by character share.
- Neutral tone; no politics, no claims about real people beyond verifiable facts; no copyrighted characters or logos.
- Finance episodes: general education only, add «не является финансовой рекомендацией» in the caption.

## Steps

1. `bash tools/setup.sh`
2. Research the topic (web search, several sources). Write `episodes/YYYY-MM-DD/episode.json`
   (see `episodes/2026-11-12/episode.json` and `tools/examples/all_scene_types.json`; scene fields are in `tools/engine.py`).
   Include `"caption"`: 1–2 sentence hook, `Источник: …`, 4–6 hashtags (#Кыргызстан first).
3. `python3 tools/make.py episodes/YYYY-MM-DD --stills` → open `episodes/YYYY-MM-DD/stills/sheet.png` and look at it.
   Fix overlaps, clipped or too-long text, wrong numbers; repeat (add `--reuse-audio` if only visuals changed).
   Total duration must be 52–63 s: shorten/lengthen text or adjust `"speed"` (0.80–0.90).
4. `python3 tools/make.py episodes/YYYY-MM-DD --reuse-audio` → `episodes/YYYY-MM-DD/video.mp4`.
   Spot-check 3 frames with ffmpeg and look at them.
5. `cp` it to `videos/YYYY-MM-DD-<slug>.mp4` (latin slug). Delete files in `videos/` older than 14 days
   (Instagram keeps its own copy). Commit (`episodes/YYYY-MM-DD/episode.json` + video) and push to `main`.
6. Wait for GitHub Pages: poll `https://api.github.com/repos/Talantbey/kg-v-cifrah/deployments` until the
   deployment for the pushed sha has status `success` (`/deployments/<id>/statuses`). github.io itself is not reachable from the sandbox.
7. Wait until 21:00 Asia/Bishkek (if already past, go on). Publish with Windsor `execute_action`:
   connector `instagram`, action `create_video_post`, account `17841469113945711`,
   params `{video_url, caption, share_to_feed: true, thumb_offset: 2500}`.
   On failure retry once after 2 minutes; if it still fails, tell the user and give the video URL.
8. Append a row to `episodes.md` (date, rubric, subject, video path, media id), commit, push.
9. Send the user a short message (Kyrgyz): what was published, the subject, the source.
