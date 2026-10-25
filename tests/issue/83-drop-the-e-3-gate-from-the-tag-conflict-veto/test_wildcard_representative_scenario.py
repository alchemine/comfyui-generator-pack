"""
### 이슈
1. 프롬프트에 드문 태그가 있으면 한 카테고리의 후보가 거의 다 막혀 같은 태그만 나온다.
   * ASIS: `__mf__` 와일드카드로 표정을 생성하면 `closed eyes`, `grin`이 고정된다.
   * TOBE: 다른 표정도 나온다.

### 원인 분석
1. 쌍 판정의 "기대 동시 출현 E < 3이면 차단" 규칙에 `fatherly`(solo 0건), `affectionate`(1,514건) 같은 드문 참조 태그가 표정 354개 중 344~354개를 걸고, 생성기는 프롬프트 태그 전부를 참조로 쓴다.

### 솔루션
1. 두 노드의 쌍 판정을 lift < `lift_threshold`만으로 바꾼다(logic-v2.2.0).
   - 한 번도 같이 나오지 않은 쌍은 lift 0이라 그대로 막힌다.

### 테스트
1. 시나리오: TagsGenerator에 프롬프트를 넣고 expressions만 켜 n=3으로 seed 20개를 생성한다.
2. 예제 5건: 프롬프트마다 20 seed에서 나온 표정 종류 수.
    __mf__ (1girl, 1boy, hetero, affectionate, ..., fatherly)   <- 사용자 보고
    __nl__ (…, husband and wife)                                <- 직접 추가
    __fm__ (…, mature female, shota, motherly, mother and son) <- 직접 추가
    1girl, office lady, desk                                    <- 직접 추가
    1girl, solo, crying, rain                                   <- 직접 추가
3. 비교: 종류 수가 수정 전 값(5, 14, 12, 26, 13)보다 많다.
"""

import pytest

from .conftest import MF

HETERO = "1girl, 1boy, hetero, affectionate, deep skin, leaning on person"


@pytest.mark.parametrize(
    "text, at_least",
    [
        (MF, 10),  # 4.2.0: 5
        (HETERO + ", husband and wife", 16),  # 4.2.0: 14
        (
            HETERO + ", age difference, mature female, shota, motherly, mother and son",
            15,
        ),  # 4.2.0: 12
        ("1girl, office lady, desk", 30),  # 4.2.0: 26
        ("1girl, solo, crying, rain", 17),  # 4.2.0: 13
    ],
)
def test_more_expressions(expressions, text, at_least):
    assert len(expressions(text)) >= at_least
