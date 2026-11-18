"""Container security policy for compose files (scripts/ci/check_compose_policy.py)."""

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.ci.check_compose_policy import check

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge mappings recursively, the override wins for everything else (enough for these files)."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _hardened(**extra: Any) -> dict[str, Any]:
    service = {"image": "app", "read_only": True, "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"]}
    service.update(extra)
    return service


def _config(**services: dict[str, Any]) -> dict[str, Any]:
    return {"services": services, "networks": {"backend": {"internal": True}, "edge": {}}}


def test_production_compose_complies() -> None:
    assert check(_load("compose.yaml")) == []


def test_development_compose_complies() -> None:
    config = _merge(_load("compose.yaml"), {k: v for k, v in _load("compose.override.yaml").items() if k == "services"})

    assert check(config) == []


def test_web_port_is_bound_to_localhost_by_default() -> None:
    ports = _load("compose.yaml")["services"]["web"]["ports"]

    assert check(_config(web=_hardened(ports=ports))) == []


def test_redis_is_only_on_the_internal_network() -> None:
    redis = _load("compose.yaml")["services"]["redis"]

    assert redis["networks"] == ["backend"]
    assert "ports" not in redis


def test_one_shot_services_have_no_network() -> None:
    services = _load("compose.yaml")["services"]

    assert services["migrate"]["network_mode"] == "none"
    assert services["seed"]["network_mode"] == "none"


def test_a_hardened_service_complies() -> None:
    assert check(_config(app=_hardened())) == []


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"privileged": True}, "privileged"),
        ({"cap_add": ["NET_ADMIN"]}, "cap_add"),
        ({"network_mode": "host"}, "network_mode: host"),
        ({"pid": "host"}, "pid: host"),
        ({"security_opt": ["no-new-privileges:true", "seccomp:unconfined"]}, "seccomp=unconfined"),
        ({"security_opt": ["no-new-privileges:true", "apparmor=unconfined"]}, "apparmor=unconfined"),
        ({"security_opt": ["no-new-privileges:true", "label:disable"]}, "label=disable"),
        ({"security_opt": []}, "no-new-privileges"),
        ({"cap_drop": ["NET_RAW"]}, "cap_drop"),
        ({"read_only": False}, "read_only"),
        ({"volumes": ["/var/run/docker.sock:/var/run/docker.sock"]}, "Docker socket"),
        ({"volumes": [{"type": "bind", "source": "/", "target": "/host"}]}, "host root"),
        ({"ports": ["8000:8000"]}, "all interfaces"),
        ({"ports": ["8000"]}, "all interfaces"),
        ({"ports": ["0.0.0.0:8000:8000"]}, "all interfaces"),
        ({"ports": [{"target": 8000, "published": "8000", "host_ip": ""}]}, "all interfaces"),
    ],
)
def test_violations_are_reported(extra: dict[str, Any], message: str) -> None:
    problems = check(_config(app=_hardened(**extra)))

    assert any(message in problem for problem in problems), problems


def test_writable_root_is_allowed_with_watch() -> None:
    assert check(_config(app=_hardened(read_only=False, develop={"watch": []}))) == []


@pytest.mark.parametrize(
    "ports",
    [["127.0.0.1:8000:8000"], ["${WEB_PUBLISH:-127.0.0.1:8000}:8000"], [{"target": 8000, "host_ip": "127.0.0.1"}]],
)
def test_ports_bound_to_one_interface_comply(ports: list[Any]) -> None:
    assert check(_config(app=_hardened(ports=ports))) == []


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"networks": ["backend", "edge"]}, "only on internal networks"),
        ({}, "only on internal networks"),
        ({"networks": ["backend"], "ports": ["127.0.0.1:6379:6379"]}, "must not publish ports"),
    ],
)
def test_datastores_stay_internal(extra: dict[str, Any], message: str) -> None:
    problems = check(_config(redis=_hardened(image="redis:7-alpine@sha256:abc", **extra)))

    assert any(message in problem for problem in problems), problems


def test_normalized_json_networks_are_understood() -> None:
    """`docker compose config --format json` writes networks as a mapping."""
    redis = _hardened(image="redis:7-alpine", networks={"backend": None})

    assert check(_config(redis=redis)) == []


def test_limits_use_service_level_keys() -> None:
    """Compose rejects `pids_limit` together with `deploy.resources.limits` ("can't set distinct values")."""
    for name, service in _load("compose.yaml")["services"].items():
        assert "deploy" not in service, name
        assert "pids_limit" in service, name
