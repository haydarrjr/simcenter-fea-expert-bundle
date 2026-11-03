"""Stage/enable the existing local FEA release without replacing other bundle state.

Backups are evidence only: never restore enabled-bundles.json wholesale.
Uses the documented Workspace bundle CLI for materialization and activation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enabled(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list) or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) or not isinstance(x.get("version"), str) for x in data):
        raise RuntimeError("Unexpected enabled-bundles.json structure")
    ids = [x["id"] for x in data]
    if len(set(ids)) != len(ids):
        raise RuntimeError("Duplicate enabled bundle IDs; reconcile before installing")
    return {x["id"]: x["version"] for x in data}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--productdata", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    args = parser.parse_args()
    target = args.productdata.resolve(strict=True)
    cli = args.cli.resolve(strict=True)
    manifest = tomllib.loads((ROOT / ".sim-ai-agents.toml").read_text(encoding="utf-8"))
    bundle_id, version = manifest["bundle"]["id"], manifest["bundle"]["version"]
    release = ROOT / "dist" / bundle_id / version
    archive, sidecar = release / "agents-artefact-windows.zip", release / ".sim-ai-agents.toml"
    if not archive.is_file() or sidecar.read_bytes() != (ROOT / ".sim-ai-agents.toml").read_bytes():
        raise RuntimeError("Release archive missing or sidecar differs")
    state = target / "enabled-bundles.json"
    before = enabled(state)
    backup = ROOT / ".work" / "install-backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(state, backup / state.name)
    destinations = [(archive, target / f"{bundle_id}-{version}.bundle"), (sidecar, target / f"{bundle_id}-{version}.toml")]
    for src, dst in destinations:
        if dst.exists():
            if not dst.is_file() or digest(src) != digest(dst):
                raise RuntimeError(f"Existing release differs; refusing overwrite: {dst}")
            shutil.copy2(dst, backup / dst.name)
    env = dict(os.environ, SC_AGENTS_PRODUCT_DATA=str(target))
    def call(*parts):
        result = subprocess.run([str(cli), *parts], env=env, text=True, capture_output=True)
        (backup / ("cli-" + "-".join(parts[:2]) + ".txt")).write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(result.stdout + "\n" + result.stderr)
        return result
    receipt = {"bundle_id": bundle_id, "version": version, "productdata": str(target), "backup": str(backup), "enabled_before": before, "archive_sha256": digest(archive), "native_execution": "NOT_RUN", "desktop_new_session": "NOT_RUN", "whole_state_restored": False}
    try:
        for src, dst in destinations:
            if not dst.exists():
                with dst.open("xb") as out, src.open("rb") as source:
                    shutil.copyfileobj(source, out)
        call("bundle", "enable", bundle_id, "--version", version)
        listing = json.loads(call("bundle", "list", "--json").stdout)
        after = enabled(state)
        unrelated_before = {k: v for k, v in before.items() if k != bundle_id}
        unrelated_after = {k: v for k, v in after.items() if k != bundle_id}
        if unrelated_before != unrelated_after:
            raise RuntimeError("Unrelated enabled state changed; manual reconciliation required, no wholesale restore attempted")
        if after.get(bundle_id) != version:
            raise RuntimeError("Target bundle is not enabled at requested version")
        group = next(g for g in listing["groups"] if g["key"] == bundle_id)
        if group["enabledVersionIds"] != [f"{bundle_id}-{version}"]:
            raise RuntimeError("CLI enabled version readback mismatch")
        expanded = target / f"{bundle_id}-{version}"
        if not (expanded / "recipes" / "fea-expert-agent.yaml").is_file():
            raise RuntimeError("Main recipe not materialized")
        materialized = json.loads((expanded / "mcps.json").read_text(encoding="utf-8"))
        configs = materialized.get("configs", [])
        expected_mcp_names = {m["name"] for m in manifest.get("mcps", [])}
        if {m["name"] for m in configs} != expected_mcp_names:
            raise RuntimeError("Materialized MCP name set differs")
        for m in configs:
            if not (target / m["cmd"]).is_file():
                raise RuntimeError("Materialized launcher missing")
        receipt.update(result="PASS", enabled_after=after, unrelated_enabled_preserved=True, installed_archive_sha256=digest(destinations[0][1]), expanded=str(expanded), skill_count=len(list((expanded / "skills").glob("*/SKILL.md"))), subrecipe_count=len(list((expanded / "recipes" / "subrecipes").glob("*.yaml"))), catalog_agent_count=len(list((expanded / "recipes").glob("*.yaml"))), mcp_names=sorted(expected_mcp_names), mcp_handshake="NOT_RUN")
    except Exception as exc:
        receipt.update(result="FAIL_REQUIRES_RECONCILIATION", error=str(exc))
        (backup / "installation.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        raise
    (backup / "installation.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
