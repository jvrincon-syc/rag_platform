import { Bot, GitBranch, History } from "lucide-react";
import type { Release, Variant } from "../platformTypes.js";

// Catálogo de variantes y releases del proyecto. La lectura primaria es la variante
// RAG; dentro de cada bloque se listan sus releases para que el operador vea qué
// pertenece a qué receta, qué ya está publicado y qué release está gestionando.
export function ReleaseHistory({
  releases,
  variants,
  selectedReleaseId,
  onSelect,
}: {
  releases: Release[];
  variants: Variant[];
  selectedReleaseId: string | null;
  onSelect: (releaseId: string) => void;
}) {
  if (releases.length === 0 && variants.length === 0) {
    return (
      <div className="ui-empty">
        <History size={22} />
        <span>
          Este proyecto aún no tiene variantes ni releases. Crea el primer draft cuando la
          variante RAG ya exista.
        </span>
      </div>
    );
  }

  const groups = buildReleaseGroups(variants, releases);

  return (
    <div className="release-history-groups" aria-label="Variantes y releases del proyecto">
      {groups.map((group) => {
        const publishedCount = group.releases.filter((release) => release.state === "published").length;
        return (
          <section
            key={group.variantId}
            className="release-variant-card"
            aria-label={`Releases de ${group.variantId}`}
          >
            <header className="release-variant-card-header">
              <div>
                <div className="release-variant-title">
                  <GitBranch size={16} aria-hidden="true" />
                  <strong>
                    <code>{group.variantId}</code>
                  </strong>
                </div>
                <p>
                  {group.isCatalogued
                    ? "Variante RAG disponible para crear y agrupar releases del proyecto."
                    : "Release heredada: esta variante no apareció en el catálogo actual."}
                </p>
              </div>
              <div className="release-variant-card-stats">
                <span className={`ui-status-chip ${toneForVariantState(group.variantState)}`}>
                  {group.variantState}
                </span>
                <span className="ui-meta">{group.releases.length} release(s)</span>
                <span className={publishedCount > 0 ? "ui-status-chip success" : "ui-status-chip neutral"}>
                  <Bot size={12} aria-hidden="true" />
                  {publishedCount} publicada(s)
                </span>
              </div>
            </header>

            {group.releases.length === 0 ? (
              <div className="ui-empty compact">
                <History size={18} />
                <span>Aún no hay releases para esta variante. Crea el primer draft.</span>
              </div>
            ) : (
              <ul className="ui-list release-variant-release-list">
                {group.releases.map((release) => {
                  const active = release.rag_release_id === selectedReleaseId;
                  return (
                    <li key={release.rag_release_id}>
                      <button
                        type="button"
                        className={active ? "ui-list-item active" : "ui-list-item"}
                        aria-current={active ? "true" : undefined}
                        onClick={() => onSelect(release.rag_release_id)}
                      >
                        <div className="release-entry-header">
                          <strong>
                            <code>{release.rag_release_id}</code>
                          </strong>
                          <div className="ui-status-row">
                            <span className={`ui-status-chip ${toneForReleaseState(release.state)}`}>
                              {release.state}
                            </span>
                            {release.state === "published" ? (
                              <span className="ui-status-chip success">
                                <Bot size={12} aria-hidden="true" />
                                Usable por API chatbot
                              </span>
                            ) : null}
                            {active ? <span className="ui-status-chip warning">En gestión</span> : null}
                          </div>
                        </div>
                        <div className="release-entry-meta">
                          <span>release #{release.release_number}</span>
                          <span>
                            snapshot <code>{release.corpus_snapshot_id}</code>
                          </span>
                          <span>
                            binding <code>{release.target_binding_key}</code>
                          </span>
                        </div>
                        <span>
                          manifest{" "}
                          <code title="Firma inmutable de procedencia">
                            {release.release_manifest_hash ?? "—"}
                          </code>
                        </span>
                        <small>{release.created_at}</small>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        );
      })}
    </div>
  );
}

type ReleaseGroup = {
  variantId: string;
  variantState: string;
  isCatalogued: boolean;
  releases: Release[];
};

function buildReleaseGroups(variants: Variant[], releases: Release[]): ReleaseGroup[] {
  const releasesByVariant = new Map<string, Release[]>();
  for (const release of releases) {
    const bucket = releasesByVariant.get(release.rag_variant_id);
    if (bucket) {
      bucket.push(release);
      continue;
    }
    releasesByVariant.set(release.rag_variant_id, [release]);
  }

  const groups: ReleaseGroup[] = variants.map((variant) => ({
    variantId: variant.rag_variant_id,
    variantState: variant.state,
    isCatalogued: true,
    releases: sortReleases(releasesByVariant.get(variant.rag_variant_id) ?? []),
  }));

  const knownVariantIds = new Set(variants.map((variant) => variant.rag_variant_id));
  for (const [variantId, groupedReleases] of releasesByVariant.entries()) {
    if (knownVariantIds.has(variantId)) {
      continue;
    }
    groups.push({
      variantId,
      variantState: "catalogo no cargado",
      isCatalogued: false,
      releases: sortReleases(groupedReleases),
    });
  }

  return groups;
}

function sortReleases(releases: Release[]): Release[] {
  return [...releases].sort((left, right) => {
    if (right.release_number !== left.release_number) {
      return right.release_number - left.release_number;
    }
    return right.created_at.localeCompare(left.created_at);
  });
}

function toneForReleaseState(state: string): "neutral" | "warning" | "success" | "danger" {
  if (state === "validated") {
    return "warning";
  }
  if (state === "published") {
    return "success";
  }
  return "neutral";
}

function toneForVariantState(state: string): "neutral" | "warning" | "success" {
  if (state === "buildable" || state === "active") {
    return "success";
  }
  if (state === "blocked") {
    return "warning";
  }
  return "neutral";
}
