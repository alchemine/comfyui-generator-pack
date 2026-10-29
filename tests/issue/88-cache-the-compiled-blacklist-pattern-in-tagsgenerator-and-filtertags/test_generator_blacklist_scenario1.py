"""
### 이슈
1. 블랙리스트 540개를 넘긴 `TagsGenerator` 1회 실행이 30~46 ms다. 블랙리스트가 없으면 4~10 ms다.
   * ASIS: 실행마다 `blacklist_pattern`이 `wildcards.yaml`을 읽고 토큰 540개를 각각 컴파일한다.
   * TOBE: 같은 블랙리스트는 한 번만 계산하고, 결과 태그는 같다.

### 원인 분석
1. `blacklist_pattern`이 호출 사이에 결과를 남기지 않고, 실행 1회에 3~4번 호출된다.

### 솔루션
1. `blacklist_pattern`을 블랙리스트 문자열 기준으로 캐시한다.

### 테스트
1. 시나리오: 워크플로의 블랙리스트(540 토큰)로 생성기 1개(pose, expressions, n=10)를 프롬프트마다 실행한다.
2. 예제 10건 (2026-10-29 출력 이미지의 앞부분 태그, 직접 찾음): conftest.PROMPTS. seed만 바꿔 두 번 실행한다.
    ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, dutch angle, curtains, ocean, day
    ... (나머지 9건은 conftest.PROMPTS)
3. 비교: 두 번째 실행은 wildcards.yaml을 읽지 않는다. 같은 seed의 두 실행은 결과가 같다.
"""

import pytest

from .conftest import PROMPTS


@pytest.mark.parametrize("text", PROMPTS)
def test_second_run_skips_the_blacklist_rebuild(generate, yaml_loads, text):
    generate(text, 1, n=10, auto=False, lift_threshold=0.2, pose=True, expressions=True)
    reads = len(yaml_loads)
    generate(text, 2, n=10, auto=False, lift_threshold=0.2, pose=True, expressions=True)
    assert len(yaml_loads) == reads


@pytest.mark.parametrize("text", PROMPTS)
def test_same_seed_gives_same_tags(generate, text):
    first = generate(text, 7, n=10, auto=False, lift_threshold=0.2, pose=True, expressions=True)
    second = generate(text, 7, n=10, auto=False, lift_threshold=0.2, pose=True, expressions=True)
    assert first == second
