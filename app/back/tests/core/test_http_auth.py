from __future__ import annotations

import hashlib
import json

from core.http_auth import AUTH_CREDENTIALS_JSON_KEY, ConfiguredBearerAuth


def test_register_principal_persists_salted_digest_and_authenticates_after_restart(
    tmp_path,
) -> None:
    registry_path = tmp_path / "gui_auth_registry.json"
    authenticator = ConfiguredBearerAuth({}, local_registry_path=registry_path)

    credential = authenticator.register_principal(
        principal_id="gui-op",
        project_scope=("proj_a",),
    )

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    stored = payload["credentials"][0]
    assert stored["principal_id"] == "gui-op"
    assert stored["project_scope"] == ["proj_a"]
    assert "token_digest" in stored
    assert "token_salt" in stored
    assert "token_sha256" not in stored

    restarted = ConfiguredBearerAuth({}, local_registry_path=registry_path)
    principal = restarted.authenticate(f"Bearer {credential.token}")

    assert principal.principal_id == "gui-op"
    assert principal.project_scope == ("proj_a",)


def test_authenticate_accepts_legacy_unsalted_registry_for_backward_compatibility(
    tmp_path,
) -> None:
    registry_path = tmp_path / "gui_auth_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "credentials": [
                    {
                        "principal_id": "legacy-op",
                        "token_sha256": hashlib.sha256(
                            "legacy-token".encode("utf-8")
                        ).hexdigest(),
                        "project_scope": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    authenticator = ConfiguredBearerAuth({}, local_registry_path=registry_path)
    principal = authenticator.authenticate("Bearer legacy-token")

    assert principal.principal_id == "legacy-op"
    assert principal.project_scope is None


def test_is_admin_solo_lo_otorga_una_credencial_estatica_configurada(tmp_path) -> None:
    """G3: solo credenciales estáticas (SST_HTTP_AUTH_CREDENTIALS_JSON) pueden

    ser admin; una credencial GUI registrada/local nunca lo es, aunque
    comparta el mismo registro (fail-closed por defecto).
    """

    registry_path = tmp_path / "gui_auth_registry.json"
    authenticator = ConfiguredBearerAuth(
        {
            AUTH_CREDENTIALS_JSON_KEY: json.dumps(
                [
                    {"principal_id": "admin-op", "token": "admin-token", "is_admin": True},
                    {"principal_id": "plain-op", "token": "plain-token"},
                ]
            )
        },
        local_registry_path=registry_path,
    )
    gui_credential = authenticator.register_principal(principal_id="gui-op", project_scope=None)

    admin_principal = authenticator.authenticate("Bearer admin-token")
    plain_principal = authenticator.authenticate("Bearer plain-token")
    gui_principal = authenticator.authenticate(f"Bearer {gui_credential.token}")

    assert admin_principal.is_admin is True
    assert plain_principal.is_admin is False
    assert gui_principal.is_admin is False
