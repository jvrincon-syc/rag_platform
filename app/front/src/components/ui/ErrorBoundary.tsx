import { Component, type ErrorInfo, type ReactNode } from "react";
import { StatePanel } from "./StatePanel.js";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  error: Error | null;
};

// Límite de errores de render compartido (PR-4 4.4): sin esto, cualquier
// excepción no capturada en un hijo deja la pantalla completamente en blanco
// (AGENTS_front §7/§9: nunca ocultar un fallo tras un éxito aparente ni una
// pantalla vacía sin explicación). Solo un componente de clase puede
// implementar `getDerivedStateFromError`/`componentDidCatch`; no hay
// equivalente de hooks.
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Fail-closed: se registra el fallo real, nunca se oculta ni se resume.
    console.error("Fallo de render capturado por ErrorBoundary:", error, info.componentStack);
  }

  private readonly reset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error) {
      return (
        <section className="panel">
          <StatePanel
            kind="error"
            message={`Ocurrió un error inesperado en la interfaz: ${this.state.error.message}`}
            onRetry={this.reset}
          />
        </section>
      );
    }
    return this.props.children;
  }
}
