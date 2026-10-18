"""
### 이슈
1. 필터와 생성기의 판정이 달라, 필터가 생성기는 내지 않는 태그를 통과시키거나 반대로 막는다.
   * ASIS: `1girl, solo` + `kiss`를 필터가 통과시킨다.
   * TOBE: 생성기와 같이 막는다.

### 원인 분석
1. 필터에는 solo guard와 subject 조합 판정이 없고, 쌍 판정이 solo 게시물 통계만 쓴다.

### 솔루션
1. 필터가 생성기와 같은 세 판정(solo guard, subject 조합, 쌍 판정)을 쓴다.
   - `TagVeto.judge`가 `tag_solo.ruled_out`, `tag_subject`, `conflict`를 차례로 묻는다.
   - 기준 태그가 두 사람 이상이면 전체 게시물 통계로 판정한다.

### 테스트
1. 시나리오: 고정 태그와 생성 태그를 TagsConflictFilter에 넣는다.
2. 예제 1건: 고정 태그 하나와 그 뒤에 붙인 생성 태그 묶음. 10건.
    `1girl, solo` + `kiss, hug`               <- 한 사람 프롬프트의 두 사람 행동
    `1girl` + `penis, erection, smile`         <- 여자 한 명에 남성 신체
    `1girl, futanari` + `penis, smile`         <- futanari면 허용
    `1boy, solo` + `breasts, beard`            <- subject 조합
    `2girls, yuri` + `kiss, hug`               <- 두 사람이면 전체 게시물
    `2girls` + `blonde hair, red hair`         <- 두 사람이면 머리색 둘
    `1girl, bikini, beach, day` + `night, snow, swimsuit`
    `1girl, short hair` + `long hair`
    `1girl, solo` + `laughing, pout`           <- 표정은 solo 기준 그대로
    `1girl, turnaround, variations` + `hug`    <- 한 명용 태그는 solo 그대로
3. 비교: 남은 생성 태그가 기대와 같다.
"""

import pytest


@pytest.mark.parametrize(
    "fixed, generated, kept",
    [
        ("1girl, solo", "kiss, hug", []),
        ("1girl", "penis, erection, smile", ["smile"]),
        ("1girl, futanari", "penis, smile", ["penis", "smile"]),
        ("1boy, solo", "breasts, beard", ["beard"]),
        ("2girls, yuri", "kiss, hug", ["kiss", "hug"]),
        ("2girls", "blonde hair, red hair", ["blonde hair", "red hair"]),
        ("1girl, bikini, beach, day", "night, snow, swimsuit", ["swimsuit"]),
        ("1girl, short hair", "long hair", []),
        ("1girl, solo", "laughing, pout", ["laughing"]),
        ("1girl, turnaround, variations", "hug", []),
    ],
)
def test_filter(conflict_filter, fixed, generated, kept):
    given = {t.strip() for t in fixed.split(",")}
    assert [t for t in conflict_filter(fixed, generated) if t not in given] == kept
