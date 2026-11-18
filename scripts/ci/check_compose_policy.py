"""
Check a Compose configuration against the project's container security policy.

Reads the output of ``docker compose config --format json`` (what CI passes) or a
Compose YAML file (what the tests pass) and fails on anything that weakens the
isolation described in ADR 0004 and ADR 0005:

* privileged containers, added capabilities, host namespaces;
* disabled seccomp, AppArmor or SELinux profiles;
* the Docker socket or the host root mounted into a container;
* a service without ``cap_drop: [ALL]`` or ``no-new-privileges``;
* a writable root filesystem, except for development services with ``develop.watch``;
* a port published on all interfaces or without an explicit host IP;
* a datastore (redis, postgres, ...) with published ports or on a non-internal network.

Uses only the standard library for JSON input, so it runs before dependencies are
installed; PyYAML is imported only for YAML input.

Usage:
    docker compose config --format json | python scripts/ci/check_compose_policy.py -
    python scripts/ci/check_compose_policy.py compose.yaml

Exit codes:
    0: no violations.
    1: at least one violation (each is printed).
"""

import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

HOST_NAMESPACE_KEYS = ("network_mode", "pid", "ipc", "userns_mode", "uts", "cgroup")
UNCONFINED_OPTIONS = frozenset(
    {
        "seccomp=unconfined",
        "apparmor=unconfined",
        "systempaths=unconfined",
        "label=disable",
    }
)
DOCKER_SOCKETS = frozenset({"/var/run/docker.sock", "/run/docker.sock"})
DATASTORE_IMAGE = re.compile(r"^(?:[\w.-]+/)*(redis|valkey|postgres|postgis|mysql|mariadb|mongo|memcached)[:@]")
OPEN_HOST_IPS = frozenset({"", "0.0.0.0", "::", "[::]"})  # noqa: S104 - these are the values we reject
PORT_SPEC_WITH_IP_PARTS = 3  # IP:HOST_PORT:CONTAINER_PORT
INTERPOLATION = re.compile(r"\$\{(\w+)(?::?-([^}]*))?\}")


def _interpolate_defaults(value: str) -> str:
    """Replace ``${VAR:-default}`` with its default, as Compose does when VAR is unset."""
    return INTERPOLATION.sub(lambda match: match.group(2) or "", value)


def _normalize_option(option: str) -> str:
    """Compose accepts both ``seccomp:unconfined`` and ``seccomp=unconfined``."""
    return option.strip().replace(":", "=", 1).lower()


def _port_host_ip(port: Any) -> str:
    """
    Return the host IP an entry of ``ports`` is bound to, "" for all interfaces.

    Every entry is published: "8000" gets a random host port and "8000:8000" a fixed one,
    both on all interfaces. Only "IP:HOST_PORT:CONTAINER_PORT" restricts the interface.
    """
    if isinstance(port, dict):
        return str(port.get("host_ip") or "")
    parts = _interpolate_defaults(str(port)).split("/")[0].rsplit(":", 2)
    return parts[0] if len(parts) == PORT_SPEC_WITH_IP_PARTS else ""


def _volume_source(volume: Any) -> str:
    if isinstance(volume, dict):
        return str(volume.get("source") or "")
    return _interpolate_defaults(str(volume)).split(":")[0]


def _service_networks(service: dict[str, Any]) -> list[str]:
    networks = service.get("networks") or []
    if isinstance(networks, dict):
        return list(networks)
    return [str(name) for name in networks]


def _privileges(service: dict[str, Any]) -> Iterator[str]:
    if service.get("privileged"):
        yield "privileged: true is not allowed"
    if service.get("cap_add"):
        yield f"cap_add is not allowed: {service['cap_add']}"
    if "ALL" not in [str(cap).upper() for cap in service.get("cap_drop") or []]:
        yield "cap_drop must be [ALL]"
    for key in HOST_NAMESPACE_KEYS:
        if str(service.get(key, "")).lower() == "host":
            yield f"{key}: host shares a host namespace"


def _security_profiles(service: dict[str, Any]) -> Iterator[str]:
    options = {_normalize_option(str(option)) for option in service.get("security_opt") or []}
    for option in sorted(options & UNCONFINED_OPTIONS):
        yield f"security_opt {option} disables a kernel security profile"
    if not options & {"no-new-privileges=true", "no-new-privileges"}:
        yield "security_opt must contain no-new-privileges:true"


def _filesystem(service: dict[str, Any]) -> Iterator[str]:
    if not service.get("read_only") and not service.get("develop"):
        yield "read_only must be true (a writable root is allowed only for services with develop.watch)"
    for volume in service.get("volumes") or []:
        source = _volume_source(volume)
        if source in DOCKER_SOCKETS:
            yield f"mounts the Docker socket {source}"
        elif source == "/":
            yield "mounts the host root filesystem"


def _ports(service: dict[str, Any]) -> Iterator[str]:
    for port in service.get("ports") or []:
        if _port_host_ip(port) in OPEN_HOST_IPS:
            yield f"port {port} is published on all interfaces; bind it to 127.0.0.1 or set the host IP explicitly"


def _datastore(service: dict[str, Any], internal_networks: set[str]) -> Iterator[str]:
    if not DATASTORE_IMAGE.match(str(service.get("image", ""))):
        return
    if service.get("ports"):
        yield "a datastore must not publish ports"
    networks = _service_networks(service)
    if service.get("network_mode") != "none" and (not networks or not set(networks) <= internal_networks):
        yield f"a datastore must be only on internal networks, found {networks or ['default']}"


def _check_service(name: str, service: dict[str, Any], internal_networks: set[str]) -> list[str]:
    rules = (
        _privileges(service),
        _security_profiles(service),
        _filesystem(service),
        _ports(service),
        _datastore(service, internal_networks),
    )
    return [f"{name}: {problem}" for rule in rules for problem in rule]


def check(config: dict[str, Any]) -> list[str]:
    """Return the policy violations of a Compose configuration (empty if it complies)."""
    internal_networks = {
        name for name, network in (config.get("networks") or {}).items() if (network or {}).get("internal")
    }
    problems: list[str] = []
    for name, service in sorted((config.get("services") or {}).items()):
        problems.extend(_check_service(name, service or {}, internal_networks))
    return problems


def load(path: str) -> dict[str, Any]:
    """Load a Compose configuration from a JSON or YAML file, or JSON from stdin ("-")."""
    if path == "-":
        return json.load(sys.stdin)
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        import yaml  # noqa: PLC0415 - only needed for YAML input

        return yaml.safe_load(text)
    return json.loads(text)


def main(argv: list[str]) -> int:
    """Check every configuration given on the command line."""
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    failed = False
    for path in argv:
        problems = check(load(path))
        for problem in problems:
            print(f"policy violation ({path}): {problem}")
        failed = failed or bool(problems)
        if not problems:
            print(f"{path}: complies with the container security policy")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
