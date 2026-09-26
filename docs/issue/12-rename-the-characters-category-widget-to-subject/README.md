# #12 Rename the characters category widget to subject

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/12

## 이슈
- `TagsGenerator`의 `characters` 위젯은 인원수, 관계, 인물 유형(`1girl`, `couple`, `family`, `bride`)을 다룬다.
- 이름이 Danbooru의 character 태그(`hatsune miku` 같은 고유 캐릭터 이름)와 같아서 캐릭터 이름을 뽑는 위젯으로 읽힌다.
- 캐릭터 이름을 뽑는 위젯을 따로 추가하려면 `characters`라는 이름이 비어 있어야 한다.
- `ClassifyTags`의 첫 출력도 `characters`라서 같은 오해가 생긴다.

## 해결책
- `CATEGORY_DEFAULTS`의 키를 `subject`로 바꾼다. 위젯은 `subject`, `subject_share`가 된다.
- `CATEGORY_GROUPS`에 `"subject": ("characters",)`를 넣어 내부 카테고리 `characters`로 잇는다. `background`가 세 카테고리를 묶는 것과 같은 경로다.
- `categories_v1.0.json`의 키, `CATEGORY_ORDER`, `tag_suggest.py`의 `characters` 판정은 내부 이름이라 그대로 둔다.
- `tag_guard.py`의 `BUCKETS` 첫 항목과 `bucket_of`의 반환값을 `subject`로 바꾼다. `ClassifyTags`의 첫 출력 이름이 `subject`가 된다. 출력 링크는 순서로 이어지므로 기존 워크플로의 연결은 끊기지 않는다.
- README 두 개와 예제 워크플로의 위젯 이름을 바꾼다.
- 기존 워크플로에 저장된 `characters`, `characters_share` 값은 읽히지 않고 기본값이 쓰인다. 배포 전인 2.0.0에 넣는다.

## 테스트 계획
테스트는 `tests/issue/12-rename-the-characters-category-widget-to-subject/`에 있다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_the_generator_offers_subject` | `TagsGenerator` 입력 이름 | `subject`, `subject_share`가 있고 `characters`, `characters_share`는 없다 |
| `test_subject_reaches_the_characters_category` | `_categories_spec({"subject_share": 0.4})` | spec에 `characters:0.4`가 있다 |
| `test_subject_off_drops_the_characters_category` | `_categories_spec({"subject": False})` | spec에 `characters`가 없다 |
| `test_classify_names_its_first_output_subject` | `ClassifyTags.RETURN_NAMES[0]` | `subject` |
| `test_classify_puts_the_subject_first` | `ClassifyTags.execute("1boy, serafuku, sitting")` | 첫 출력이 `1boy`다 |

## 테스트 결과
| | 수정 전 | 수정 후 |
|---|---|---|
| `tests/issue/12-...` | 4 failed, 1 passed | 5 passed |
| 전체 pytest | | 51 passed |
