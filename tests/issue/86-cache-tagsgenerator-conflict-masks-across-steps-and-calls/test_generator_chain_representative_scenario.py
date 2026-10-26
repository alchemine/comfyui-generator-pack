"""
### 이슈
1. 워크플로의 생성기 3개(기본, pose, expressions)가 프롬프트당 약 0.2 s를 쓴다.
   * ASIS: 세 생성기가 같은 프롬프트 태그의 충돌 마스크를 각각 계산한다.
   * TOBE: 첫 생성기가 계산한 마스크를 나머지가 재사용한다.

### 원인 분석
1. 마스크가 호출 사이에 남지 않아 생성기마다, 라운드마다 다시 계산한다.

### 솔루션
1. 전체 어휘 마스크를 TagVeto 안에 LRU로 보관한다.

### 테스트
1. 시나리오: 워크플로의 체인대로 생성기 3개를 차례로 실행한다(기본 n=5 → pose n=10 → expressions n=5, 앞 결과가 뒤의 입력).
2. 예제 5건 (모두 직접 추가): 프롬프트.
    1girl, solo, azusa (blue archive), white hair, halo, school uniform, looking at viewer, smile
    1girl, solo, office lady, desk, pencil skirt, glasses, sitting
    2girls, yuri, holding hands, park, sunset
    1girl, 1boy, hetero, hug, couch, living room
    1girl, solo, cat ears, tail, kimono, shrine, autumn leaves
3. 비교: 체인 전체의 쌍 테이블 조회 수가, 생성기마다 마스크를 비우고 돌린 조회 수의 절반 이하다. 흔들림은 체인을 3번 돌려 결과가 다른 횟수로 잰다(로그로 출력).
"""

import logging
import time

import pytest

from .conftest import PROMPTS

CHAIN = PROMPTS[:2] + PROMPTS[3:5] + PROMPTS[9:]

WIDGETS = (
    "subject",
    "body",
    "expressions",
    "pose",
    "clothes",
    "background",
    "bg_details",
    "framing",
)


def only(*names):
    return {w: w in names for w in WIDGETS}


def chain(generate, text, seed, between=lambda: None):
    base = generate(text, seed, n=5)
    text = f"{text}, {base}" if base else text
    between()
    pose = generate(text, seed, n=10, auto=False, **only("pose", "body"))
    text = f"{text}, {pose}" if pose else text
    between()
    expr = generate(text, seed, n=5, auto=False, **only("expressions", "framing"))
    return base, pose, expr


@pytest.mark.parametrize("text", CHAIN)
def test_later_generators_reuse_masks(generate, lift_calls, forget, text):
    cold = chain(generate, text, 1, between=forget)
    uncached = len(lift_calls)
    forget()
    warm = chain(generate, text, 1)
    cached = len(lift_calls) - uncached
    assert warm == cold
    assert cached <= uncached / 2, (uncached, cached)


@pytest.mark.parametrize("text", CHAIN)
def test_chain_is_stable(generate, text):
    runs, t = [], time.time()
    for _ in range(3):
        runs.append(chain(generate, text, 7))
    logging.getLogger(__name__).info(
        "%r: 3 chains in %.2fs, differing runs: %d",
        text[:40],
        time.time() - t,
        len(set(runs)) - 1,
    )
