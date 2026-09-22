# #10 Add TagsExtractor node: natural language to Danbooru tags

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/10

## 이슈
- `TagsGenerator`와 `TagsConflictFilter`는 입력이 Danbooru 태그일 때만 동작한다. 자연어 문장이나 없는 태그는 조건에 쓰이지 않고 무시된다.
- LLM에게 태그를 바로 만들게 하면 없는 태그를 지어내거나 서로 모순되는 태그를 낸다. 학습된 모델(TIPO 등)은 출력을 통제하기 어렵다.
- 자연어를 실제 태그로 바꾸는 결정적인 단계가 없다.

## 해결책
- `nodes/lib/tag_search.py`를 추가한다. `search_tags(text, max_tags)`가 문장을 받아 실제 Danbooru general 태그 목록을 돌려준다.
- 색인은 `resources/danbooru-tags.txt`의 general 태그 이름(밑줄을 공백으로)과 alias로 만든다. 표준 라이브러리 `sqlite3`의 FTS5 메모리 테이블 두 개다. 하나는 쓰인 그대로(`unicode61`), 하나는 어근(`porter unicode61`)으로 색인한다. 빌드가 0.2초라 파일로 저장하지 않는다. 의존성은 추가하지 않는다.
- 문장을 1~3단어 구간으로 잘라 그 구간이 태그 철자 전체와 같을 때만 맞는 것으로 본다. `ponytail`이 `high ponytail`을 끌어오지 않는다. 긴 구간이 짧은 구간보다 먼저 단어를 차지한다.
- 어근 테이블은 구간에 활용형(`s`, `ing`, `ed`로 끝나는 단어)이 있을 때만 본다. 어근 처리는 `short`를 `shorts`로도 접기 때문이다.
- 이름을 앞에서 자른 alias(`sitting on` → `sitting on person`, `blonde` → `blonde hair`)는 구간 끝에 올 때만 믿는다. `sitting on a chair`는 이름과 다르게 이어지므로 다른 뜻이다.
- bm25 순위 채우기는 하지 않는다. 문장에 없는 단어를 가진 태그가 들어와 무모순 목표와 어긋난다.
- `no`, `not`, `without`은 다음 `and`/`but`/`with`나 문장 부호까지를 부정 구간으로 연다. 구간 자체가 태그면 그것을 낸다(`no hat`은 `missing headwear`의 alias). 나머지는 후보에서 뺀다.
- 관사와 대명사(`a`, `the`, `her`, `his` 등)는 건너뛴다. `hand on her hip`이 `hand on own hip`에 닿는다.
- 사람 명사는 검색하지 않고 센다. 바로 앞의 수 단어(`a`, `two`, `3`)를 붙여 `1girl`, `2girls`, `3boys`로, 6명 이상은 `6+girls`로, 수 없는 복수형은 `multiple girls`로 낸다. 합쳐 한 명이면 `solo`를 붙인다. `girl`/`woman`/`lady`는 girl, `boy`/`man`/`guy`는 boy다. 센 명사는 검색에서 소비되므로 `a man`이 alias로 `male focus`에 닿지 않는다.
- 동사 뒤의 목적어 대명사(`her`, `him`, `them`)는 그림 속 다른 사람이다. `-ing` 단어 바로 뒤, 또는 `-ing` 단어와 `at`/`to`/`with` 뒤에 오면 `another`로 바꾼다. Danbooru가 그렇게 쓴다(`looking at another`, `undressing another`). 다른 사람이 있으므로 `solo`도 붙이지 않는다.
- `min_count`는 포스트 수가 그보다 적은 태그를 뺀다. 기본 100은 `TagsGenerator`의 어휘 바닥이고 덤프는 20까지 내려간다. 희귀 태그의 alias가 구간을 잡을 때 올린다. `taking off`가 `take-off`를 거쳐 `takeoff`(130 포스트, 비행기 이륙)에 닿는 사례다. 빠진 태그는 단어를 차지하지 않으므로 그 밑의 짧은 구간이 다시 맞을 수 있다.
- 결과는 `_sort_by_category`로 종류별(인물, 몸, 표정, 자세, 의상, 배경)로 항상 정렬한다. `TagsGenerator`와 같은 함수와 순서이고 위젯은 없다.
- 두 번째 출력 `table`은 매칭 하나마다 한 줄이다. 맞은 구간, 태그, 거쳐 온 철자(alias면), 포스트 수, 판정(`kept`, `below min_count`, `blacklisted`)을 적는다. 인물 수 태그는 구간 `(count)`로 적는다. `TagsConflictFilter`의 `table`과 같은 형식이다.
- `TagsExtractor` 노드를 `nodes/tags.py`에 추가하고 `__init__.py`에 등록한다. 입력은 `text`(자연어), `max_tags`, `min_count`, `subject`, `translate`, `blacklist`, 출력은 `processed_text`(쉼표로 이은 태그)와 `table`이다. `subject`를 끄면 인물 수 태그를 붙이지 않는다. 사람 명사는 어느 쪽이든 검색하지 않는다.
- `blacklist`는 `TagsGenerator`와 같은 규칙의 정규식이다. `blacklist_pattern`으로 만들어 검색 결과에서 맞는 태그를 빼고, 그 뒤에 `max_tags`를 센다. `man`이 alias로 `male focus`에 닿는 것을 `male focus`로 막는다.
- 예제 워크플로 `workflows/comfyui-generator-pack-tagsextractor-workflow.json`을 추가하고 README 두 개에 노드와 예제를 적는다.
- `translate`를 켜면 검색 전에 `googletrans`로 영어(`dest="en"`)로 번역한다. 입력 언어는 보지 않고 항상 번역한다. 영어 입력도 다시 쓰이므로 검색이 걸려 넘어질 문법 오류가 펴진다. 실행당 Google 요청 1건이다.
- `TagsExtractor.execute`는 `async def`다. ComfyUI는 프롬프트 실행 전체를 `asyncio.run` 안에서 돌리고(`execution.py`), 코루틴 함수는 그 루프에서 `await`한다. 동기 함수 안에서 `asyncio.run`을 다시 부르면 "cannot be called from a running event loop"가 난다. `exception_handler`와 `log_prompt`는 동기 래퍼라 코루틴 함수를 가리므로 이 노드에는 씌우지 않는다.
- `requirements.txt`를 새로 만들어 `googletrans`를 적는다. 이 팩의 첫 외부 의존성이다. 없으면 `translate`를 켰을 때만 에러가 난다.
- 버전을 2.0.0으로 올린다. 노드 추가는 major다.

## 테스트 계획
테스트는 `tests/issue/10-add-tagsextractor-node/`에 있다. `resources/danbooru-tags.txt`가 없으면 `artifact.bundled`가 내려받는다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_the_node_is_registered` | `NODE_CLASS_MAPPINGS`에 `TagsExtractor`가 있는가 | 있다 |
| `test_the_node_runs_inside_an_event_loop` | 이미 도는 이벤트 루프 안에서 `execute`를 `await` | `1girl, solo, sitting, on chair`가 나온다 |
| `test_translate_reaches_the_same_tags` | "창가 의자에 앉아 있는 소녀, 노을", `translate=True` | `1girl`, `sitting`, `window`, `sunset`이 있다. `googletrans`가 없으면 건너뛴다 |
| `test_a_scene_maps_to_its_tags` | "a girl sitting on a chair by the window at sunset" | `sitting`, `on chair`, `window`, `sunset`이 모두 있다 |
| `test_inflections_reach_the_tag` | "she sits" | `sitting`이 있다 |
| `test_a_phrase_picks_the_whole_tag` | "her hair in a low ponytail" | `low ponytail`은 있고 `high ponytail`은 없다 |
| `test_a_negated_phrase_is_dropped` | "a girl without a hat" | `hat`이 없다 |
| `test_an_alias_reaches_its_tag` | "oppai" | `breasts`가 있다 |
| `test_only_real_tags_come_back` | 출력의 모든 태그가 덤프의 general 태그인가 | 모두 그렇다 |
| `test_the_subject_leads` | "a girl sitting on a chair by the window at sunset" | 앞 두 태그가 `1girl`, `solo`다 |
| `test_subject_off_keeps_the_scene_only` | 같은 문장, `subject=False` | `sitting`, `on chair`, `window`, `sunset`만 나온다 |
| `test_two_people_are_not_solo` | "a girl and a boy in a library" | `1girl`, `1boy`, `library`이고 `solo`가 없다 |
| `test_a_number_counts` | "two girls and 3 boys" | `2girls`, `3boys` |
| `test_a_person_noun_is_never_searched` | "a man is taking off her bra" | `1boy`가 있고 `male focus`가 없다 |
| `test_an_object_pronoun_is_another` | "a man is undressing her bra", "she is looking at him" | `1boy`, `undressing another`, `bra` / `looking at another` |
| `test_an_object_pronoun_takes_solo_away` | "a girl hugging him" | `1girl`, `hug`이고 `solo`가 없다 |
| `test_min_count_drops_a_rare_alias_hit` | "a man is taking off her bra", `min_count=500` | 기본값에서는 `takeoff`가 있고, 500에서는 `1boy`, `solo`, `bra`만 남는다 |
| `test_the_table_names_the_spelling_and_the_verdict` | 같은 문장, `min_count=500`의 `table` | `taking off → takeoff (take-off, 130, below min_count)` 행과 `(min_count: 500)` 꼬리가 있다 |
| `test_the_tags_come_back_grouped_by_kind` | "a girl in a library, smiling" | `1girl, solo, smile, library` |
| `test_a_blacklisted_tag_is_left_out` | "a girl in a school uniform", `blacklist="uniform"` | `school uniform`이 없다. blacklist 없이는 있다 |
| `test_max_tags_is_a_ceiling` | `max_tags=3` | 3개 이하다 |

실행 방법:

```bash
uv venv
uv pip install --python .venv/bin/python -r tests/requirements.txt
.venv/bin/python -m pytest -c tests/pytest.ini tests
```

## 테스트 결과
| | 수정 전 | 수정 후 |
|---|---|---|
| pytest | 1 failed, 2 passed, 7 errors (`TagsExtractor` 미등록, `tag_search` 없음) | 23 passed |
