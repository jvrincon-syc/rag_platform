import {
  loadDashboardStatus,
  promoteDashboardStaging,
  runDashboardPipeline,
  saveDashboardSettings,
  submitDashboardReview,
  uploadDashboardDocument,
  validateDashboardBundle,
} from "./dashboardApi.js";
import type { DashboardPipelineDataSource } from "./dashboardDataSource.js";

export const legacyDashboardDataSource: DashboardPipelineDataSource = {
  loadStatus: loadDashboardStatus,
  uploadDocument: uploadDashboardDocument,
  submitReview: submitDashboardReview,
  runPipeline: runDashboardPipeline,
  saveSettings: saveDashboardSettings,
  validateBundle: validateDashboardBundle,
  promoteStaging: promoteDashboardStaging,
};
