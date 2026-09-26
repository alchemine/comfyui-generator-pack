# ComfyUI-Generator-Pack

[English](README.md) | [한국어](README_ko.md)

프롬프트에 가장 어울리는 태그를 548만 포스트 Danbooru 데이터셋에서 제안하고, 모순되는 태그는 걸러냅니다.
문장을 태그로 바꾸고, Danbooru 캐릭터 태그를 뽑는 노드도 있습니다.

## 예시

![Workflow](workflows/comfyui-generator-pack-workflow.png)

예시 워크플로는 세 노드를 잇습니다. **Tags Extractor**가 문장을 태그로 바꾸고, **Character Tags Generator**가
뽑은 캐릭터를 거기에 붙이고, **Tags Generator**가 그 결과를 프롬프트 전체로 키웁니다.

## 사용법

### Tags Generator

프롬프트를 **Tags Generator**에 넣고 `processed_text`를 받습니다.

| 위젯 | 하는 일 |
|------|---------|
| `n` | 추가할 태그 수, 후처리를 거친 뒤 기준. `0`이면 길이를 코퍼스에서 뽑고 우연 이상으로 나을 게 없으면 멈춥니다 |
| `subject` / `pose` / `expressions` / `body` / `clothes` / `background` | 각각 토글과 `_share`. share는 켜져 있는 카테고리끼리의 상대 비율입니다. `pose 0.2`, `expressions 0.1`만 켜고 10개를 요청하면 7개와 3개. `-1` = 무제한, `0` = 끄기 |

| 이럴 때 | 손잡이 |
|---------|--------|
| `rating` | 수위가 안 맞을 때. `all`은 시드에서 등급을 뽑아 시드마다 다시 굴러갑니다 |
| `momentum` | 태그들이 서로 무관해 보일 때(올리기), 한 장면이 제멋대로 굴러갈 때(내리기) |
| `repetition_penalty` | 같은 얘기 바꿔 쓰기에 예산이 절반 나갈 때. 예: `blue skin`, `pale skin`, `dark skin` |
| `lift_threshold` | 데이터가 "드물게 한다" 정도인 조합까지 막고 싶을 때. `0.1`은 사실상 함께 나오지 않는 쌍만 잡습니다 |
| `blacklist` | 후보 태그에 걸리는 정규식(`hair\|eyes`, `^black `). `<color>`는 `resources/wildcards.yaml`에서 펼쳐집니다. 결과가 아니라 후보를 걸러 `n`은 그대로 채워집니다 |
| `temperature` / `top_k` / `top_p` / `min_p` / `seed` | 익숙한 샘플링 손잡이. `temperature 0`은 argmax |
| `filter_copyright` | 기본 켜짐: 특정 캐릭터·작품 전유 태그를 후보에서 제외합니다. 도서관을 파츄리의 도서관으로 만드는 그 태그들입니다. 통계가 놓치는 건 `resources/copyright_blacklist.txt`에 직접 적으면 되고, 고쳐 쓰라고 있는 파일입니다. 직접 입력한 태그는 건드리지 않습니다 |
| `order_tags` | 기본 켜짐: 추가된 태그가 종류별로(인물, 몸, 표정, 자세, 의상, 배경 순) 정렬돼 돌아옵니다. 끄면 뽑힌 순서 그대로. 입력 프롬프트는 건드리지 않습니다 |

모든 위젯에 툴팁이 있습니다. 노드를 띄워 둔 채 마우스를 올려 보세요.

위젯 없이 알아서 도는 것이 셋 있습니다.

- 빈 프롬프트는 앵커(`beach`, `moon`)를 뽑아 거기서 장면을 키웁니다.
- 가중치가 0 이하인 태그는 반대로 밀어냅니다. 예: `(light particles:-1.2)`
- 1인 프롬프트에는 두 번째 인물이 필요한 태그를 막습니다. 목록은 첫 실행 후 생기는 `resources/solo_conflict.txt`에서 고칠 수 있습니다.

### Character Tags Generator

게시물이 100개 이상인 Danbooru 캐릭터 태그를 뽑습니다. 후보는 모두 같은 확률로 뽑힙니다.

| 위젯 | 하는 일 |
|------|---------|
| `n` | 뽑을 캐릭터 수 |
| `sex` | girl, boy, other 중 후보로 둘 성별, 하나 이상. 캐릭터의 solo 게시물에 `1girl`, `1boy`, `1other` 중 가장 많이 붙은 쪽이 그 성별이고, 동점이면 `other`입니다 |
| `subject` | 인원 태그를 앞에 붙입니다. 여자 한 명은 `1girl, solo`, 여자와 남자 한 명씩은 `1girl, 1boy`입니다 |
| `year_min` / `year_max` | 각각 토글과 연도. 캐릭터의 첫 게시 연도를 제한합니다 |
| `min_count` | 게시물이 이 수 이상인 캐릭터만 |

### Tags Extractor

문장을 넣으면 그 문장이 말하는 실제 Danbooru 태그만 돌려줍니다. 어휘에 없는 구는 Danbooru wiki 정의에서 찾습니다.

| 위젯 | 하는 일 |
|------|---------|
| `subject` | 인물을 세서 인원 태그를 붙입니다. `a girl and two boys`는 `1girl, 2boys` |
| `translate` | 먼저 Google 번역으로 영어로 바꿉니다 (`googletrans`, 실행당 요청 1건) |
| `min_count` | 포스트 수가 이보다 적은 태그는 뺍니다 |
| `blacklist` | 결과에서 뺄 태그의 정규식 |
| `table` (출력) | 매칭마다 거쳐 온 철자와 포스트 수 |

## 설치

ComfyUI Manager에서 **ComfyUI-Generator-Pack**를 검색하거나:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-generator-pack
```

## 노드 (`GeneratorPack/Tags`)

**Tags Conflict Filter**: 수작업 충돌 목록 대신 동시출현 lift로 고정 태그와 모순되는 태그를 제거합니다. Tag
Generator의 거부 로직을 독립 노드로 꺼낸 것이라, 출처가 어디든 쓸 수 있습니다.

**Classify Tags**: 프롬프트를 subject, clothes, body, expression, pose, background, objects, nsfw,
others로 나눕니다.

**Group Tags**: 주제별로 한 줄에 한 그룹. 마지막(또는 첫) 단어가 같은 태그끼리 모이고 인물 태그가 맨 앞에
옵니다. `cap`은 각 그룹을 자르며 색 태그부터 버립니다.

## 데이터

기기 밖으로 나가는 것은 `translate` 하나입니다. `googletrans`로 문장을 Google 번역에 보냅니다. 나머지는 전부
오프라인입니다.

캐릭터 목록은 2025-09까지의 게시물을 담은 danbooru-2026-clean-metadata로 만들었습니다.


저장소에는 데이터가 없습니다. 테이블·라벨·목록 전부 노드가 처음 필요로 할 때 sha256으로 고정된 채
`resources/`로 내려받습니다. 작은 파일은 아카이브 하나로, 최대 100MB짜리 통계 테이블은 따로 받으므로 태그를
묶기만 하는 워크플로는 샘플러용 데이터를 건드리지 않습니다. 이미 있는 파일은 다시 받지 않으니 직접 고친
`solo_conflict.txt`·`copyright_blacklist.txt`·`wildcards.yaml`은 그대로 남습니다.

## 라이선스

GPL-3.0. [LICENSE](LICENSE) 참고.
