"""Shared package configuration and Homebrew validation matrix."""

import json
from pathlib import Path
import re
from string import Formatter


ROOT = Path(__file__).resolve().parents[2]
TAP = "mingcheng/tap"
RUNNERS = {
    "darwin_arm64": "macos-15",
    "darwin_amd64": "macos-15-intel",
    "linux_arm64": "ubuntu-24.04-arm",
    "linux_amd64": "ubuntu-24.04",
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate configuration key: {key}")
        result[key] = value
    return result


def check_fields(value, allowed, required, context):
    if not isinstance(value, dict):
        raise ValueError(f"{context}: expected an object")
    unknown = value.keys() - allowed
    missing = required - value.keys()
    if unknown or missing:
        raise ValueError(
            f"{context}: unknown fields {sorted(unknown)}, missing fields {sorted(missing)}"
        )


def check_template(template, fields, context, require_version=False):
    if not isinstance(template, str) or not template:
        raise ValueError(f"{context}: expected a nonempty template")
    used = set()
    for _, field, spec, conversion in Formatter().parse(template):
        if field is not None:
            if field not in fields or spec or conversion:
                raise ValueError(f"{context}: unsupported template field {field!r}")
            used.add(field)
    if require_version and "version" not in used:
        raise ValueError(f"{context}: template must contain {{version}}")
    sample = template.format(name="example", version="1.2.3", tag="v1.2.3")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", sample):
        raise ValueError(f"{context}: expected a filename or tag without path separators")
    if require_version and template.count("{version}") != 1:
        raise ValueError(f"{context}: expected exactly one {{version}}")


def load_formulae(root=ROOT):
    config_path = root / ".github" / "formulae.json"
    configured = json.loads(config_path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(configured, dict):
        raise ValueError(f"{config_path}: expected an object keyed by Formula path")

    paths = sorted(path for path in (root / "Formula").rglob("*.rb") if path.is_file())
    if not paths:
        raise ValueError("No formulae found in Formula/")
    discovered = {path.relative_to(root).as_posix(): path for path in paths}
    unknown = configured.keys() - discovered.keys()
    if unknown:
        raise ValueError(f"Configured formulae do not exist: {sorted(unknown)}")

    result = {}
    names = set()
    for relative, path in discovered.items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9@+_.-]*", path.stem):
            raise ValueError(f"{relative}: unsupported formula name")
        if path.stem in names:
            raise ValueError(f"Duplicate formula name: {path.stem}")
        names.add(path.stem)
        entry = configured.get(relative, {})
        check_fields(entry, {"platforms", "update"}, set(), relative)
        platforms = entry.get("platforms", list(RUNNERS))
        if (
            not isinstance(platforms, list)
            or not platforms
            or any(not isinstance(platform, str) or platform not in RUNNERS
                   for platform in platforms)
            or len(set(platforms)) != len(platforms)
        ):
            raise ValueError(f"{relative}: expected a nonempty list of unique supported platforms")

        update = entry.get("update")
        if update is not None:
            context = f"{relative}: update"
            fields = {"repository", "tag", "assets"}
            check_fields(update, fields, fields, context)
            repository = update["repository"]
            if not isinstance(repository, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", repository
            ):
                raise ValueError(f"{context}: expected a GitHub owner/repository")
            check_template(update["tag"], {"version"}, context, require_version=True)
            assets = update["assets"]
            check_fields(assets, set(platforms), set(platforms), f"{context}: assets")
            for platform, template in assets.items():
                check_template(template, {"name", "version", "tag"}, f"{context}: {platform}")
        result[relative] = {"platforms": platforms, "update": update}
    return result


def build_matrix(formulae):
    return {
        "include": [
            {"formula": f"{TAP}/{Path(path).stem}", "os": RUNNERS[platform]}
            for path, config in formulae.items()
            for platform in config["platforms"]
        ]
    }


if __name__ == "__main__":
    print(json.dumps(build_matrix(load_formulae()), separators=(",", ":")))
