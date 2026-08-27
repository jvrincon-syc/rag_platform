-- Operational review decisions for RAG Platform document revisions.
-- This table is append-only by decision_id. It does not mutate immutable source
-- revisions and it does not put blocked revisions inside corpus snapshots.

CREATE TABLE IF NOT EXISTS source_document_revision_review_decisions (
    decision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES rag_projects(project_id),
    source_document_revision_id TEXT NOT NULL,
    eligibility_decision TEXT NOT NULL
        CHECK (eligibility_decision IN (
            'approved_after_review',
            'operator_waiver',
            'blocked'
        )),
    reason TEXT NOT NULL CHECK (length(btrim(reason)) > 0),
    decided_by TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Existing source_document_revisions has a simple PK. This composite uniqueness
-- target lets the review-decision table enforce project ownership in the DB.
CREATE UNIQUE INDEX IF NOT EXISTS uq_source_document_revisions_project_revision
    ON source_document_revisions (project_id, source_document_revision_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'source_revision_review_decisions_project_revision_fk'
    ) THEN
        ALTER TABLE source_document_revision_review_decisions
            ADD CONSTRAINT source_revision_review_decisions_project_revision_fk
            FOREIGN KEY (project_id, source_document_revision_id)
            REFERENCES source_document_revisions (
                project_id,
                source_document_revision_id
            );
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_revision_review_decisions_latest
    ON source_document_revision_review_decisions (
        project_id,
        source_document_revision_id,
        decided_at DESC,
        decision_id DESC
    );
