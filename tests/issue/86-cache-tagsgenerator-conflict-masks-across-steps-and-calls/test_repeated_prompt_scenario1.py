"""
### 이슈
1. 같은 프롬프트로 생성기를 다시 실행하면 프롬프트 태그의 충돌 마스크를 처음부터 다시 계산한다.
   * ASIS: 두 번째 실행도 첫 실행과 같은 수의 쌍 테이블 조회를 한다.
   * TOBE: 두 번째 실행은 새로 뽑힌 태그만 조회한다.

### 원인 분석
1. `conflict_mask`가 결과를 보관하지 않아, 실행과 라운드마다 같은 참조 태그를 다시 조회한다.

### 솔루션
1. `conflict_mask`의 전체 어휘 마스크를 `(ref, multi, lift_th)`로 캐시한다.

### 테스트
1. 시나리오: 워크플로처럼 같은 프롬프트로 seed만 바꿔 생성기를 두 번 실행한다.
2. 예제 10건: 프롬프트마다 seed 1, 2.
    1girl, solo, azusa (blue archive), white hair, halo, school uniform, looking at viewer, smile
    1girl, solo, office lady, desk, pencil skirt, glasses, sitting
    ...
3. 비교: 두 번째 실행의 쌍 테이블 조회 수가 첫 실행의 절반 이하이고, 같은 seed의 결과는 캐시 전후가 같다.
"""

import pytest

from .conftest import PROMPTS


@pytest.mark.parametrize("text", PROMPTS)
def test_second_run_reuses_the_prompt_masks(generate, lift_calls, text):
    generate(text, seed=1)
    first = len(lift_calls)
    generate(text, seed=2)
    second = len(lift_calls) - first
    assert second <= first / 2, (first, second)


@pytest.mark.parametrize("text", PROMPTS)
def test_same_seed_same_tags(generate, text):
    assert generate(text, seed=3) == generate(text, seed=3)
