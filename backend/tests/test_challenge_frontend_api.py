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
    assert "3D Knowledge Singularity Universe" in page.text
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
    renderer = client.get("/trainer/space/singularity-renderer.js")

    assert script.status_code == 200
    assert renderer.status_code == 200
    assert "EffectComposer" in script.text
    assert "UnrealBloomPass" in script.text
    assert "addCinematicLighting" in script.text
    assert "ShaderMaterial" in renderer.text
    assert "createPortalAperture" in renderer.text
    assert "createCoronaSprite" in renderer.text
    assert "qualityLevel" in renderer.text


def test_space_trainer_builds_high_fidelity_volumetric_portals() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    renderer = client.get("/trainer/space/singularity-renderer.js")
    filament_veil = client.get("/trainer/space/assets/portal-energy-veil.png")

    assert script.status_code == 200
    assert renderer.status_code == 200
    assert filament_veil.status_code == 200
    assert filament_veil.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert int.from_bytes(filament_veil.content[16:20], "big") >= 1_500
    assert int.from_bytes(filament_veil.content[20:24], "big") >= 1_000
    assert "DOMAIN_WARP_GLSL" in renderer.text
    assert "VOLUMETRIC_MANTLE_FRAGMENT_SHADER" in renderer.text
    assert "BALANCED_VOLUMETRIC_MANTLE_FRAGMENT_SHADER" in renderer.text
    assert "FILAMENT_VEIL_FRAGMENT_SHADER" in renderer.text
    assert "FUNNEL_VERTEX_SHADER" in renderer.text
    assert "createVolumetricMantle" in renderer.text
    assert "createFilamentVeil" in renderer.text
    assert "createEnergyFilaments" in renderer.text
    assert "createEnergyGlints" in renderer.text
    assert "addMeshes(group, arcs.meshes)" in renderer.text
    assert "group.add(...arcs.meshes)" not in renderer.text
    assert "sharedPortalTexture" in renderer.text
    assert "sharedPortalTexture" in script.text
    assert "polarNoise" in renderer.text
    assert "braidFrequency" in renderer.text
    assert "gl_PointSize = min" in renderer.text
    assert "clamp(core + horizontal" in renderer.text
    assert "domainWarp" in renderer.text
    assert "fbm" in renderer.text
    assert "highp float" in renderer.text


def test_space_portals_have_a_layered_traversable_interior() -> None:
    client = TestClient(create_app("mixed"))

    renderer = client.get("/trainer/space/singularity-renderer.js")

    assert renderer.status_code == 200
    assert "DEPTH_CHAMBER_FRAGMENT_SHADER" in renderer.text
    assert "BALANCED_DEPTH_CHAMBER_FRAGMENT_SHADER" in renderer.text
    assert "createPortalDepthChamber" in renderer.text
    assert "createTunnelRib" in renderer.text
    assert "mouthScale" in renderer.text
    assert "layerCount" in renderer.text
    assert "coreRadius" in renderer.text
    assert "new THREE.RingGeometry" in renderer.text


def test_space_graph_is_front_facing_and_orders_each_boss_last() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    graph_adapter = client.get("/trainer/space/cosmos-graph.js")
    renderer = client.get("/trainer/space/singularity-renderer.js")

    assert script.status_code == 200
    assert graph_adapter.status_code == 200
    assert renderer.status_code == 200
    assert "buildProgressionLayout" in graph_adapter.text
    assert "orderProgressionNodes" in graph_adapter.text
    assert "decisionRole" in graph_adapter.text
    assert "frontFrame" in graph_adapter.text
    assert "BOSS_RADIUS = 78" in graph_adapter.text
    assert "frameLearningPathFront" in script.text
    assert "PORTAL_APPROACH_DIRECTION" in script.text
    assert "Object.freeze([0, 0, 1])" in script.text
    assert "new THREE.Vector3(0.62, 0.24, 1)" not in script.text
    assert "approachDirection" not in renderer.text


def test_space_progression_edges_render_and_travel_as_rapid_transit_corridors() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    transit = client.get("/trainer/space/transit-route.js")

    assert script.status_code == 200
    assert transit.status_code == 200
    assert "buildRapidTransitControlPoints" in script.text
    assert "buildGuidedTransitWaypoints" in script.text
    assert "createRapidTransitCorridor" in script.text
    assert "new THREE.TubeGeometry" in script.text
    assert "viaTunnelPath: choice.transitPath" in script.text
    assert "tween.path.getPointAt" in script.text
    assert "navigationTargetId" in script.text
    assert "edge.decisionRole" in transit.text


def test_space_trainer_uses_realistic_deep_space_art_direction() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    assert "createWorldLockedSky" in script.text
    assert "createDeepSpaceTexture" in script.text
    assert "createSolarLightSource" in script.text
    assert "createKnowledgeSingularity" in script.text
    assert "createBossCataclysm" in script.text
    assert "createPlanetSurfaceMaps" not in script.text
    assert "realisticBodyProfile" not in script.text
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
    normalized_script = script.text.replace("\r\n", "\n")
    assert "0.32,\n    0.38,\n    0.72" in normalized_script
    assert panorama.status_code == 200
    assert len(panorama.content) > 6_000_000


def test_space_trainer_builds_the_universe_from_the_runtime_knowledge_graph() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    graph_adapter = client.get("/trainer/space/cosmos-graph.js")

    assert script.status_code == 200
    assert graph_adapter.status_code == 200
    assert 'from "./cosmos-graph.js?v=' in script.text
    assert "buildCosmosGraph" in script.text
    assert "challenge.network" in graph_adapter.text
    assert "network.typed_edges" in graph_adapter.text
    assert "challenge.logic_overlay" in graph_adapter.text
    assert "deriveProgressionEdges" not in graph_adapter.text
    assert "macroDefinitions" not in script.text
    assert "nodeTypeDefinitions" not in script.text
    assert "visualOnly" not in script.text
    assert "updateCosmicMotion" in script.text
    assert "currentCandidate" in script.text


def test_space_trainer_uses_knowledge_singularities_and_semantic_routes() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    renderer = client.get("/trainer/space/singularity-renderer.js")

    assert script.status_code == 200
    assert renderer.status_code == 200
    assert "createKnowledgeSingularity" in script.text
    assert "createAuxiliaryStar" in script.text
    assert "createRepairSingularity" in script.text
    assert "createBossCataclysm" in script.text
    assert "BOSS_SCALE = 3.8" in script.text
    assert "ShaderMaterial" in renderer.text
    assert "createPortalThroat" in renderer.text
    assert "createDistortedRim" in renderer.text
    assert "createInfallField" in renderer.text
    assert "createBossGasEnvelope" in renderer.text
    assert "createGasCloudHalo" in renderer.text
    assert "createAccretionDisk" not in renderer.text
    assert "new THREE.SphereGeometry" not in renderer.text
    assert "new THREE.IcosahedronGeometry" not in renderer.text
    assert "LineDashedMaterial" in script.text
    assert "computeLineDistances" in script.text
    assert "edge.edgeType" in script.text
    assert "isRapidTransitEdge(edge, start.toArray(), end.toArray())" in script.text


def test_space_trainer_has_enterable_focus_observatory() -> None:
    client = TestClient(create_app("mixed"))

    page = client.get("/trainer/space/")
    script = client.get("/trainer/space/space.js")
    styles = client.get("/trainer/space/space.css")

    assert page.status_code == 200
    assert script.status_code == 200
    assert styles.status_code == 200
    assert 'id="learningObservatory"' in page.text
    assert 'id="observatoryObject"' in page.text
    assert 'id="branchChoices"' in page.text
    assert "enterKnowledgeDomain" in script.text
    assert "exitKnowledgeDomain" in script.text
    assert 'experienceMode: "flight"' in script.text
    assert "deriveNextDestinations" in script.text
    assert ".learning-observatory" in styles.text
    assert ".observatory-object" in styles.text


def test_space_trainer_submits_the_backend_challenge_contract() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    submit_source = script.text.split("async function submitEncounter", 1)[1].split(
        "function renderCoachOutput", 1
    )[0]
    assert "answer_text" not in submit_source
    assert "explanation_text" not in submit_source
    assert "answer," in submit_source
    assert "steps: []," in submit_source
    assert "explanation:" in submit_source


def test_space_trainer_supports_touch_drag_camera_control() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")
    styles = client.get("/trainer/space/space.css")

    assert script.status_code == 200
    assert styles.status_code == 200
    assert "touchLook" in script.text
    assert 'event.pointerType === "mouse"' in script.text
    assert 'dom.canvas.addEventListener("pointermove"' in script.text
    assert "setPointerCapture" in script.text
    assert "touch-action: none" in styles.text


def test_manual_flight_input_cancels_autopilot_without_guided_force() -> None:
    client = TestClient(create_app("mixed"))

    script = client.get("/trainer/space/space.js")

    assert script.status_code == 200
    assert "cancelAutopilotForManualControl" in script.text
    assert "MOVEMENT_KEYS" in script.text
    assert "applyGuidedNavigation" not in script.text
    update_source = script.text.split("function updateFlight", 1)[1].split(
        "function updateNearestObject", 1
    )[0]
    assert "hasManualMovement" in update_source
    assert update_source.index("cancelAutopilotForManualControl") < update_source.index(
        "if (state.flightTween) return"
    )


def test_runtime_graph_exposes_visual_difficulty_to_the_portal_renderer() -> None:
    client = TestClient(create_app("mixed"))

    graph_adapter = client.get("/trainer/space/cosmos-graph.js")

    assert graph_adapter.status_code == 200
    assert "TYPE_DIFFICULTY" in graph_adapter.text
    assert "difficulty:" in graph_adapter.text
