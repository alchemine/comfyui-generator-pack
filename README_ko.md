# ComfyUI-Tags-Generator

[English](README.md) | [한국어](README_ko.md)

프롬프트에 가장 어울리는 태그를 548만 포스트 Danbooru 데이터셋에서 제안하고, 모순되는 태그는 걸러냅니다.

## 사용법

프롬프트를 **Tags Generator**에 넣고 `processed_text`를 받습니다.

| 위젯 | 하는 일 |
|------|---------|
| `n` | 추가할 태그 수, 후처리를 거친 뒤 기준. `0`이면 길이를 코퍼스에서 뽑고 우연 이상으로 나을 게 없으면 멈춥니다 |
| `characters` / `pose` / `expressions` / `body` / `clothes` / `background` | 각각 토글과 `_share`. share는 켜져 있는 카테고리끼리의 상대 비율입니다. `pose 0.2`, `expressions 0.1`만 켜고 10개를 요청하면 7개와 3개. `-1` = 무제한, `0` = 끄기 |

매 선택이 다음 선택의 조건이 되기 때문에, share가 한 축의 독주를 막습니다. `characters`는 주체 자체(`1girl`,
`solo`)를 담당해 뒤따르는 모든 태그의 성별을 고정하고, `background`는 objects·compositions까지 한 몫으로
짊어집니다.

| 이럴 때 | 손잡이 |
|---------|--------|
| `rating` | 수위가 안 맞을 때. `all`은 시드에서 등급을 뽑아 시드마다 다시 굴러갑니다 |
| `momentum` | 태그들이 서로 무관해 보일 때(올리기), 한 장면이 제멋대로 굴러갈 때(내리기) |
| `repetition_penalty` | 같은 얘기 바꿔 쓰기에 예산이 절반 나갈 때 — `blue skin`, `pale skin`, `dark skin` |
| `lift_threshold` | 데이터가 "드물게 한다" 정도인 조합까지 막고 싶을 때. `0.1`은 사실상 함께 나오지 않는 쌍만 잡습니다 |
| `blacklist` | 후보 태그에 걸리는 정규식(`hair\|eyes`, `^black `). `<color>`는 [`resources/wildcards.yaml`](resources/wildcards.yaml)에서 펼쳐집니다. 결과가 아니라 후보를 걸러 `n`은 그대로 채워집니다 |
| `temperature` / `top_k` / `top_p` / `min_p` / `seed` | 익숙한 샘플링 손잡이. `temperature 0`은 argmax |
| `category_order` | 추가된 태그가 매번 같은 종류 순서로 돌아오길 바랄 때 |

모든 위젯에 툴팁이 있습니다. 노드를 띄워 둔 채 마우스를 올려 보세요.

위젯 없이 알아서 도는 것이 셋 있습니다. 빈 프롬프트는 코퍼스가 할 말이 많은 앵커(`beach`, `moon`)를 뽑아 거기서
장면을 키웁니다. 가중치가 0 이하인 태그는 주장이 아니라 반대로 작용합니다 — `(light particles:-1.2)`는 그 태그와
함께 다니는 것들까지 밀어냅니다. 1인 프롬프트에는 두 번째 인물이 필요한 태그가 차단되며, 목록은
[`resources/solo_conflict.txt`](resources/solo_conflict.txt)에서 직접 고치면 됩니다.

## 설치

ComfyUI Manager에서 **ComfyUI-Tags-Generator**를 검색하거나:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-tags-generator
```

## 노드 (`TagsGenerator/Tags`)

**Tags Generator** — 위에서 설명한 샘플러.

**Tags Conflict Filter** — 수작업 충돌 목록 대신 동시출현 lift로 고정 태그와 모순되는 태그를 제거합니다. Tag
Generator의 거부 로직을 독립 노드로 꺼낸 것이라, 출처가 어디든 쓸 수 있습니다.

**Classify Tags** — 프롬프트를 characters, clothes, body, expression, pose, background, objects, nsfw,
others로 나눕니다.

**Group Tags** — 주제별로 한 줄에 한 그룹. 마지막(또는 첫) 단어가 같은 태그끼리 모이고 인물 태그가 맨 앞에
옵니다. `cap`은 각 그룹을 자르며 색 태그부터 버립니다.

## 데이터

저장소에는 데이터가 없습니다. 테이블·라벨·목록 전부 노드가 처음 필요로 할 때 sha256으로 고정된 채
`resources/`로 내려받습니다. 작은 파일은 아카이브 하나로, 최대 100MB짜리 통계 테이블은 따로 받으므로 태그를
묶기만 하는 워크플로는 샘플러용 데이터를 건드리지 않습니다. 이미 있는 파일은 다시 받지 않으니 직접 고친
`solo_conflict.txt`나 `wildcards.yaml`은 그대로 남습니다.

## 라이선스

GPL-3.0 — [LICENSE](LICENSE) 참고.
