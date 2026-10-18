"""
### 이슈
1. 생성기가 낸 태그를 같은 프롬프트로 필터에 넣으면 일부가 지워질 수 있다.
   * ASIS: 두 노드의 판정 규칙이 달라 결과가 엇갈린다.
   * TOBE: 생성 결과를 필터에 넣어도 아무것도 지워지지 않는다.

### 원인 분석
1. 생성기는 suggest 테이블 lift(E >= 15)와 포아송 검정을 더 쓰고, 필터는 solo guard와 subject 조합을 쓰지 않았다.

### 솔루션
1. 생성기의 추가 규칙 두 개를 지우고, 필터에 생성기의 나머지 판정을 넣어 판정을 하나로 맞춘다.

### 테스트
1. 시나리오: TagsGenerator 출력을 같은 프롬프트를 고정 태그로 TagsConflictFilter에 넣는다.
2. 예제 1건: 프롬프트 하나를 seed 3개로 생성. 10건.
    `1girl, solo` / `2girls, yuri` / `1girl, bikini, beach` / `1boy, 1girl, hetero` / (빈 프롬프트)
    `1girl, school uniform, classroom` / `1boy, solo, armor` / `multiple girls, onsen`
    `1girl, sleeping, bed` / `1girl, solo, night, city`
3. 비교: 필터가 지운 태그가 없다.
"""

import pytest

PROMPTS = [
    "1girl, solo",
    "2girls, yuri",
    "1girl, bikini, beach",
    "1boy, 1girl, hetero",
    "",
    "1girl, school uniform, classroom",
    "1boy, solo, armor",
    "multiple girls, onsen",
    "1girl, sleeping, bed",
    "1girl, solo, night, city",
]


@pytest.mark.parametrize("prompt", PROMPTS)
def test_filter_keeps_what_the_generator_drew(generate, conflict_filter, prompt):
    for seed in range(3):
        drawn = generate(prompt, seed)
        kept = set(conflict_filter(prompt, ", ".join(drawn)))
        assert [t for t in drawn if t not in kept] == [], seed
