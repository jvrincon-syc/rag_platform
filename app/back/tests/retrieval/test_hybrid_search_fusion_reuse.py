from __future__ import annotations

from types import SimpleNamespace

from app.back.tests.retrieval.test_hybrid_search_fusion import (
    _ReusableReleaseState,
    _build_release_with_optional_reuse,
    _should_preserve_live_state_after_test,
)


def test_should_preserve_live_state_when_reuse_state_is_valid() -> None:
    assert _should_preserve_live_state_after_test(
        force_clean=False,
        reusable_state_is_valid=True,
    ) is True


def test_should_preserve_live_state_when_force_clean_is_enabled() -> None:
    assert _should_preserve_live_state_after_test(
        force_clean=True,
        reusable_state_is_valid=True,
    ) is True


def test_should_preserve_live_state_when_reuse_state_is_invalid() -> None:
    assert _should_preserve_live_state_after_test(
        force_clean=False,
        reusable_state_is_valid=False,
    ) is True


def test_build_release_with_optional_reuse_skips_build_when_release_exists() -> None:
    class _UnexpectedBuildE2E:
        def _build_fresh_release_with_native_retry(self, *_args, **_kwargs):
            raise AssertionError("should not trigger a fresh build in reuse mode")

        def _create_fresh_snapshot_and_release(self, *_args, **_kwargs):
            raise AssertionError("should not create a new release in reuse mode")

        def _run_release_build_process(self, *_args, **_kwargs):
            raise AssertionError("should not execute release build in reuse mode")

    reusable_release = _ReusableReleaseState(
        revisions=(("raw/doc.md", "rev-1"),),
        revision_relpaths=("raw/doc.md",),
        release_id="ragr_existing",
        corpus_snapshot_id="css_existing",
        build_attempt=7,
        built_stages=0,
        reused_stages=4,
    )
    progress = SimpleNamespace(detail=lambda *_args, **_kwargs: None)

    snapshot, release, report, build_attempt = _build_release_with_optional_reuse(
        _UnexpectedBuildE2E(),
        dsn="postgresql://unused",
        revisions=reusable_release.revisions,
        progress=progress,
        reusable_release=reusable_release,
    )

    assert snapshot.corpus_snapshot_id.value == "css_existing"
    assert release.rag_release_id.value == "ragr_existing"
    assert report["rag_release_id"] == "ragr_existing"
    assert report["built_stages"] == 0
    assert report["reused_stages"] == 4
    assert build_attempt == 7


def test_build_release_with_optional_reuse_runs_build_when_state_is_missing() -> None:
    expected = (
        SimpleNamespace(corpus_snapshot_id=SimpleNamespace(value="css_new")),
        SimpleNamespace(rag_release_id=SimpleNamespace(value="ragr_new")),
        {
            "rag_release_id": "ragr_new",
            "built_stages": 4,
            "reused_stages": 0,
        },
        1,
    )

    class _BuildE2E:
        def __init__(self) -> None:
            self.calls = 0

        def _build_fresh_release_with_native_retry(
            self,
            _dsn: str,
            *,
            revisions,
            progress,
        ):
            del revisions, progress
            self.calls += 1
            return expected

    e2e = _BuildE2E()

    result = _build_release_with_optional_reuse(
        e2e,
        dsn="postgresql://unused",
        revisions=(("raw/doc.md", "rev-1"),),
        progress=SimpleNamespace(detail=lambda *_args, **_kwargs: None),
        reusable_release=None,
    )

    assert result == expected
    assert e2e.calls == 1
