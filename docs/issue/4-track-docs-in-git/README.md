# #4 Track docs in git

## 이슈
- `.gitignore`가 `docs/`를 통째로 무시한다.
- `docs/` 아래에 새로 만든 문서가 추적되지 않는다.

## 해결책
- `.gitignore`에서 `docs/`를 지운다.
- 로컬 전용 자료는 `playground/`에 둔다. `playground/`는 계속 무시한다.

## 테스트 계획
| 테스트 | 기대 결과 |
|---|---|
| `git check-ignore -v docs/x.md` | 아무것도 출력하지 않고 종료 코드 1로 끝난다 |

## 테스트 결과
### 수정 전
```
.gitignore:7:docs/	docs/x.md
```
종료 코드 0.

### 수정 후
출력 없음. 종료 코드 1.
