# #21 Fix copyright stats missing aliased and emoticon tags

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/21

## 이슈
- `filter_copyright`를 켜도 `plugsuit (evangelion)`이 후보로 뽑힌다.
- `copyright_v1.npz`에서 이 태그의 통계가 모두 0이어서 기준을 넘지 못한다.
- 통계 스크립트(`playground/tag-conflict-filter/precompute_copyright.py`)는 어휘 이름에서 `_`를 공백으로 바꾼 뒤 덤프의 이름과 글자 그대로 맞춘다. 두 경우에 이름이 어긋난다.

| 경우 | 어휘 | 덤프 |
|---|---|---|
| Danbooru에서 개명된 태그 | `plugsuit_(evangelion)` | `plugsuit` |
| 이모티콘 | `=_=` → `= =` | `=_=` |

- 어휘 20811개 중 508개가 `n_posts` 0이다. 그중 99개(개명 83개, 이모티콘 16개)가 위 두 경우다.
- 나머지는 alias 표에 없는 개명(`black_shoes` → `black_footwear` 등)이라 이번 범위에 넣지 않는다.

## 해결책
- 통계 스크립트가 어휘 인덱스를 `tag_alias.expand_index`로 넓힌다.
- 모든 이름을 `_` 표기와 공백 표기 두 가지로 등록한다. 이모티콘인지 판단하지 않으므로 `u_u`, `x_x`처럼 알파벳이 든 이모티콘도 맞춰진다.
- `copyright_v1.npz`를 다시 만들어 데이터 릴리스 `data-v2.1.0`으로 올린다. 같은 파일의 내용만 바뀌므로 minor다.
- `tag_copyright.py`의 `_URL`과 `_SHA256`을 새 파일로 바꾼다.
- `playground/`는 저장소에 없으므로 스크립트 수정은 로컬에만 남는다.
- 버전은 2.2.0이다.

## 테스트 계획
테스트는 `tests/issue/21-fix-copyright-stats-missing-aliased-and-emoticon-tags/`에 있다. 로컬 `resources/copyright_v1.npz`를 읽는다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_aliased_tag_has_posts` | `plugsuit_(evangelion)`, `interface_headset_(evangelion)`, `trap` | `n_posts` > 0 |
| `test_emoticon_has_posts` | `^_^`, `=_=`, `0_0`, `u_u`, `x_x` | `n_posts` > 0 |
| `test_plugsuit_is_masked` | `Copyright` 마스크 | `plugsuit_(evangelion)`이 True |
| `test_code_pins_the_local_data` | 로컬 파일의 sha256 | `tag_copyright._SHA256`과 같다 |

## 테스트 결과
| | 수정 전 | 수정 후 |
|---|---|---|
| `tests/issue/21-...` | 9 failed, 1 passed | |
