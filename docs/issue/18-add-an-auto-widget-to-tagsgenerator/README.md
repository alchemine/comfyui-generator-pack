# #18 Add an auto widget to TagsGenerator

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/18

## 이슈
- 카테고리 비율 없이 모든 태그에서 `n`개를 뽑으려면 여섯 `_share`를 하나씩 `-1`로 바꿔야 한다.
- 다시 비율을 쓰려면 원래 값을 하나씩 다시 입력해야 한다.

## 해결책
- `TagsGenerator`에 BOOLEAN 위젯 `auto`(기본값 `True`)를 `n` 바로 다음에 둔다.
- `auto`가 켜지면 `execute`가 카테고리 토글과 `_share`를 읽지 않고, 여섯 카테고리를 모두 `-1`(제한 없음)로 넘긴다. spec은 `characters, pose, expressions, body, clothes, background+objects+compositions`가 된다.
- `auto`가 꺼지면 지금과 같다.
- `IS_CHANGED`도 `execute`처럼 `auto`를 명시적 인자로 받는다. 원래 `**categories`로 들어가 캐시 키에 있었으므로 동작은 같다.
- `web/js/tags_generator_categories.js`는 `auto`가 켜져 있으면 카테고리 여섯 줄을 흐리게 그리고 클릭을 무시한다. 값은 바꾸지 않으므로 `auto`를 끄면 원래 설정으로 돌아간다. `drawToggle`은 호출한 쪽의 투명도를 기준으로 그려서 흐린 줄의 토글도 흐리게 보인다.
- README 두 개의 Tags Generator 위젯 표에 `auto`를 넣는다.
- 버전은 2.1.0이다.
- 같은 브랜치에서 `TagsGenerator` 기본값을 바꾼다: `n` 10, `auto` `True`, `momentum` 0.2(`DEFAULT_MOMENTUM`), `temperature` 1.3, `top_p` 1.0, `min_p` 0.0. `execute`와 `IS_CHANGED`의 인자 기본값도 같게 맞춘다.

## 테스트 계획
테스트는 `tests/issue/18-add-an-auto-widget-to-tagsgenerator/`에 있다. `suggest_tags`를 가로채 넘어간 `categories` spec을 본다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_auto_follows_n` | 입력 순서 | `auto`가 `n` 바로 다음, BOOLEAN, 기본값 `True` |
| `test_auto_on_lifts_every_cap` | `auto=True`, `pose_share=0.3`, `body=False` | spec이 여섯 카테고리 모두 제한 없음 |
| `test_auto_off_keeps_the_shares` | `auto=False`, `pose_share=0.3`, `body=False` | spec에 `pose:0.3`이 있고 `body`가 없다 |
| `test_auto_changes_the_cache_key` | `IS_CHANGED`에 `auto=True`/`False` | 두 값이 다르다 |

## 테스트 결과
| | 수정 전 | 수정 후 |
|---|---|---|
| `tests/issue/18-...` | 2 failed, 2 passed | 4 passed |
| 전체 pytest | | 67 passed |
