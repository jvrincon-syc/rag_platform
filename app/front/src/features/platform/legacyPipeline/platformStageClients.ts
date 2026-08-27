// Clientes de etapa (chunking / embedding-indexing-retrieval) project-aware
// para el pipeline Legacy montado bajo Platform. Regla dura (plan 2026-08-25,
// Task 6 Step 4): Platform NUNCA usa los endpoints globales `/api/*` como si
// fueran datos del proyecto. Solo consume los contratos `/api/platform/*`
// existentes; lo que no tiene endpoint por proyecto se devuelve como estado
// vacio/no-disponible EXPLICITO, mientras la MISMA pantalla Legacy sigue
// renderizando (sin pantallas de reemplazo).
//
// Contratos por proyecto disponibles hoy:
//  - `listChunkingProfiles(projectId)` -> perfiles de chunking (sin token params)
// El resto de etapas (runs de chunking/embedding/indexing, activation,
// retrieval) NO tiene endpoint por proyecto: se ejecutan dentro del build de una
// release (`RAG / Releases`). Aqui se devuelven como no disponibles.
import { listChunkingProfiles } from "../platformApi.js";
import type { ChunkingApiClient } from "../../chunking/chunkingApi.js";
import type { ChunkingProfile } from "../../chunking/chunkingTypes.js";
import type { EmbeddingIndexingApiClient } from "../../embeddingIndexing/useEmbeddingIndexingPipeline.js";
import { recordChunkingProfile, recordEmbeddingProfile } from "./platformRecipeDraft.js";

// Mensaje honesto y estable para acciones/lecturas sin contrato por proyecto.
// La UI Legacy lo surfacea como notice de error; nunca finge exito.
function unavailable(action: string): never {
  throw new Error(
    `No disponible en Platform: ${action}. Esta etapa se ejecuta dentro del build de una release ` +
      `(RAG / Releases); Platform no expone un endpoint por proyecto para ejecutarla aqui.`,
  );
}

// Pagina vacia estructural: `items: []` infiere `never[]`, asignable a cualquier
// `PaginatedResponse<T>`/`Chunking*Page`. Evita fabricar contenido de proyecto.
function emptyPage(pageSize = 100) {
  return { items: [], page: 1, pageSize, totalItems: 0, totalPages: 0 };
}

export function createPlatformChunkingApiClient(projectId: string): ChunkingApiClient {
  return {
    // Contrato REAL por proyecto. `ChunkingProfileReadSchema` no expone token
    // params: se devuelven `null` y la UI Legacy los pinta `N/D` (sin inventar).
    async loadProfiles(): Promise<ChunkingProfile[]> {
      const profiles = await listChunkingProfiles(projectId);
      return profiles.map((profile) => ({
        profileId: profile.chunking_profile_id,
        childMinTokens: null,
        childTargetTokens: null,
        childMaxTokens: null,
        overlapRatio: null,
        overlapMinTokens: null,
        overlapMaxTokens: null,
      }));
    },
    // Lanzar chunking no tiene endpoint por proyecto: se registra el perfil
    // elegido en la receta (lo consume el resolver de variante en RAG/Releases)
    // y se falla cerrado explicando donde corre realmente.
    async createRun(options) {
      recordChunkingProfile(projectId, options.request.profileId);
      return unavailable("ejecutar una corrida de chunking");
    },
    async loadRun() {
      return unavailable("consultar una corrida de chunking");
    },
    async loadRunDocuments() {
      return emptyPage(25);
    },
    // Sin corrida por proyecto no hay documentos ya chunkeados que listar.
    async loadStoredDocuments() {
      return emptyPage(25);
    },
    // Honesto: no hay reporte de validacion por proyecto (null = pendiente/ausente).
    async loadValidationOptional() {
      return null;
    },
    async loadParents() {
      return emptyPage(25);
    },
    async loadChildren() {
      return emptyPage(25);
    },
  };
}

export function createPlatformEmbeddingIndexingApiClient(
  projectId: string,
): EmbeddingIndexingApiClient {
  return {
    embedding: {
      // Platform no expone un read-model rico de perfiles de embedding por
      // proyecto (la configuracion solo trae id+enabled, insuficiente para el
      // contrato Legacy sin inventar). Catalogo vacio explicito.
      async loadProfiles() {
        return emptyPage();
      },
      async loadChunkBundles() {
        return emptyPage();
      },
      async loadChunkBundleSummary() {
        return unavailable("resumir un chunk bundle");
      },
      async createRun(request) {
        recordEmbeddingProfile(projectId, request.profileId);
        return unavailable("ejecutar una corrida de embedding");
      },
      async loadRun() {
        return unavailable("consultar una corrida de embedding");
      },
      async loadBundle() {
        return unavailable("inspeccionar un embedding bundle");
      },
      async loadBundleChunks() {
        return emptyPage();
      },
      async loadBundleValidation() {
        return unavailable("validar un embedding bundle");
      },
      async loadIndexingReadiness() {
        return unavailable("consultar el readiness de indexing");
      },
    },
    indexing: {
      async loadOverview() {
        return unavailable("consultar el overview de indexing");
      },
      async createRun() {
        return unavailable("ejecutar una corrida de indexing");
      },
      async loadRun() {
        return unavailable("consultar una corrida de indexing");
      },
      async loadRunDocuments() {
        return emptyPage();
      },
      async loadRunErrors() {
        return emptyPage();
      },
      async loadRetrievalReadiness() {
        return unavailable("consultar el readiness de retrieval");
      },
      async activateRun() {
        return unavailable("activar una corrida de indexing");
      },
    },
    retrieval: {
      async loadProfiles() {
        return emptyPage();
      },
      async loadStatus() {
        return unavailable("consultar el estado de un perfil de retrieval");
      },
      async validate() {
        return unavailable("validar un perfil de retrieval");
      },
      async search() {
        return unavailable("buscar evidencia con retrieval");
      },
    },
  };
}
