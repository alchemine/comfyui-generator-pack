"""
### 이슈
1. 생성기 결과를 같은 프롬프트로 필터에 넣으면 아무것도 지워지지 않아야 한다(issue 80의 약속).
   * ASIS: 두 노드가 같은 판정을 쓴다.
   * TOBE: E < 3 규칙을 지운 뒤에도 같다.

### 원인 분석
1. 규칙을 한쪽 노드에서만 바꾸면 생성기가 낸 드문 쌍을 필터가 지운다.

### 솔루션
1. `TagVeto`의 규칙 하나를 두 노드가 그대로 쓰므로, 규칙 변경이 양쪽에 같이 적용된다.

### 테스트
1. 시나리오: TagsGenerator 출력을 같은 프롬프트를 고정 태그로 TagsConflictFilter에 넣는다.
2. 예제 1건: 프롬프트 6개를 seed 5개로 생성. 30건.
    __mf__ / __nl__ / __fm__ / 1girl, office lady, desk / 1girl, solo, crying, rain / 1girl, beach
3. 비교: 필터가 지운 태그가 없다.
"""

import pytest

from .conftest import MF

HETERO = "1girl, 1boy, hetero, affectionate, deep skin, leaning on person"
PROMPTS = [
    MF,
    HETERO + ", husband and wife",
    HETERO + ", age difference, mature female, shota, motherly, mother and son",
    "1girl, office lady, desk",
    "1girl, solo, crying, rain",
    "1girl, beach",
]


@pytest.mark.parametrize("text", PROMPTS)
def test_filter_keeps_what_the_generator_drew(generate_then_filter, text):
    for seed in range(5):
        assert generate_then_filter(text, seed) == [], seed
