from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_package_json_declares_indexing_scripts() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    # PR-7 7.2: "indexing:run" (scripts/indexing/run_indexing.py) retired along
    # with the legacy IndexDocumentUseCase/LlamaIndexingPort write lane it drove
    # -- bundle-first indexing runs via POST /api/indexing/runs or a Release
    # build, never a standalone CLI. Asserting its *absence* keeps this test
    # from silently going stale if someone reintroduces a dead script pointer.
    assert "indexing:run" not in package["scripts"]
    assert package["scripts"]["indexing:validate"] == (
        "npm run python -- scripts/indexing/validate_index.py"
    )
    assert package["scripts"]["indexing:prepare-postgres"] == (
        "npm run python -- scripts/indexing/prepare_postgres_indexing.py"
    )
    assert package["scripts"]["test:indexing"] == (
        "npm run python -- -m pytest app/back/tests/indexing"
    )
