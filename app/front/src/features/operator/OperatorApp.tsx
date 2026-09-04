import { ErrorBoundary } from "../../components/ui/ErrorBoundary.js";
import { PlatformWorkspace } from "../platform/PlatformWorkspace.js";
import { OperatorAuthWorkspace } from "./components/OperatorAuthWorkspace.js";
import { OperatorSidebar } from "./components/OperatorSidebar.js";
import { useOperatorSession } from "./useOperatorSession.js";

// La superficie "legacy" global (DashboardApp) se retiró (PR-5 5.1): todo el
// flujo vive en Platform. `OperatorSurface` sigue siendo un tipo separado de
// `AppView` por si el rail vuelve a tener más de una entrada.
export function OperatorApp() {
  const operatorSession = useOperatorSession();

  if (operatorSession.state.status !== "authenticated") {
    return (
      <div className="operator-auth-shell">
        <OperatorAuthWorkspace
          state={operatorSession.state}
          onLogin={operatorSession.login}
          onRegister={operatorSession.register}
          onRetry={() => void operatorSession.refresh()}
        />
      </div>
    );
  }

  return (
    <div className="operator-shell">
      <OperatorSidebar
        activeSurface="platform"
        session={operatorSession.state.session}
        loggingOut={operatorSession.state.loggingOut}
        onLogout={() => void operatorSession.logout()}
      />
      <div className="operator-surface">
        <ErrorBoundary>
          <PlatformWorkspace />
        </ErrorBoundary>
      </div>
    </div>
  );
}
