from __future__ import annotations

from types import SimpleNamespace

from app.back.tests.retrieval.test_hybrid_search_fusion import (
    _ReusableReleaseState,
    _build_release_with_optional_reuse,
    _should_preserve_live_state_after_test,
)


def test_should_preserve_live_state_after_success_by_default() -> None:
    assert _should_preserve_live_state_after_test(
        force_clean=False,
        run_completed=True,
    ) is True


def test_should_not_preserve_live_state_when_force_clean_is_enabled() -> None:
    assert _should_preserve_live_state_after_test(
        force_clean=True,
        run_completed=True,
    ) is False


def test_build_release_with_optional_reuse_skips_build_when_release_exists() -> None:
    class _UnexpectedBuildE2E:
        def _build_fresh_release_with_native_retry(self, **_kwargs):
            raise AssertionError("should not trigger a fresh build in reuse mode")

        def _create_fresh_snapshot_and_release(self, **_kwargs):
            raise AssertionError("should not create a new release in reuse mode")

        def _run_release_build_process(self, **_kwargs):
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
