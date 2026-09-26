# ComfyUI-Generator-Pack

[English](README.md) | [한국어](README_ko.md)

Suggests the tags most relevant to your prompt from a 5.48M-post Danbooru dataset, and drops the ones that contradict it.
It also turns a sentence into tags and draws Danbooru character tags.

## Example

![Workflow](workflows/comfyui-generator-pack-workflow.png)

The example workflow chains three nodes. **Tags Extractor** turns a sentence into tags, **Character Tags Generator**
draws characters to join them, and **Tags Generator** grows the result into a full prompt.

## Usage

### Tags Generator

Feed a prompt into **Tags Generator**, read the extended prompt out of `processed_text`.

| Widget | What it does |
|--------|--------------|
| `n` | How many tags to add, counted after post-processing. `0` = draw the length from the corpus and stop once nothing beats chance |
| `subject` / `pose` / `expressions` / `body` / `clothes` / `background` | A toggle and a `_share` each. The share is relative to the categories still on: with only `pose 0.2` and `expressions 0.1`, ten tags come back 7 and 3. `-1` = no cap, `0` = off |

| Reach for | When |
|-----------|------|
| `rating` | The explicitness is off. `all` draws a tier from the seed, so a new seed rerolls it |
| `momentum` | The tags have nothing to do with each other (raise), or read as one runaway scene (lower) |
| `repetition_penalty` | Half the draw goes on respelling one idea: `blue skin`, `pale skin`, `dark skin` |
| `lift_threshold` | The output contradicts the prompt in ways the data merely discourages. `0.1` catches only pairs that essentially never co-occur |
| `blacklist` | A regex over the candidates (`hair\|eyes`, `^black `). `<color>` expands from `resources/wildcards.yaml`. Filters candidates, so `n` still holds |
| `temperature` / `top_k` / `top_p` / `min_p` / `seed` | The usual sampling knobs. `temperature 0` is argmax |
| `filter_copyright` | On by default: drops candidates owned by one character or franchise: the tags that turn a library into Patchouli's library. `resources/copyright_blacklist.txt` adds the ones the statistics miss, and is meant to be edited. Your own tags are never dropped |
| `order_tags` | On by default: the added tags come back grouped by kind: subject, body, expressions, pose, clothes, scene. Off keeps the draw order. The input prompt is never reordered |

Every widget carries its own tooltip; hover it with the node in front of you.

Three things happen without a widget:

- An empty prompt draws an anchor (`beach`, `moon`) and grows a scene from it.
- A weight at or below zero pushes a tag away: `(light particles:-1.2)`.
- A one-person prompt blocks tags that need a second character. The list is `resources/solo_conflict.txt`, editable after the first run.

### Character Tags Generator

Draws Danbooru character tags from the characters with at least 100 posts, all equally likely.

| Widget | What it does |
|--------|--------------|
| `n` | How many characters to draw |
| `sex` | Which of girl, boy, other to draw from, at least one. A character's sex is whichever of `1girl`, `1boy`, `1other` sits on most of its solo posts, `other` on a tie |
| `subject` | Puts the person count in front: `1girl, solo` for one girl, `1girl, 1boy` for a girl and a boy |
| `year_min` / `year_max` | A toggle and a year each, limiting the year of the character's first post |
| `min_count` | Only characters with at least this many posts |

### Tags Extractor

Turns a sentence into the real Danbooru tags it names. A phrase the vocabulary cannot spell is looked up in the Danbooru wiki.

| Widget | What it does |
|--------|--------------|
| `subject` | Counts the people into person tags: `a girl and two boys` is `1girl, 2boys` |
| `translate` | Runs the text through Google Translate into English first (`googletrans`, one request per run) |
| `min_count` | Drops tags with fewer posts than this |
| `blacklist` | A regex for tags to drop from the result |
| `table` (output) | Every match with the spelling it came in through and its post count |

## Installation

Search for **ComfyUI-Generator-Pack** in ComfyUI Manager, or:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-generator-pack
```

## Nodes (`GeneratorPack/Tags`)

**Tags Conflict Filter**: drops tags contradicting the fixed ones, by co-occurrence lift rather than a
hand-written conflict list. Tags Generator's veto as a node of its own, for tags from anywhere else.

**Classify Tags**: splits a prompt into subject, clothes, body, expression, pose, background, objects,
nsfw, others.

**Group Tags**: one themed group per line; tags sharing a last (or first) word gather together, person tags
lead. `cap` trims each group, colours first.

## Data

`translate` is the one thing that leaves the machine: it sends the text to Google Translate through `googletrans`.
Everything else runs offline.

The character list is built from danbooru-2026-clean-metadata, which runs to 2025-09.


Nothing ships in the repository. Every table, label file and list downloads into `resources/` the first time a
node needs it, each pinned by sha256: the small files as one archive, the statistics tables (up to 100MB)
separately, so a workflow that only groups tags never pulls what the sampler needs. A file already on disk is
never re-fetched, so an edited `solo_conflict.txt`, `copyright_blacklist.txt` or `wildcards.yaml` stays yours.

## License

GPL-3.0. See [LICENSE](LICENSE).
