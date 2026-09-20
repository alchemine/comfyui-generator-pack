# #7 Exclude docs and tests from the published package

이슈: https://github.com/alchemine/comfyui-generator-pack/issues/7

## 이슈
- `comfy node publish`는 git이 추적하는 파일을 모두 배포 zip에 넣는다. `docs/`와 `tests/`도 Registry로 올라간다.
- 사용자에게 필요 없는 개발용 파일이 패키지에 실린다.
- Registry의 자동 스캔은 이 파일들의 문자열도 검사한다. 문서나 테스트에 적힌 문자열만으로 버전이 Flagged가 될 수 있다.

## 해결책
- 리포 루트에 `.comfyignore`를 두고 `docs/`와 `tests/`를 적는다. 문법은 `.gitignore`와 같고, `comfy node publish`가 이 파일에 맞는 경로를 zip에서 뺀다.
- 리포에는 그대로 남는다. 빠지는 것은 배포 zip뿐이다.
- 버전을 1.0.2로 올린다.

## 테스트 계획
테스트는 `tests/issue/7-exclude-docs-and-tests-from-the-published-package/`에 있다. 리포를 임시 폴더에 복제하고 `uvx --from comfy-cli comfy node pack`으로 배포 zip을 실제로 만들어 그 안의 파일 이름을 본다. `uvx`가 없으면 건너뛴다.

| 테스트 | 무엇을 테스트하는가 | 기대 결과 |
|---|---|---|
| `test_the_archive_carries_no_docs_or_tests` | zip 안에 `docs/`나 `tests/`로 시작하는 항목이 있는가 | 하나도 없다 |
| `test_the_archive_still_carries_the_pack` | zip 안에 `__init__.py`, `pyproject.toml`, `nodes/tags.py`, `nodes/lib/tag_solo.py`이 있는가 | 모두 있다 |

실행 방법:

```bash
uv venv
uv pip install --python .venv/bin/python -r tests/requirements.txt
.venv/bin/python -m pytest -c tests/pytest.ini tests
```

## 테스트 결과
| | 수정 전 (`70dd177`) |
|---|---|
| 배포 zip | 파일 32개 가운데 `docs/` 2개, `tests/` 3개 |
| pytest | 1 failed, 1 passed |
