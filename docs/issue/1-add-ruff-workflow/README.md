# #1 Add ruff workflow

## 이슈
- GitHub Actions에 ruff 검사가 없다.
- `pyproject.toml`에 의존성 선언이 남아 있다.

## 해결책
- `.github/workflows/ruff.yml`을 추가한다. `ruff check .`와 `ruff format --check .`를 실행한다.
- `pyproject.toml`에 `[tool.ruff]` 설정을 추가한다.
- `pyproject.toml`에서 `dependencies`를 지운다. 의존성은 `requirements.txt`에만 적는다.
- `ruff check --fix`로 쓰지 않는 import와 공백만 있는 빈 줄을 지운다. `ruff format`으로 13개 파일의 형식을 맞춘다.
- 버전을 1.0.1로 올린다.

## 테스트 계획
| 테스트 | 기대 결과 |
|---|---|
| `ruff check .` | `All checks passed!` |
| `ruff format --check .` | 다시 형식을 맞출 파일이 없다 |

## 테스트 결과
### 수정 전
```
nodes/tags.py:11:8: F401 [*] `numbers` imported but unused
nodes/tags.py:477:1: W293 [*] Blank line contains whitespace
nodes/tags.py:481:1: W293 [*] Blank line contains whitespace
nodes/tags.py:560:1: W293 [*] Blank line contains whitespace
nodes/tags.py:564:1: W293 [*] Blank line contains whitespace
Found 5 errors.
[*] 5 fixable with the `--fix` option.
Would reformat: nodes/lib/artifact.py
Would reformat: nodes/lib/tag_alias.py
Would reformat: nodes/lib/tag_avoid.py
Would reformat: nodes/lib/tag_category.py
Would reformat: nodes/lib/tag_copyright.py
Would reformat: nodes/lib/tag_data.py
Would reformat: nodes/lib/tag_guard.py
Would reformat: nodes/lib/tag_solo.py
Would reformat: nodes/lib/tag_subject.py
Would reformat: nodes/lib/tag_suggest.py
Would reformat: nodes/lib/tag_veto.py
Would reformat: nodes/lib/utils.py
Would reformat: nodes/tags.py
13 files would be reformatted, 6 files already formatted
```

### 수정 후
```
All checks passed!
19 files already formatted
```
