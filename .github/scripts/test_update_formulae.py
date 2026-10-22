import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import update_formulae as updater
from formula_config import load_formulae


PLATFORMS = ("darwin_arm64", "darwin_amd64", "linux_arm64", "linux_amd64")


class UpdateFormulaTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "mp3blstr.rb"
        self.config = {
            "repository": "mingcheng/mp3blstr",
            "tag": "v{version}",
            "assets": {
                platform: f"{{name}}_{{version}}_{platform}.tar.gz"
                for platform in PLATFORMS
            },
        }
        self.original = (
            'class Mp3blstr < Formula\n  version "1.0.0"\n  revision 1\n'
            + "".join(
                f'  url "https://github.com/mingcheng/mp3blstr/releases/download/'
                f'v1.0.0/mp3blstr_1.0.0_{platform}.tar.gz"\n'
                f'  sha256 "{"0" * 64}"\n'
                for platform in PLATFORMS
            )
            + '  depends_on "alsa-lib"\nend\n'
        )
        self.path.write_text(self.original)
        self.release = {
            "tag_name": "v1.1.0",
            "draft": False,
            "prerelease": False,
            "assets": [
                {
                    "name": f"mp3blstr_1.1.0_{platform}.tar.gz",
                    "browser_download_url": (
                        "https://github.com/mingcheng/mp3blstr/releases/download/"
                        f"v1.1.0/mp3blstr_1.1.0_{platform}.tar.gz"
                    ),
                }
                for platform in PLATFORMS
            ],
        }
        self.latest = patch.object(updater, "latest_release", return_value=self.release)
        self.latest.start()
        self.addCleanup(self.latest.stop)
        self.checksum = patch.object(
            updater, "asset_sha256", side_effect=["1" * 64, "2" * 64, "3" * 64, "4" * 64]
        )
        self.download = self.checksum.start()
        self.addCleanup(self.checksum.stop)

    def update(self):
        return updater.update_formula(self.path, self.config)

    def test_updates_every_platform_and_resets_revision(self):
        self.assertTrue(self.update())
        expected = self.original.replace("1.0.0", "1.1.0").replace("  revision 1\n", "")
        for number in range(1, 5):
            expected = expected.replace("0" * 64, str(number) * 64, 1)
        self.assertEqual(self.path.read_text(), expected)
        self.assertEqual(self.download.call_count, 4)
        self.assertFalse(self.update())
        self.assertEqual(self.download.call_count, 4)

    def test_equal_or_older_release_does_not_change_formula(self):
        for tag in ("v1.0.0", "v0.9.0"):
            with self.subTest(tag=tag):
                self.release["tag_name"] = tag
                self.assertFalse(self.update())
                self.assertEqual(self.path.read_text(), self.original)
        self.download.assert_not_called()

    def test_invalid_or_unstable_release_fails_without_writing(self):
        for changes in (
            {"draft": True},
            {"prerelease": True},
            {"tag_name": "v1.1.0-rc1"},
            {"tag_name": "1.1.0"},
            {"tag_name": "invalid"},
        ):
            with self.subTest(changes=changes):
                with patch.object(updater, "latest_release", return_value=self.release | changes):
                    with self.assertRaises(ValueError):
                        self.update()
                self.assertEqual(self.path.read_text(), self.original)
        self.download.assert_not_called()

    def test_missing_or_duplicate_asset_fails_without_writing(self):
        assets = self.release["assets"]
        for invalid in (assets[:-1], assets + [assets[0]]):
            with self.subTest(assets=invalid):
                self.download.side_effect = None
                self.download.return_value = "1" * 64
                self.release["assets"] = invalid
                with self.assertRaises(ValueError):
                    self.update()
                self.assertEqual(self.path.read_text(), self.original)

    def test_unexpected_asset_url_fails_without_writing(self):
        self.release["assets"][0]["browser_download_url"] = "https://example.com/archive"
        with self.assertRaisesRegex(ValueError, "unexpected download URL"):
            self.update()
        self.assertEqual(self.path.read_text(), self.original)
        self.download.assert_not_called()

    def test_changed_formula_layout_fails_without_writing(self):
        changed = self.original.replace("darwin_arm64", "unsupported")
        self.path.write_text(changed)
        with self.assertRaisesRegex(ValueError, "unexpected platform URLs"):
            self.update()
        self.assertEqual(self.path.read_text(), changed)
        self.download.assert_not_called()

    def test_duplicate_url_fails_without_writing(self):
        self.path.write_text(self.original + self.original.split("  revision 1\n")[1])
        original = self.path.read_text()
        with self.assertRaisesRegex(ValueError, "unexpected platform URLs"):
            self.update()
        self.assertEqual(self.path.read_text(), original)
        self.download.assert_not_called()

    def test_resource_block_fails_without_writing(self):
        original = self.original.replace("end\n", '  resource "extra" do\n  end\nend\n')
        self.path.write_text(original)
        with self.assertRaisesRegex(ValueError, "resource blocks"):
            self.update()
        self.assertEqual(self.path.read_text(), original)
        self.download.assert_not_called()

    def test_missing_or_multiple_versions_fail_without_writing(self):
        for version in ("", '  version "1.0.0"\n  version "1.0.0"\n'):
            with self.subTest(version=version):
                original = self.original.replace('  version "1.0.0"\n', version)
                self.path.write_text(original)
                with self.assertRaisesRegex(ValueError, "expected one explicit version"):
                    self.update()
                self.assertEqual(self.path.read_text(), original)
        self.download.assert_not_called()

    def test_download_failure_does_not_partially_update_formula(self):
        self.download.side_effect = ["1" * 64, OSError("download failed")]
        with self.assertRaisesRegex(OSError, "download failed"):
            self.update()
        self.assertEqual(self.path.read_text(), self.original)

    def test_numeric_version_comparison(self):
        self.assertGreater(updater.parse_version("1.10.0"), updater.parse_version("1.9.0"))

    def test_checked_in_formula_remains_compatible(self):
        for relative, entry in load_formulae().items():
            config = entry["update"]
            if config is None:
                continue
            with self.subTest(formula=relative):
                original = (updater.ROOT / relative).read_text()
                current = updater.re.search(
                    r'^  version "([^"]+)"$', original, updater.re.MULTILINE
                )[1]
                major, minor, patch_version = updater.parse_version(current)
                version = f"{major}.{minor}.{patch_version + 1}"
                tag = config["tag"].format(version=version)
                self.path = Path(self.directory.name) / Path(relative).name
                self.release["tag_name"] = tag
                self.release["assets"] = []
                for template in dict.fromkeys(config["assets"].values()):
                    name = template.format(name=self.path.stem, version=version, tag=tag)
                    self.release["assets"].append({
                        "name": name,
                        "browser_download_url": (
                            f"https://github.com/{config['repository']}/releases/download/{tag}/{name}"
                        ),
                    })
                self.download.side_effect = [
                    str(number) * 64 for number in range(1, len(self.release["assets"]) + 1)
                ]
                self.path.write_text(original)
                self.assertTrue(updater.update_formula(self.path, config))
                expected = updater.re.sub(
                    r"^  revision \d+\n", "", original.replace(current, version),
                    flags=updater.re.MULTILINE,
                )
                for number, checksum in enumerate(
                    dict.fromkeys(updater.re.findall(r'sha256 "([0-9a-f]{64})"', original)), 1
                ):
                    expected = expected.replace(checksum, str(number) * 64)
                self.assertEqual(self.path.read_text(), expected)


class MultipleFormulaTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / ".github").mkdir()
        self.config = {}
        self.releases = {}

    def add_package(self, relative, repository, tag_template, assets):
        config = {"repository": repository, "tag": tag_template, "assets": assets}
        self.config[relative] = {"platforms": list(assets), "update": config}
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        urls = []
        release_assets = []
        for template in dict.fromkeys(assets.values()):
            for version in ("1.0.0", "1.1.0"):
                tag = tag_template.format(version=version)
                filename = template.format(name=path.stem, version=version, tag=tag)
                url = f"https://github.com/{repository}/releases/download/{tag}/{filename}"
                if version == "1.0.0":
                    urls.append(f'  url "{url}"\n  sha256 "{"0" * 64}"\n')
                else:
                    release_assets.append({"name": filename, "browser_download_url": url})
        path.write_text('class Example < Formula\n  version "1.0.0"\n' + "".join(urls) + "end\n")
        self.releases[repository] = {
            "tag_name": tag_template.format(version="1.1.0"),
            "draft": False,
            "prerelease": False,
            "assets": release_assets,
        }
        return path

    def run_updates(self):
        (self.root / ".github/formulae.json").write_text(json.dumps(self.config))
        with (
            patch.object(updater, "latest_release", side_effect=self.releases.__getitem__) as latest,
            patch.object(updater, "asset_sha256", return_value="a" * 64) as download,
        ):
            changed = updater.update_formulae(self.root)
        return changed, latest, download

    def test_updates_different_packages_without_changing_updater(self):
        first = self.add_package(
            "Formula/first.rb", "vendor/other-project", "{version}",
            {"darwin_arm64": "OtherProject-{version}-mac-aarch64.zip"},
        )
        second = self.add_package(
            "Formula/tools/second.rb", "other/cli", "release-{version}",
            {
                "linux_arm64": "cli-{tag}-aarch64.tar.xz",
                "linux_amd64": "cli-{tag}-x86_64.tar.xz",
            },
        )
        changed, latest, download = self.run_updates()
        self.assertEqual(changed, ["Formula/first.rb", "Formula/tools/second.rb"])
        self.assertEqual(
            [call.args[0] for call in latest.call_args_list],
            ["vendor/other-project", "other/cli"],
        )
        self.assertEqual(download.call_count, 3)
        self.assertIn('/1.1.0/OtherProject-1.1.0-mac-aarch64.zip"', first.read_text())
        self.assertIn('/release-1.1.0/cli-release-1.1.0-x86_64.tar.xz"', second.read_text())
        for path in (first, second):
            self.assertIn('version "1.1.0"', path.read_text())
            self.assertNotIn("1.0.0", path.read_text())
            self.assertNotIn("0" * 64, path.read_text())

    def test_shared_asset_is_downloaded_once(self):
        self.add_package(
            "Formula/universal.rb", "vendor/universal", "v{version}",
            {
                "darwin_arm64": "{name}-{version}.zip",
                "darwin_amd64": "{name}-{version}.zip",
            },
        )
        changed, _, download = self.run_updates()
        self.assertEqual(changed, ["Formula/universal.rb"])
        download.assert_called_once()

    def test_colliding_templates_fail_without_writing(self):
        for fixed_version in ("1.0.0", "1.1.0"):
            with self.subTest(version=fixed_version):
                path = self.add_package(
                    "Formula/collision.rb", "vendor/collision", "v{version}",
                    {
                        "darwin_arm64": "app-{version}.zip",
                        "darwin_amd64": f"app-{fixed_version}.zip",
                    },
                )
                original = path.read_text()
                with self.assertRaisesRegex(ValueError, "same URL"):
                    self.run_updates()
                self.assertEqual(path.read_text(), original)

    def test_unconfigured_and_disabled_packages_are_not_updated(self):
        paths = [
            self.add_package(f"Formula/{name}.rb", f"vendor/{name}", "v{version}",
                             {"linux_amd64": "{name}.tar.gz"})
            for name in ("enabled", "disabled", "unconfigured")
        ]
        self.config["Formula/disabled.rb"]["update"] = None
        del self.config["Formula/unconfigured.rb"]
        originals = [path.read_text() for path in paths]
        changed, latest, _ = self.run_updates()
        self.assertEqual(changed, ["Formula/enabled.rb"])
        latest.assert_called_once_with("vendor/enabled")
        self.assertEqual(paths[1].read_text(), originals[1])
        self.assertEqual(paths[2].read_text(), originals[2])

    def test_invalid_configuration_stops_before_any_update(self):
        path = self.add_package(
            "Formula/first.rb", "vendor/first", "v{version}",
            {"linux_amd64": "{name}.zip"},
        )
        original = path.read_text()
        self.config["Formula/missing.rb"] = {}
        with patch.object(updater, "update_formula") as update:
            with self.assertRaisesRegex(ValueError, "do not exist"):
                self.run_updates()
        update.assert_not_called()
        self.assertEqual(path.read_text(), original)


class AssetChecksumTests(unittest.TestCase):
    def setUp(self):
        self.data = b"release archive"
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.asset = {
            "name": "archive.tar.gz",
            "browser_download_url": "https://github.com/example/archive.tar.gz",
            "size": len(self.data),
            "digest": f"sha256:{self.digest}",
        }

    def checksum(self):
        with patch.object(updater.urllib.request, "urlopen", return_value=io.BytesIO(self.data)):
            return updater.asset_sha256(self.asset)

    def test_hashes_download_and_verifies_digest(self):
        self.assertEqual(self.checksum(), self.digest)

    def test_hashes_download_when_api_digest_is_unavailable(self):
        self.asset["digest"] = None
        self.assertEqual(self.checksum(), self.digest)

    def test_rejects_digest_mismatch(self):
        self.asset["digest"] = f'sha256:{"0" * 64}'
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            self.checksum()

    def test_rejects_truncated_or_empty_download(self):
        for data in (b"partial", b""):
            with self.subTest(data=data):
                self.data = data
                with self.assertRaisesRegex(ValueError, "Download size mismatch"):
                    self.checksum()


if __name__ == "__main__":
    unittest.main()
