"""Contract for local chatbot answer prompts used by the real retrieval sweep."""

from __future__ import annotations

from types import SimpleNamespace

from scripts.rag_platform.run_61_real_retrieval import _build_messages


def test_prompt_exige_referencia_directa_en_el_texto_de_respuesta() -> None:
    evidence = [
        SimpleNamespace(
            metadata={"source_relpath": "convivencia/manual_de_convivencia.md"},
            document_id="doc_manual",
            page_start=3,
            section_title="Derechos",
            text="Los trabajadores tienen derecho al respeto y trato digno.",
        )
    ]

    messages = _build_messages("Que derechos tengo?", evidence)

    system = messages[0]["content"]
    user = messages[1]["content"]
    assert "En el documento {documento} se estipula" in system
    assert "Direct reference phrase: En el documento manual_de_convivencia.md se estipula" in user
