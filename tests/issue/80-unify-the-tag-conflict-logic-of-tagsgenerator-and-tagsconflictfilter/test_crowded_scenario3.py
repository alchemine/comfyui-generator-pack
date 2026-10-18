"""
### 이슈
1. solo 게시물에 거의 없는 태그가 기준이면, 그 태그와 어울리는 태그까지 막힌다.
   * ASIS: 필터가 `1girl, yuri`의 `kiss`, `hug`를 지우고, `multiple views` 프롬프트에서 background 태그가 생성되지 않는다.
   * TOBE: 남고, 생성된다.

### 원인 분석
1. solo 게시물에는 `yuri`가 28건, `multiple views`가 34건이라 기대 동시 출현 E가 3보다 작아 E < 3 규칙에 걸린다.

### 솔루션
1. 기준 태그가 두 사람 이상(`2girls`, `hug`, `yuri`, `multiple views` 등)이면 전체 게시물 통계로 판정하고, 한 사람 규칙(solo guard)을 쓰지 않는다.

### 테스트
1. 시나리오: 두 사람 이상이거나 여러 모습을 그린 프롬프트를 노드에 넣는다.
2. 예제 3건.
    필터 `1girl, yuri` + `kiss, hug` -> 둘 다 남음
    issue/27 프롬프트, background만 켜고 생성 -> 태그가 생김
    필터 `2girls` + `blonde hair, red hair` -> 둘 다 남음
3. 비교: 위 기대와 같다.
"""


def test_filter_keeps_kiss_and_hug_beside_yuri(conflict_filter):
    assert conflict_filter("1girl, yuri", "kiss, hug") == ["1girl", "yuri", "kiss", "hug"]


def test_character_sheet_draws_background(generate, sheet, background_only):
    assert generate(sheet, 0, n=10, auto=True, **background_only)


def test_filter_keeps_two_hair_colours_for_two_girls(conflict_filter):
    assert conflict_filter("2girls", "blonde hair, red hair") == ["2girls", "blonde hair", "red hair"]
