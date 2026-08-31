"""61 preguntas SST con RETRIEVAL REAL (release publicada) + generacion real Qwen.

Todo in-process en el venv SST (menos piezas fragiles que el cruce .NET/Redis, que
ya se valido aparte): por pregunta hace el retrieval release-scoped REAL contra la
release PUBLISHED `ragr_...` (BGE embed + pgvector + rerank BGE), arma el MISMO
prompt que EvidencePromptBuilder (.NET) con los chunks reales y sus nombres de
documento originales, y genera con llama-server (:8001, thinking off,
repeat_penalty 1.1, max 200) midiendo tiempos por etapa.

BGE se calienta con una query throwaway antes del loop cronometrado (si no, la
primera pagaria ~110s de cold-load).

Requiere: llama-server en :8001, Postgres con la release publicada, corpus
materializado, BGE cacheado.

Uso:
    C:/venvs/chatbot-sst/Scripts/python.exe scripts/rag_platform/run_61_real_retrieval.py [limit]
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "app" / "back" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "indexing"))

_PROJECT_ID = "proj_sst-general"
_VARIANT_ID = "ragv_local-bge"
_RELEASE_ID = "ragr_4ea80fc628ea4ab3"
_TOP_K = 4  # cap de evidencia al LLM (paridad con DefaultTopK/.NET MaxEvidenceItems)

_LLAMA_URL = "http://127.0.0.1:8001/v1/chat/completions"
_REPORT = str(_REPO_ROOT / "scripts" / "rag_platform" / "sweep_61_real_retrieval.txt")

# Mirror exacto de EvidencePromptBuilder.SystemPrompt (.NET) — mantener en sync.
_SYSTEM = (
    "You are a warm, clear SST documentary assistant. "
    "Answer ONLY from the supplied evidence. Do not invent, assume, or use outside knowledge. "
    "For specific questions about emails, names, dates, deadlines, locations, or phone numbers, "
    "give the exact data first instead of a general summary. "
    "If the evidence is insufficient, say so clearly. Use plain text only, answer in the user's "
    "language, and do not include a Fuentes/Sources section because the UI shows citations separately."
)

QUESTIONS = [
    "Que establece la politica de seguridad y salud en el trabajo?",
    "Cuales son los objetivos del SG-SST?",
    "Como identifica la empresa los peligros y valora los riesgos?",
    "Que programas conforman la planificacion del SG-SST?",
    "Como se gestionan los requisitos legales en SST?",
    "Que contempla la gestion del cambio en seguridad y salud?",
    "Como se prepara la empresa para emergencias?",
    "Que lineamientos aplican a proveedores y contratistas en SST?",
    "Como se hacen auditorias internas del SG-SST?",
    "Como se revisa el SG-SST por la alta direccion?",
    "Que fuentes se usan para identificar oportunidades de mejora continua?",
    "Como se gestionan las acciones correctivas y preventivas?",
    "Como se investigan incidentes accidentes y enfermedades laborales?",
    "Que debe comunicarse al COPASST sobre investigaciones de accidentes?",
    "Que responsabilidades tiene la ARL en seguridad y salud en el trabajo?",
    "Que responsabilidades de SST tiene la organizacion?",
    "Como funciona la induccion y capacitacion anual en SST?",
    "Cuales son las funciones del COPASST?",
    "Que funciones tiene el presidente del COPASST?",
    "Que funciones tiene la secretaria del COPASST?",
    "Como se puede comunicar un trabajador con el COPASST?",
    "Quienes son los miembros principales y suplentes del COPASST 2025 a 2027?",
    "Quien fue nombrado presidente y secretaria del COPASST?",
    "Que es el comite de convivencia laboral?",
    "Cuales son las funciones del comite de convivencia?",
    "Cual es el objetivo del reglamento del comite de convivencia?",
    "Como se conforma el comite de convivencia laboral?",
    "Como funcionan las reuniones del comite de convivencia?",
    "Que metodologia siguen las sesiones del comite de convivencia?",
    "Como se presentan quejas o denuncias de convivencia?",
    "A que correo se envian las quejas de convivencia laboral?",
    "Que derechos tienen los trabajadores en convivencia laboral?",
    "Que deberes de convivencia laboral deben cumplir los trabajadores?",
    "Que principios y valores orientan la convivencia laboral?",
    "En que consiste la politica de desconexion laboral?",
    "Que normas de convivencia deben cumplir los trabajadores?",
    "Que marco legal soporta el comite y la convivencia laboral?",
    "Que dice la politica de prevencion del acoso laboral?",
    "Que es la sala amiga de la familia lactante?",
    "Cuales son las ventajas de la sala amiga?",
    "Donde esta ubicada la sala amiga y quienes pueden usarla?",
    "Como solicito o pido vacaciones?",
    "Que tipos de faltas contempla el reglamento interno de trabajo?",
    "Que sanciones aplican por consumo de alcohol o sustancias psicoactivas?",
    "Que dice la politica de prevencion de alcohol y drogas?",
    "Cuando puede la empresa requerir pruebas de deteccion de consumo?",
    "En que consiste el programa o politica de pausas activas?",
    "Por que son importantes las pausas activas para la salud fisica?",
    "Como ayudan las pausas activas a la concentracion y al estres?",
    "Que recomendaciones de seguridad vial aparecen en el corpus?",
    "Que compromisos tiene el PESV o plan estrategico de seguridad vial?",
    "Que significa cero tolerancia frente a alcohol y sustancias en seguridad vial?",
    "Que documentos o reglas hablan de prevencion del acoso laboral?",
    "Cual es el objetivo general del manual de convivencia laboral?",
    "Cuales son los objetivos especificos del manual de convivencia?",
    "En cuanto tiempo debe el Comite de Convivencia dar tramite a una queja?",
    "Que ocurre si un integrante del Comite de Convivencia es parte de una queja o investigacion?",
    "Por que la seguridad vial es una responsabilidad compartida?",
    "Que programa incluye el PESV para proteger actores viales vulnerables?",
    "Que metodologia debe adoptar la empresa para mejorar continuamente la prevencion del riesgo vial?",
    "Que medidas preventivas y correctivas contempla el reglamento interno frente al acoso laboral y sexual?",
]


def _doc_name(evidence) -> str:
    """Nombre de documento original desde source_relpath (basename), fallback document_id."""

    relpath = (evidence.metadata or {}).get("source_relpath", "")
    if relpath:
        return relpath.rstrip("/").split("/")[-1]
    return evidence.document_id


def _build_messages(question: str, evidence) -> list[dict]:
    sb = [f"QUESTION:\n{question}\n\nEVIDENCE:\n"]
    for i, e in enumerate(evidence, 1):
        head = f"\n[SOURCE {i}] Document: {_doc_name(e)}"
        if e.page_start is not None:
            head += f" | Page: {e.page_start}"
        if e.section_title:
            head += f" | Section: {e.section_title}"
        sb.append(head + "\n" + (e.text or "") + "\n")
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": "".join(sb)},
    ]


def _generate(messages: list[dict], t0: float) -> tuple[str, float]:
    """Stream Qwen; devuelve (answer, ttft). Mismos params que el provider .NET."""

    payload = {
        "model": "qwen3-1.7b",
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0,
        "stream": True,
        "cache_prompt": False,
        "repeat_penalty": 1.1,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        _LLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    answer = []
    ttft = None
    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            try:
                delta = json.loads(data)["choices"][0]["delta"].get("content")
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
            if delta:
                if ttft is None:
                    ttft = time.perf_counter() - t0
                answer.append(delta)
    return "".join(answer), (ttft if ttft is not None else time.perf_counter() - t0)


def _strip_think(text: str) -> str:
    """Qwen IQ4_XS a veces emite </think> pese a thinking off; el formatter .NET lo quita."""

    import re

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return re.sub(r"</?think>", "", text).strip()


def pct(vals: list[float], p: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1))))]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(QUESTIONS)

    from prepare_postgres_indexing import build_dsn_from_env, load_env_file

    dsn = build_dsn_from_env(dict(load_env_file(_REPO_ROOT / "secrets.env")))
    os.environ["SST_POSTGRES_DSN"] = dsn
    os.environ["SST_PERSISTENCE_MODE"] = "postgres"
    os.environ["SST_FEATURE_RAG_PLATFORM_V1"] = "true"

    from api.dependencies import build_pipeline_services_from_env

    services = build_pipeline_services_from_env(
        chunks_root=_REPO_ROOT / "data" / "projects" / "sst-general" / "chunks",
        embeddings_root=_REPO_ROOT / "data" / "projects" / "sst-general" / "embeddings",
    )
    port = services.chatbot_dispatch_question._release_retrieval

    def retrieve(q: str):
        return port.search(
            project_id=_PROJECT_ID, rag_variant_id=_VARIANT_ID,
            rag_release_id=_RELEASE_ID, question=q, top_k=_TOP_K,
        ).evidence

    print("warming BGE (throwaway query) ...", flush=True)
    tw = time.perf_counter()
    retrieve("calentamiento del modelo de recuperacion")
    print(f"warm done in {time.perf_counter() - tw:.1f}s", flush=True)

    rows = []
    out = open(_REPORT, "w", encoding="utf-8")
    try:
        for i, q in enumerate(QUESTIONS[:limit], 1):
            t0 = time.perf_counter()
            evidence = retrieve(q)
            t_ret = time.perf_counter() - t0
            names = [_doc_name(e) for e in evidence]

            t_llm0 = time.perf_counter()
            answer, ttft = _generate(_build_messages(q, evidence), t_llm0)
            t_llm = time.perf_counter() - t_llm0
            answer = _strip_think(answer)
            e2e = time.perf_counter() - t0

            rows.append({"ret": t_ret, "llm": t_llm, "ttft": ttft, "e2e": e2e})
            block = (
                f"#{i:02d} [e2e={e2e:5.1f}s ret={t_ret:4.1f}s llm={t_llm:5.1f}s "
                f"ttft={ttft:4.1f}s chunks={len(evidence)}] {q}\n"
                f"   cites: {', '.join(names)}\n"
                f"   -> {answer}\n"
            )
            print(block, flush=True)
            out.write(block)
            out.flush()

        if rows:
            ret = [r["ret"] for r in rows]
            llm = [r["llm"] for r in rows]
            e2e = [r["e2e"] for r in rows]
            summary = (
                f"\n=== {len(rows)} questions, concurrency=1, REAL retrieval (release {_RELEASE_ID}) ===\n"
                f"RETRIEVAL P50={pct(ret,50):.1f}s P95={pct(ret,95):.1f}s max={max(ret):.1f}s\n"
                f"LLM       P50={pct(llm,50):.1f}s P95={pct(llm,95):.1f}s max={max(llm):.1f}s\n"
                f"E2E       P50={pct(e2e,50):.1f}s P95={pct(e2e,95):.1f}s max={max(e2e):.1f}s\n"
                f"TARGET: E2E < 25s hard. Retrieval and LLM are the two real cost centers.\n"
            )
            print(summary, flush=True)
            out.write(summary)
    finally:
        out.close()
        services.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
