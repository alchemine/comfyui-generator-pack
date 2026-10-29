"""
### 이슈
1. 워크플로의 생성기 3개가 프롬프트당 약 0.115 s를 쓴다(서버 표시 21/48/46 ms).
   * ASIS: 생성기마다, 그 안의 FilterTags마다 블랙리스트 540개를 다시 컴파일한다.
   * TOBE: 체인 전체에서 블랙리스트는 한 번만 컴파일된다.

### 원인 분석
1. `blacklist_pattern`이 결과를 남기지 않는다.

### 솔루션
1. `blacklist_pattern`을 캐시한다.

### 테스트
1. 시나리오: 워크플로 체인대로 생성기 3개를 차례로 실행한다(배경·구도 n=5 → 포즈·표정 n=10 → 몸·옷 n=10, 앞 결과가 뒤의 입력). 블랙리스트는 워크플로의 540 토큰.
2. 예제 5건 (직접 찾음): conftest.PROMPTS[:5].
3. 비교: 두 번째 체인은 wildcards.yaml을 한 번도 읽지 않는다. 흔들림은 체인을 3번 돌려 결과가 다른 횟수와 시간을 로그로 잰다.
"""

import logging
import time

import pytest

from .conftest import PROMPTS, chain

EXAMPLES = PROMPTS[:5]


@pytest.mark.parametrize("text", EXAMPLES)
def test_second_chain_skips_the_blacklist_rebuild(generate, yaml_loads, text):
    chain(generate, text, 1)
    reads = len(yaml_loads)
    chain(generate, text, 2)
    assert len(yaml_loads) == reads


@pytest.mark.parametrize("text", EXAMPLES)
def test_repeat_chain_three_times(generate, text):
    outs, times = [], []
    for _ in range(3):
        t0 = time.perf_counter()
        outs.append(chain(generate, text, 3))
        times.append(time.perf_counter() - t0)
    differing = sum(o != outs[0] for o in outs[1:])
    logging.getLogger(__name__).warning(
        "chain x3 | differing=%d | %.3fs %.3fs %.3fs | %s",
        differing,
        *times,
        text[-60:],
    )
