from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.challenge.repository import ChallengeRepository
from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields


TRUSTED_FIELDS = {
    "expected_answer",
    "answer_aliases",
    "rubric",
    "solution_outline",
    "validator_config",
    "trusted_scoring",
    "answer_key",
    "scorer_results",
    "diagnosis_trace",
    "debug_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
    "include_debug",
}


def test_ode_network_mvp_loads_three_macro_nodes() -> None:
    repository = ChallengeRepository()

    graph = repository.load_graph("ode_network_mvp")
    questions = repository.load_question_bank("ode_network_mvp")

    assert [node.id for node in graph.macro_nodes] == [
        "ode_separable",
        "ode_first_order_linear",
        "ode_homogeneous_first_order",
    ]
    assert len(graph.micro_nodes) == 18
    assert len(graph.macro_challenges) == 3
    assert len(questions.questions) == 21
    assert graph.unlock_edges[0].from_macro_node_id == "ode_separable"


def test_challenge_api_is_only_registered_on_mixed_profile() -> None:
    mixed_paths = set(TestClient(create_app("mixed")).get("/openapi.json").json()["paths"])
    learner_paths = set(TestClient(create_app("learner")).get("/openapi.json").json()["paths"])
    internal_paths = set(TestClient(create_app("internal")).get("/openapi.json").json()["paths"])

    assert "/api/challenge/v1/health" in mixed_paths
    assert "/api/challenge/v1/health" not in learner_paths
    assert "/api/challenge/v1/health" not in internal_paths


def test_challenge_api_start_returns_public_current_question(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHALLENGE_SESSION_ROOT", str(tmp_path))
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/start",
        json={"chapter_id": "ode_network_mvp", "session_id": "web-start"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.concept"
    assert payload["challenge"]["current_question"]["question_id"] == "ode-net-sep-concept-001"
    assert "mastery" in payload["challenge"]
    assert_no_trusted_fields(payload)


def test_challenge_api_submit_advances_micro_node_without_trusted_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHALLENGE_SESSION_ROOT", str(tmp_path))
    client = TestClient(create_app("mixed"))
    client.post("/api/challenge/v1/start", json={"chapter_id": "ode_network_mvp", "session_id": "web-submit"})

    response = client.post(
        "/api/challenge/v1/submit",
        json={
            "session_id": "web-submit",
            "answer": "属于可分离，dy/dx=f(x)g(y)，其中 f(x)=x，g(y)=1+y^2。",
            "steps": ["识别 f(x)g(y)", "指出 f(x) 与 g(y)"],
            "explanation": "右端是只含 x 的因子乘只含 y 的因子。",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["challenge_attempt"]["pass_state"] == "pass"
    assert payload["challenge"]["micro_nodes"]["ode_separable.concept"]["status"] == "mastered"
    assert payload["challenge"]["mastery"]["ode_separable.concept"]["mastery_score"] >= 70
    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.trigger"
    assert "已点亮当前小节点" in payload["progression_advice"]
    assert "不建议推进" not in payload["progression_advice"]
    assert_no_trusted_fields(payload)


def test_challenge_api_rejects_invalid_session_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHALLENGE_SESSION_ROOT", str(tmp_path))
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/start",
        json={"chapter_id": "ode_network_mvp", "session_id": "../bad"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "challenge_request_schema_invalid"


def test_trainer_static_page_is_served_from_mixed_profile() -> None:
    response = TestClient(create_app("mixed")).get("/trainer/")

    assert response.status_code == 200
    assert "星系知识网训练舱" in response.text
    assert "/api/challenge/v1" not in response.text


def assert_no_trusted_fields(value) -> None:
    ensure_no_trusted_fields(value)
    text = json.dumps(value, ensure_ascii=False)
    for field in TRUSTED_FIELDS:
        assert field not in text


def test_space_trainer_static_page_and_assets_are_served_from_mixed_profile() -> None:
    client = TestClient(create_app("mixed"))

    page = client.get("/trainer/space/")
    script = client.get("/trainer/space/space.js")
    styles = client.get("/trainer/space/space.css")

    assert page.status_code == 200
    assert "3D Free Flight Knowledge Universe" in page.text
    assert 'href="/trainer/space/space.css?v=' in page.text
    assert 'type="module" src="/trainer/space/space.js?v=' in page.text
    assert script.status_code == 200
    assert "createKnowledgeUniverse" in script.text
    assert "startSpaceExperience" in script.text
    assert "showRenderFallback" in script.text
    assert styles.status_code == 200
    assert ".space-hud" in styles.text


def test_space_trainer_uses_cinematic_rendering_pipeline() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    assert "EffectComposer" in script.text
    assert "UnrealBloomPass" in script.text
    assert "createPlanetSurfaceMaps" in script.text
    assert "createAtmosphereShell" in script.text
    assert "createSoftParticleTexture" in script.text
    assert "addCinematicLighting" in script.text
    assert "ShaderMaterial" in script.text


def test_space_trainer_uses_realistic_deep_space_art_direction() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    assert "createWorldLockedSky" in script.text
    assert "createDeepSpaceTexture" in script.text
    assert "createSolarLightSource" in script.text
    assert "realisticBodyProfile" in script.text
    assert "preserveSurfaceColor" in script.text
    assert "addNebulaDust" not in script.text


def test_space_trainer_uses_world_locked_equirectangular_sky() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    panorama = client.get("/trainer/space/assets/milky-way-eso-6000.jpg")

    assert script.status_code == 200
    assert panorama.status_code == 200
    assert "createWorldLockedSky" in script.text
    assert "EquirectangularReflectionMapping" in script.text
    assert '"/trainer/space/assets/milky-way-eso-6000.jpg"' in script.text
    sky_source = script.text.split("function createWorldLockedSky", 1)[1].split("\n}", 1)[0]
    assert "THREE.Sprite" not in sky_source


def test_space_trainer_uses_high_resolution_observatory_panorama() -> None:
    client = TestClient(create_app("mixed"))

    page = client.get("/trainer/space/")
    script = client.get("/trainer/space/space.js")
    panorama = client.get("/trainer/space/assets/milky-way-eso-6000.jpg")

    assert page.status_code == 200
    assert "ESO/S. Brunier" in page.text
    assert script.status_code == 200
    assert '"/trainer/space/assets/milky-way-eso-6000.jpg"' in script.text
    assert "createRealisticStarField" not in script.text
    assert "scene.backgroundIntensity = 0.62" in script.text
    assert "scene.backgroundRotation.set(-0.16, 0, -0.14)" in script.text
    assert "0.32,\n    0.38,\n    0.72" in script.text
    assert panorama.status_code == 200
    assert len(panorama.content) > 6_000_000


def test_space_trainer_expands_to_large_dynamic_knowledge_galaxy() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    assert script.text.count("visualOnly: true") >= 4
    assert script.text.count("type:") >= 12
    assert "nodeTypeDefinitions" in script.text
    assert "updateCosmicMotion" in script.text
    assert "state.nebulaSprites" in script.text
    assert "currentCandidate" in script.text
    assert "macroRadii = [56, 48, 52, 42, 46, 50, 44, 40]" in script.text
    assert "interactionRadius: macroRadius * 3.6" in script.text


def test_space_trainer_uses_galactic_scale_and_physical_routes() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    assert "const GALAXY_SCALE = 1.95" in script.text
    assert "macroRadiusFor" in script.text
    assert "createPlanetSurfaceMaps" in script.text
    assert "colorMap" in script.text
    assert "roughnessMap" in script.text
    assert "emissiveMap" in script.text
    assert "const orbitBase = 120" in script.text
    assert "LineDashedMaterial" in script.text
    assert "computeLineDistances" in script.text
    assert "Math.min(0.42, 0.12 + opacity * 1.5)" in script.text
    assert "toneMapped: false" in script.text
    assert "pointLight.position.set(-definition.radius * 3" in script.text
    assert "if (index === 0) addRoute" in script.text
    assert "satellitePositions[index - 3]" not in script.text
    assert 'radius * (kind === "macro" ? 1.028 : 1.055)' in script.text
    assert "new THREE.AmbientLight(0x789cff, 0.22)" in script.text
    assert "new THREE.TubeGeometry" not in script.text
