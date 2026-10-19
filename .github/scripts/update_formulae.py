"""Update supported binary formulae from stable GitHub releases."""

import hashlib
import json
import os
import re
import urllib.request

from formula_config import ROOT, load_formulae



def parse_version(value):
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value):
        raise ValueError(f"Unsupported stable version: {value!r}")
    return tuple(map(int, value.split(".")))


def latest_release(repository):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "homebrew-tap-updater",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/latest",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def asset_sha256(asset):
    checksum = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(asset["browser_download_url"], timeout=60) as response:
        while chunk := response.read(1024 * 1024):
            checksum.update(chunk)
            size += len(chunk)
    if size == 0 or size != asset["size"]:
        raise ValueError(f"Download size mismatch: {asset['name']}")
    result = checksum.hexdigest()
    if asset.get("digest") and asset["digest"] != f"sha256:{result}":
        raise ValueError(f"SHA-256 mismatch: {asset['name']}")
    return result


def asset_urls(config, name, version):
    tag = config["tag"].format(version=version)
    base_url = f"https://github.com/{config['repository']}/releases/download/{tag}/"
    urls = {
        template: base_url + template.format(name=name, version=version, tag=tag)
        for template in config["assets"].values()
    }
    if len(set(urls.values())) != len(urls):
        raise ValueError(f"{name}: different asset templates produce the same URL")
    return urls


def update_formula(path, config):
    repository = config["repository"]
    original = path.read_text()
    versions = re.findall(r'^  version "([^"]+)"$', original, re.MULTILINE)
    if len(versions) != 1:
        raise ValueError(f"{path}: expected one explicit version")
    current = versions[0]
    release = latest_release(repository)
    if release["draft"] or release["prerelease"]:
        raise ValueError(f"{repository}: expected a published stable release")
    tag = release["tag_name"]
    tag_pattern = re.escape(config["tag"]).replace(
        re.escape("{version}"), r"(?P<version>[0-9]+\.[0-9]+\.[0-9]+)"
    )
    tag_match = re.fullmatch(tag_pattern, tag)
    if not tag_match:
        raise ValueError(f"{repository}: release tag does not match {config['tag']!r}")
    version = tag_match["version"]
    if parse_version(version) <= parse_version(current):
        print(f"{path.name}: {current} is up to date (latest: {tag})")
        return False

    name = path.stem
    if re.search(r"^ *resource\b", original, re.MULTILINE):
        raise ValueError(f"{path}: resource blocks are not supported for automatic updates")
    pattern = re.compile(
        r'^(?P<indent> +)url "(?P<url>[^"]+)"\n'
        r'(?P=indent)sha256 "[0-9a-f]{64}"$',
        re.MULTILINE,
    )
    matches = list(pattern.finditer(original))
    current_urls = asset_urls(config, name, current)
    next_urls = asset_urls(config, name, version)
    if len(matches) != len(current_urls) or {m["url"] for m in matches} != set(current_urls.values()):
        raise ValueError(f"{path}: unexpected platform URLs or checksum layout")

    replacements = {}
    for template, old_url in current_urls.items():
        url = next_urls[template]
        filename = url.rsplit("/", 1)[1]
        assets = [asset for asset in release["assets"] if asset["name"] == filename]
        if len(assets) != 1:
            raise ValueError(f"{repository}: expected one release asset {filename}")
        asset = assets[0]
        if asset["browser_download_url"] != url:
            raise ValueError(f"{repository}: unexpected download URL for {filename}")
        replacements[old_url] = (url, asset_sha256(asset))

    def replace_asset(match):
        url, checksum = replacements[match["url"]]
        indent = match["indent"]
        return f'{indent}url "{url}"\n{indent}sha256 "{checksum}"'

    updated = pattern.sub(replace_asset, original)
    updated = re.sub(
        r'^  version "[^"]+"$', f'  version "{version}"', updated, flags=re.MULTILINE
    )
    updated = re.sub(r"^  revision \d+\n", "", updated, flags=re.MULTILINE)
    path.write_text(updated)
    print(f"{path.name}: updated {current} -> {version}")
    return True


def update_formulae(root=ROOT):
    formulae = load_formulae(root)
    changed = []
    for relative, config in formulae.items():
        if config["update"] is None:
            print(f"{relative}: automatic updates disabled")
        elif update_formula(root / relative, config["update"]):
            changed.append(relative)
    return changed


if __name__ == "__main__":
    update_formulae()
