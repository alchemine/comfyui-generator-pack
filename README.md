# ComfyUI-Generator-Pack

[English](README.md) | [한국어](README_ko.md)

Suggests the tags most relevant to your prompt from a 5.48M-post Danbooru dataset, and drops the ones that contradict it.

## Usage

Feed a prompt into **Tags Generator**, read the extended prompt out of `processed_text`.

| Widget | What it does |
|--------|--------------|
| `n` | How many tags to add, counted after post-processing. `0` = draw the length from the corpus and stop once nothing beats chance |
| `characters` / `pose` / `expressions` / `body` / `clothes` / `background` | A toggle and a `_share` each. The share is relative to the categories still on: with only `pose 0.2` and `expressions 0.1`, ten tags come back 7 and 3. `-1` = no cap, `0` = off |

The shares are what keep one axis from taking the draw over, since every pick conditions the next. `characters`
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
| `category_order` | The added tags should come back in the same order by kind every time |

Every widget carries its own tooltip — hover it with the node in front of you.

Three things happen without a widget for them. An empty prompt draws an anchor the corpus has plenty to say
about (`beach`, `moon`) and grows a scene from it. A weight at or below zero reverses a tag instead of
asserting it: `(light particles:-1.2)` costs light particles and what travels with them. A one-person prompt
vetoes the tags that need a second character — the list is `resources/solo_conflict.txt`, on disk after the
first run, and it is meant to be edited: your copy is never overwritten.

## Example

[`workflows/comfyui-generator-pack-workflow.json`](workflows/comfyui-generator-pack-workflow.json) — type two tags, watch them grow into a prompt, and render it.

## Installation

Search for **ComfyUI-Generator-Pack** in ComfyUI Manager, or:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-generator-pack
```

## Nodes (`GeneratorPack/Tags`)

**Tags Generator** — the sampler above.

**Tags Conflict Filter** — drops tags contradicting the fixed ones, by co-occurrence lift rather than a
hand-written conflict list. Tags Generator's veto as a node of its own, for tags from anywhere else.

**Classify Tags** — splits a prompt into characters, clothes, body, expression, pose, background, objects,
nsfw, others.

**Group Tags** — one themed group per line; tags sharing a last (or first) word gather together, person tags
lead. `cap` trims each group, colours first.

## Data

Nothing ships in the repository. Every table, label file and list downloads into `resources/` the first time a
node needs it, each pinned by sha256 — the small files as one archive, the statistics tables (up to 100MB)
separately, so a workflow that only groups tags never pulls what the sampler needs. A file already on disk is
never re-fetched, so an edited `solo_conflict.txt` or `wildcards.yaml` stays yours.

## License

GPL-3.0 — see [LICENSE](LICENSE).
