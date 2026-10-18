"""
### 이슈
1. 두 사람 프롬프트에서 어울리는 태그가 생성되지 않는다.
   * ASIS: `2girls, yuri`를 10번 생성해도 `kiss`가 한 번도 나오지 않는다.
   * TOBE: `kiss`가 나온다.
2. 필터가 생성기는 내지 않는 태그를 통과시킨다.
   * ASIS: `1girl, solo` + `kiss`, `1girl` + `penis`, `1boy, solo` + `breasts`, `1girl, solo` + `pout`(`laughing` 뒤)이 남는다.
   * TOBE: 지워진다.

### 원인 분석
1. 생성기는 solo 게시물 통계로 만든 suggest lift(E >= 15)와 포아송 검정으로 `kiss`를 `yuri` 옆에서 막는다.
2. 필터에는 solo guard와 subject 조합 판정이 없고, 기본 lift 기준이 0.1이라 `laughing`과 `pout`(lift 0.33)을 통과시킨다.

### 솔루션
1. 두 노드가 한 판정을 쓴다: solo guard, subject 조합, E < 3 또는 lift < 0.5.
2. 기준 태그가 두 사람 이상이면 전체 게시물 통계로 판정한다.

### 테스트
1. 시나리오: 사용자가 보고한 프롬프트와 필터가 놓치던 프롬프트를 노드에 그대로 넣는다.
2. 예제 5건.
    `2girls, yuri` 생성 10회 중 `kiss`가 나온다      <- 사용자 보고
    필터 `1girl, solo` + `kiss` -> 지워짐             <- 직접 추가
    필터 `1girl` + `penis, smile` -> `smile`만 남음   <- 직접 추가
    필터 `1boy, solo` + `breasts, beard` -> `beard`만 <- 직접 추가
    필터 `1girl, solo` + `laughing, pout` -> `pout` 지워짐 <- 직접 추가
3. 비교: 위 기대와 같다.
"""


def test_yuri_draws_kiss(generate):
    assert any("kiss" in generate("2girls, yuri", seed) for seed in range(10))


def test_filter_drops_kiss_from_a_solo_prompt(conflict_filter):
    assert conflict_filter("1girl, solo", "kiss") == ["1girl", "solo"]


def test_filter_drops_male_anatomy_from_one_girl(conflict_filter):
    assert conflict_filter("1girl", "penis, smile") == ["1girl", "smile"]


def test_filter_drops_what_two_subject_tags_rule_out(conflict_filter):
    assert conflict_filter("1boy, solo", "breasts, beard") == ["1boy", "solo", "beard"]


def test_filter_drops_pout_after_laughing(conflict_filter):
    assert conflict_filter("1girl, solo", "laughing, pout") == ["1girl", "solo", "laughing"]
