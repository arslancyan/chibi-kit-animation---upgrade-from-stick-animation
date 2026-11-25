# Chibi Kit: Animation (upgrade from stick animation)

A Claude-driven pipeline for portrait (9:16) animated shorts: **2D chibi characters acting inside a stylized 3D world
rendered in an anime-film, HD look.** Script, voiceover, word timing, camera plan, render and captions, all driven from Claude Code.

This project is a fork of the MIT-licensed *Ricks Clips Style Kit* by @caesarscales (see `docs/upstream/README.md`,
`LICENSE`, `THIRD_PARTY_NOTICES.md`). We keep its pipeline and tools and replace the character system and the look.

## What changes from upstream
| Area | Upstream | This kit |
|---|---|---|
| Characters | bean-head stickman (`characters/rick.js`) | modular chibi base body, see `docs/09_CHIBI_CHARACTERS.md` |
| Look | thick-ink cartoon 3D world | anime-film HD stylized world, see `docs/10_ANIME_FILM_LOOK.md` |
| Format | 9:16 Shorts | 9:16 (1080x1920) first, 16:9 later |

## Status
- [x] Upstream pipeline imported (tools, engine, Blender builder, rulebook)
- [x] Chibi character spec and anime-film look spec written
- [ ] Chibi renderer (`characters/chibi.js`) replacing `rick.js`
- [x] Base body parts cut into transparent PNGs (`assets/base_body/parts/`, `rig.json` with estimated pivots)
- [x] 8 expression heads cut (`assets/faces/expressions/`)
- [x] Mouth shapes (9), hair (5 views), clothes (11 pieces) and 5-view turnaround cut into transparent PNGs (`assets/mouths|hair|clothes|turnaround`)
- [ ] 20-face personality sheet added as a file (`assets/faces/`), see `docs/11_PERSONALITY_FACES.md`
- [ ] Verify rig pivots with a test render
- [ ] Anime-film grade, toon shader and FX in `engine/` and `blender/`
- [ ] First test short

## Read first
`RULEBOOK.md` (still mandatory, with the chibi overrides in `CLAUDE.md`), then `docs/04_PIPELINE.md`, `docs/09_CHIBI_CHARACTERS.md`, `docs/10_ANIME_FILM_LOOK.md`.

## Requirements
Claude Code, Python 3.10+, Node.js 18+, ffmpeg, Blender 4.2+, a decent GPU for rendering, and an ElevenLabs key for voice (never commit keys).
