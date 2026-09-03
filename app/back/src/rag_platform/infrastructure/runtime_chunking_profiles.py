"""Resolución fail-closed de una receta de chunking persistida a su runtime.

Una ``ChunkingProfile`` de plataforma persiste ``strategy`` + ``sanitized_config``
+ ``fingerprint``. El build de release necesita el ``RuntimeChunkingProfile``
concreto (política de tokens/overlap y ``include_section_context``) que esa receta
selecciona. Este resolver hace ese mapeo **sin degradar** recetas desconocidas a
v1: si la estrategia/configuración no está soportada, o si el fingerprint no
corresponde a la receta canónica, falla cerrado con
``UnsupportedRuntimeChunkingRecipe``.

Vive en infraestructura porque cruza dos dominios (``rag_platform`` y ``chunking``)
para traducir una receta persistida a un objeto de runtime; el dominio de
plataforma no conoce el runtime de chunking.
"""

from __future__ import annotations

from chunking.domain.errors import ChunkingProfileError
from chunking.domain.models import ChunkingProfile as RuntimeChunkingProfile
from rag_platform.domain.errors import UnsupportedRuntimeChunkingRecipe
from rag_platform.domain.models import (
    ChunkingProfile,
    compute_chunking_profile_fingerprint,
)

#: Estrategia de chunking con hiperparámetros LIBRES: en vez de mapear a un preset
#: fijo, construye el ``RuntimeChunkingProfile`` desde ``sanitized_config`` (tokens y
#: overlap). Los invariantes los valida el constructor del runtime; el guard de
#: fingerprint sigue vigente (config manipulada = fail-closed). Las claves ausentes
#: caen a los defaults de v1, así un config parcial sigue siendo coherente.
_CUSTOM_STRATEGY = "structural-custom"
_CUSTOM_DEFAULTS: dict[str, float] = {
    "child_min_tokens": 250,
    "child_target_tokens": 350,
    "child_max_tokens": 450,
    "overlap_ratio": 0.12,
    "overlap_min_tokens": 30,
    "overlap_max_tokens": 60,
}


class RuntimeChunkingProfileResolver:
    """Mapea una ``ChunkingProfile`` persistida a su ``RuntimeChunkingProfile``.

    v1 (``structural`` sin contexto de sección) y v2 (``local-structural-v2`` con
    ``include_section_context``) son las únicas recetas seleccionables. Cualquier
    otra combinación es fail-closed.
    """

    #: Recetas que resuelven a la política v1 (sin contexto de sección). Se
    #: aceptan los alias históricos de la estrategia para no romper perfiles ya
    #: persistidos, todos con ``include_section_context`` en falso.
    _V1_KEYS = frozenset(
        {
            ("structural", False),
            ("local-structural", False),
            ("local-structural-v1", False),
            ("local_structural_v1", False),
        }
    )
    #: Recetas que resuelven a la política v2 (contexto de sección habilitado).
    _V2_KEYS = frozenset(
        {
            ("local-structural-v2", True),
            ("local_structural_v2", True),
        }
    )

    def resolve(self, profile: ChunkingProfile) -> RuntimeChunkingProfile:
        """Resuelve el runtime de una receta persistida o falla cerrado.

        Args:
            profile: Perfil de chunking de plataforma persistido.

        Returns:
            El ``RuntimeChunkingProfile`` concreto que la receta selecciona.

        Raises:
            UnsupportedRuntimeChunkingRecipe: Si el fingerprint no corresponde a
                la receta canónica, o si la estrategia/configuración no está
                soportada por el runtime.
        """

        expected_fingerprint = compute_chunking_profile_fingerprint(
            strategy=profile.strategy,
            sanitized_config=profile.sanitized_config,
        )
        if profile.fingerprint != expected_fingerprint:
            raise UnsupportedRuntimeChunkingRecipe(
                f"chunking profile {profile.chunking_profile_id.value!r} fingerprint "
                "does not match its canonical recipe; refusing to run a tampered recipe"
            )

        key = (
            profile.strategy,
            bool(profile.sanitized_config.get("include_section_context")),
        )
        if key in self._V1_KEYS:
            return RuntimeChunkingProfile.local_structural_v1()
        if key in self._V2_KEYS:
            return RuntimeChunkingProfile.local_structural_v2()
        if profile.strategy == _CUSTOM_STRATEGY:
            return self._build_custom(profile)

        raise UnsupportedRuntimeChunkingRecipe(
            "unsupported runtime chunking recipe: "
            f"strategy={profile.strategy!r} "
            f"include_section_context={key[1]!r}"
        )

    def _build_custom(self, profile: ChunkingProfile) -> RuntimeChunkingProfile:
        """Construye un runtime param-driven desde ``sanitized_config``.

        El ``profile_id`` del runtime se deriva del ``chunking_profile_id`` de
        plataforma para que params distintos generen ids/fingerprints de chunk
        distintos (identidad de artefactos correcta, sin colisionar con v1/v2).
        """

        config = profile.sanitized_config

        def _int(key: str) -> int:
            return int(config.get(key, _CUSTOM_DEFAULTS[key]))

        try:
            return RuntimeChunkingProfile(
                profile_id=profile.chunking_profile_id.value,
                child_min_tokens=_int("child_min_tokens"),
                child_target_tokens=_int("child_target_tokens"),
                child_max_tokens=_int("child_max_tokens"),
                overlap_ratio=float(
                    config.get("overlap_ratio", _CUSTOM_DEFAULTS["overlap_ratio"])
                ),
                overlap_min_tokens=_int("overlap_min_tokens"),
                overlap_max_tokens=_int("overlap_max_tokens"),
                include_section_context=bool(config.get("include_section_context", False)),
            )
        except (ChunkingProfileError, ValueError, TypeError) as error:
            # Config con params incoherentes (p. ej. max < target) o no numéricos:
            # fail-closed, nunca degradar silenciosamente a v1.
            raise UnsupportedRuntimeChunkingRecipe(
                f"invalid custom chunking recipe for "
                f"{profile.chunking_profile_id.value!r}: {error}"
            ) from error
