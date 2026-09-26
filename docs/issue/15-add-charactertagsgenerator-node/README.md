# #15 Add CharacterTagsGenerator node

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/15

## 이슈
- `TagsGenerator`는 general 태그만 뽑는다. 어휘에 character 태그가 없고, `filter_copyright`는 특정 캐릭터를 떠올리게 하는 general 태그도 후보에서 뺀다.
- 캐릭터 이름을 넣으려면 사용자가 직접 적어야 한다.

## 해결책
- `resources/characters_v1.txt`를 추가한다. 탭 구분이고 한 줄에 캐릭터 하나(`name`, `posts`, `first_year`, `sex`)다. 이름은 밑줄을 공백으로 쓴다.
  - `playground/tag-conflict-filter/precompute_characters.py`가 `ThetaCursed/danbooru-2026-clean-metadata`(9,228,854 게시물, 2005-05 ~ 2025-09)에서 만든다.
  - `posts`는 그 캐릭터 태그가 붙은 게시물 수, `first_year`는 가장 이른 게시물의 연도다.
  - `sex`는 `1girl`, `1boy`, `1other` 각각이 `solo`, 그 캐릭터와 함께 붙은 게시물 수 중 가장 큰 쪽이다. 가장 큰 값이 여럿이거나 모두 0이면 `other`다.
  - 게시물 100개 이상인 캐릭터만 넣는다. 16,943개, 약 570KB다.
- `CharacterTagsGenerator` 노드("Character Tags Generator")를 `nodes/tags.py`에 추가하고 `__init__.py`에 등록한다.

| 위젯 | 종류 | 기본값 | 동작 |
|---|---|---|---|
| `n` | INT | 1 | 뽑을 캐릭터 수 |
| `girl`, `boy`, `other` | BOOLEAN | `True`, `False`, `False` | 후보로 둘 성별. JS가 `sex` 한 줄 칩으로 그린다 |
| `subject` | BOOLEAN | `True` | 인물 수 태그를 앞에 붙인다 |
| `year_min`, `year_min_value` | BOOLEAN, INT | `False`, 2020 | 켜면 `first_year >= year_min_value`만 남긴다 |
| `year_max`, `year_max_value` | BOOLEAN, INT | `False`, 2025 | 켜면 `first_year <= year_max_value`만 남긴다 |
| `min_count` | INT | 500 | `posts >= min_count`만 남긴다 |
| `seed` | INT | 0 | 뽑기 재현 |

- 뽑기는 `posts`에 비례한 가중치로 중복 없이 한다. 후보가 `n`보다 적으면 후보 전부를 낸다.
- 인물 수 태그는 뽑힌 캐릭터의 성별을 센다. 성별마다 `1girl`, `2girls`, ..., `6+girls`(boy, other도 같다)를 쓰고, 한 성별이 2명 이상이면 `multiple girls`처럼 붙인다. 합쳐 1명이면 `solo`를 붙인다. 순서는 girl, boy, other다.
- 출력은 인물 수 태그와 캐릭터 이름을 쉼표로 이은 문자열 하나다.
- 이름의 괄호는 `TagsGenerator`처럼 `\(`, `\)`로 이스케이프한다. `astolfo (fate)`의 괄호가 가중치로 읽히지 않게 하기 위해서다.
- 데이터 파일은 다른 표처럼 릴리스 `data-v1.1.0`에서 `artifact.ensure`로 받고 sha256으로 고정한다. 파일을 못 받으면 빈 문자열을 낸다.
- `web/js/character_tags_generator.js`가 `girl`, `boy`, `other`를 한 줄 칩으로, `year_min`/`year_max`를 토글과 값 한 줄로 그린다. 원래 위젯은 숨기기만 하므로 저장과 백엔드 입력은 그대로다.
- 모든 성별이 꺼지면 후보가 없으므로 빈 문자열을 낸다.

## 테스트 계획
테스트는 `tests/issue/15-add-charactertagsgenerator-node/`에 있다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_the_node_is_registered` | `NODE_CLASS_MAPPINGS` | `CharacterTagsGenerator`가 있다 |
| `test_the_node_offers_its_widgets` | 입력 이름 | 위 표의 위젯이 모두 있다 |
| `test_the_data_file_labels_known_characters` | `characters_v1.txt` | `hatsune miku` girl 2007, `link` boy, `astolfo (fate)` boy |
| `test_n_characters_come_back` | `n=3`, `subject=False` | 파일에 있는 이름 3개 |
| `test_sex_filters_the_pool` | `girl=False, boy=True` | 모든 이름의 `sex`가 boy |
| `test_min_count_filters_the_pool` | `min_count=5000` | 모든 이름의 `posts >= 5000` |
| `test_year_limits_filter_the_pool` | `year_min` 2023, `year_max` 2024 켬 | 모든 이름의 `first_year`가 2023~2024 |
| `test_year_limits_off_are_ignored` | 토글은 끄고 값만 2030 | 이름이 나온다 |
| `test_subject_counts_one_girl` | `n=1`, girl만 | `1girl, solo, <이름>` |
| `test_subject_counts_mixed_sexes` | `n=2`, girl과 boy, 여러 seed | 성별 구성에 맞게 `2girls, multiple girls` / `1girl, 1boy` / `2boys, multiple boys` |
| `test_the_draw_follows_the_seed` | 같은 seed, 다른 seed | 같은 seed는 같은 결과, seed 0~9에서는 결과가 여럿 |
| `test_no_sex_selected_returns_empty` | 세 성별 모두 끔 | 빈 문자열 |

## 테스트 결과
| | 수정 전 | 수정 후 |
|---|---|---|
| `tests/issue/15-...` | 2 failed, 10 errors (노드와 데이터 파일 없음) | 12 passed |
| 전체 pytest | | 63 passed |
