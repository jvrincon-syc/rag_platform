import type {
  ActionResult,
  DashboardUploadForm,
  DecisionKind,
  LlamaControls,
  StatusPayload,
} from "./dashboardTypes.js";

// Data boundary consumed by DashboardPipelineApp. Legacy wires this to the
// global /api/* endpoints (legacyDashboardDataSource.ts); Platform wires it to
// /api/platform/* scoped by project_id (features/platform/legacyPipeline). The
// component tree and behavior stay identical across both — only this contract
// changes where data comes from.
export type DashboardPipelineDataSource = {
  loadStatus: () => Promise<StatusPayload>;
  uploadDocument: (form: DashboardUploadForm) => Promise<ActionResult>;
  submitReview: (options: {
    documentId: string;
    decision: DecisionKind;
    reason: string;
  }) => Promise<ActionResult>;
  runPipeline: (options: {
    controls: LlamaControls;
    ocrReviewThresholdPercent: number;
  }) => Promise<ActionResult>;
  saveSettings: (options: {
    ocrReviewThresholdPercent: number;
    llamaControls: LlamaControls;
  }) => Promise<{
    ok?: boolean;
    settings?: StatusPayload["settings"];
    status?: StatusPayload;
  }>;
  validateBundle: (options: { stagingRoot?: string | null }) => Promise<ActionResult>;
  promoteStaging: (options: { stagingRoot: string }) => Promise<ActionResult>;
};
