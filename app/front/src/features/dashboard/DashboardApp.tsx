import { DashboardPipelineApp } from "./DashboardPipelineApp.js";
import { legacyDashboardDataSource } from "./legacyDashboardDataSource.js";

export function DashboardApp() {
  return <DashboardPipelineApp dataSource={legacyDashboardDataSource} />;
}
