from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from pathlib import Path


SST_HYBRID_QUESTIONS: tuple[str, ...] = (
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
)

_QUERY_EMBEDDING_CACHE: dict[tuple[str, str, str], list[list[float]]] = {}


def load_sst_hybrid_questions() -> tuple[str, ...]:
    return SST_HYBRID_QUESTIONS


def sst_reusable_derived_state_exists(project_root: Path) -> bool:
    return _has_files(project_root / "chunks") and _has_files(
        project_root / "embeddings"
    )


def query_embedding_cache_path(
    project_root: Path,
    *,
    embedding_profile_id: str,
    questions: Sequence[str],
) -> Path:
    digest = _questions_digest(embedding_profile_id, questions)
    profile_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", embedding_profile_id).strip("_")
    return project_root / f".query_embedding_cache_{profile_slug}_{digest[:12]}.json"


def load_cached_query_embeddings(
    *,
    project_root: Path,
    embedding_profile_id: str,
    questions: Sequence[str],
) -> list[list[float]] | None:
    cache_key = _cache_key(project_root, embedding_profile_id, questions)
    cached = _QUERY_EMBEDDING_CACHE.get(cache_key)
    if cached is not None:
        return [list(vector) for vector in cached]

    cache_path = query_embedding_cache_path(
        project_root,
        embedding_profile_id=embedding_profile_id,
        questions=questions,
    )
    if not cache_path.is_file():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    if payload.get("embedding_profile_id") != embedding_profile_id:
        return None
    if tuple(payload.get("questions", [])) != tuple(questions):
        return None

    raw_vectors = payload.get("vectors")
    if not isinstance(raw_vectors, list) or len(raw_vectors) != len(questions):
        return None

    try:
        vectors = [
            [float(value) for value in vector]
            for vector in raw_vectors
            if isinstance(vector, list)
        ]
    except (TypeError, ValueError):
        return None

    if len(vectors) != len(questions):
        return None

    _QUERY_EMBEDDING_CACHE[cache_key] = [list(vector) for vector in vectors]
    return [list(vector) for vector in vectors]


def save_cached_query_embeddings(
    *,
    project_root: Path,
    embedding_profile_id: str,
    questions: Sequence[str],
    vectors: Sequence[Sequence[float]],
) -> Path:
    if len(vectors) != len(questions):
        raise ValueError(
            "cached query embeddings must align 1:1 with the SST question bank"
        )

    cache_path = query_embedding_cache_path(
        project_root,
        embedding_profile_id=embedding_profile_id,
        questions=questions,
    )
    normalized_vectors = [
        [float(value) for value in vector]
        for vector in vectors
    ]
    payload = {
        "embedding_profile_id": embedding_profile_id,
        "questions": list(questions),
        "questions_digest": _questions_digest(embedding_profile_id, questions),
        "vectors": normalized_vectors,
    }
    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    _QUERY_EMBEDDING_CACHE[_cache_key(project_root, embedding_profile_id, questions)] = [
        list(vector) for vector in normalized_vectors
    ]
    return cache_path


def _cache_key(
    project_root: Path,
    embedding_profile_id: str,
    questions: Sequence[str],
) -> tuple[str, str, str]:
    return (
        str(project_root.resolve()),
        embedding_profile_id,
        _questions_digest(embedding_profile_id, questions),
    )


def _questions_digest(
    embedding_profile_id: str,
    questions: Sequence[str],
) -> str:
    payload = json.dumps(
        {
            "embedding_profile_id": embedding_profile_id,
            "questions": list(questions),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _has_files(path: Path) -> bool:
    return path.is_dir() and any(child.is_file() for child in path.rglob("*"))
