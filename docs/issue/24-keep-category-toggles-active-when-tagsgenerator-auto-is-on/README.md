# #24 Keep category toggles active when TagsGenerator auto is on

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/24

## 이슈
- `auto`가 켜지면 카테고리 여섯 줄이 모두 흐려지고 클릭되지 않는다.
- `execute`도 토글을 읽지 않고 여섯 카테고리를 모두 `-1`(제한 없음)로 넘긴다.
- 그래서 비율 없이 뽑으면서 특정 카테고리를 뺄 수 없다.

## 해결책
- `auto`가 켜지면 `execute`가 `_share`만 `-1`로 덮어쓰고, 카테고리 토글은 그대로 `_categories_spec`에 넘긴다.
- `web/js/tags_generator_categories.js`는 `auto`가 켜져 있어도 토글을 또렷하게 그리고 클릭을 받는다. `_share`(값, ◀ ▶)는 지금처럼 흐리게 그리고 클릭을 무시한다.
- `auto`의 tooltip과 README 두 개의 위젯 표에서 토글을 무시한다는 문구를 고친다.
- #18의 `test_auto_on_lifts_every_cap`은 `body=False`인데도 `body`가 spec에 있기를 기대하므로, 토글이 반영된 spec을 기대하도록 고친다.
- 버전은 2.3.0이다.

## 테스트 계획
테스트는 `tests/issue/24-keep-category-toggles-active-when-tagsgenerator-auto-is-on/`에 있다. `suggest_tags`를 가로채 넘어간 `categories` spec을 본다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_auto_drops_toggled_off_categories` | `auto=True`, `body=False` | spec에 `body`가 없고 나머지 다섯은 제한 없음 |
| `test_auto_ignores_the_shares` | `auto=True`, `pose_share=0.3` | spec의 `pose`에 비율이 없다 |

## 테스트 결과
| | 수정 전 | 수정 후 |
|---|---|---|
| `tests/issue/24-...` | 1 failed, 1 passed | 2 passed |
| 전체 pytest | | 67 passed |
