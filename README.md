# ComfyUI-Generator-Pack

[English](README.md) | [한국어](README_ko.md)

Suggests the tags most relevant to your prompt from a 5.48M-post Danbooru dataset, and drops the ones that contradict it.

## Usage

Feed a prompt into **Tags Generator**, read the extended prompt out of `processed_text`.

| Widget | What it does |
|--------|--------------|
| `n` | How many tags to add, counted after post-processing. `0` = draw the length from the corpus and stop once nothing beats chance |
| `subject` / `pose` / `expressions` / `body` / `clothes` / `background` | A toggle and a `_share` each. The share is relative to the categories still on: with only `pose 0.2` and `expressions 0.1`, ten tags come back 7 and 3. `-1` = no cap, `0` = off |

The shares are what keep one axis from taking the draw over, since every pick conditions the next. `subject`
owns the subject itself (`1girl`, `solo`), so it anchors the gender of everything after it; `background`
carries objects and compositions on its one share.

| Reach for | When |
|-----------|------|
| `rating` | The explicitness is off. `all` draws a tier from the seed, so a new seed rerolls it |
| `momentum` | The tags have nothing to do with each other (raise), or read as one runaway scene (lower) |
| `repetition_penalty` | Half the draw goes on respelling one idea — `blue skin`, `pale skin`, `dark skin` |
| `lift_threshold` | The output contradicts the prompt in ways the data merely discourages. `0.1` catches only pairs that essentially never co-occur |
| `blacklist` | A regex over the candidates (`hair\|eyes`, `^black `). `<color>` expands from `resources/wildcards.yaml`. Filters candidates, so `n` still holds |
| `temperature` / `top_k` / `top_p` / `min_p` / `seed` | The usual sampling knobs. `temperature 0` is argmax |
| `filter_copyright` | On by default: drops candidates owned by one character or franchise — the tags that turn a library into Patchouli's library. `resources/copyright_blacklist.txt` adds the ones the statistics miss, and is meant to be edited. Your own tags are never dropped |
| `order_tags` | On by default: the added tags come back grouped by kind — subject, body, expressions, pose, clothes, scene. Off keeps the draw order. The input prompt is never reordered |

Every widget carries its own tooltip — hover it with the node in front of you.

Three things happen without a widget for them. An empty prompt draws an anchor the corpus has plenty to say
about (`beach`, `moon`) and grows a scene from it. A weight at or below zero reverses a tag instead of
asserting it: `(light particles:-1.2)` costs light particles and what travels with them. A one-person prompt
vetoes the tags that need a second character — the list is `resources/solo_conflict.txt`, on disk after the
first run, and it is meant to be edited: your copy is never overwritten.

## Example

[`workflows/comfyui-generator-pack-workflow.json`](workflows/comfyui-generator-pack-workflow.json)

![Workflow](workflows/comfyui-generator-pack-workflow.png)

[`workflows/comfyui-generator-pack-tagsextractor-workflow.json`](workflows/comfyui-generator-pack-tagsextractor-workflow.json) starts from a sentence instead of tags: **Tags Extractor** in front of the same chain.

## Installation

Search for **ComfyUI-Generator-Pack** in ComfyUI Manager, or:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-generator-pack
```

## Nodes (`GeneratorPack/Tags`)

**Tags Extractor** — a sentence in, the Danbooru tags it names out. Every run of up to three words is looked up
against the vocabulary and its aliases, so only real tags come back, and only ones the sentence said: `sits`
reaches `sitting`, `oppai` reaches `breasts`, `low ponytail` is one tag, and `without a hat` yields `missing
headwear` rather than `hat`. The people are counted rather than looked up — `a girl` is `1girl, solo`, `a girl and
two boys` is `1girl, 2boys`, `hugging him` is someone else and no `solo` — and `subject` turns that off. Family
words count too, and a pair of them says what it is: `mother and daughter` is `2girls` and the tag of that name. `translate`
runs the text through Google Translate into English first, whatever language it is in (`googletrans`, one request
per run). `min_count` and `blacklist` are Tags Generator's, for an alias that lands wrong: `taking off` reaches
`takeoff` (130 posts) through `take-off`. `table` shows every match with the spelling it came in through and the
post count, so that kind of turn is read off the node. A phrase the vocabulary cannot spell is looked for in the
Danbooru wiki instead — the first sentence of each tag's page — and comes back marked `wiki` in the table: `taking
off` is in the definition of `undressing`. The tags come back grouped by kind, in Tags Generator's order. Feed
`processed_text` to Tags Generator to grow the scene.

**Tags Generator** — the sampler above.

**Character Tags Generator** — draws `n` Danbooru character tags, weighted by post count, from the 16,943
characters with at least 100 posts up to 2025-09. `sex` keeps girls, boys or others — whichever of `1girl`, `1boy`,
`1other` sits on most of the character's solo posts, `other` on a tie. `year_min` and `year_max` limit the year of
the character's first post, `min_count` its post count. `subject` puts the person count in front: `1girl, solo` for
one girl, `1girl, 1boy` for a girl and a boy.

**Tags Conflict Filter** — drops tags contradicting the fixed ones, by co-occurrence lift rather than a
hand-written conflict list. Tags Generator's veto as a node of its own, for tags from anywhere else.

**Classify Tags** — splits a prompt into subject, clothes, body, expression, pose, background, objects,
nsfw, others.

**Group Tags** — one themed group per line; tags sharing a last (or first) word gather together, person tags
lead. `cap` trims each group, colours first.

## Data

`translate` is the one thing that leaves the machine: it sends the text to Google Translate through `googletrans`.
Everything else runs offline.


Nothing ships in the repository. Every table, label file and list downloads into `resources/` the first time a
node needs it, each pinned by sha256 — the small files as one archive, the statistics tables (up to 100MB)
separately, so a workflow that only groups tags never pulls what the sampler needs. A file already on disk is
never re-fetched, so an edited `solo_conflict.txt`, `copyright_blacklist.txt` or `wildcards.yaml` stays yours.

## License

GPL-3.0 — see [LICENSE](LICENSE).
