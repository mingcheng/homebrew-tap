import copy
import json
from pathlib import Path
import tempfile
import unittest

from formula_config import build_matrix, load_formulae


class FormulaConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / ".github").mkdir()
        self.config_path = self.root / ".github/formulae.json"
        self.add_formula("Formula/example.rb")
        self.entry = {
            "platforms": ["darwin_arm64"],
            "update": {
                "repository": "vendor/project",
                "tag": "v{version}",
                "assets": {"darwin_arm64": "app-{version}.zip"},
            },
        }

    def add_formula(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def load(self, config):
        self.config_path.write_text(json.dumps(config))
        return load_formulae(self.root)

    def test_unconfigured_formula_gets_all_runners_without_updates(self):
        formulae = self.load({})
        self.assertIsNone(formulae["Formula/example.rb"]["update"])
        self.assertEqual(build_matrix(formulae), {
            "include": [
                {"formula": "mingcheng/tap/example", "os": runner}
                for runner in ("macos-15", "macos-15-intel", "ubuntu-24.04-arm", "ubuntu-24.04")
            ]
        })

    def test_matrix_respects_platforms_and_discovers_nested_unconfigured_formula(self):
        self.add_formula("Formula/tools/extra.rb")
        formulae = self.load({"Formula/example.rb": self.entry})
        self.assertEqual(build_matrix(formulae), {
            "include": [
                {"formula": "mingcheng/tap/example", "os": "macos-15"},
                {"formula": "mingcheng/tap/extra", "os": "macos-15"},
                {"formula": "mingcheng/tap/extra", "os": "macos-15-intel"},
                {"formula": "mingcheng/tap/extra", "os": "ubuntu-24.04-arm"},
                {"formula": "mingcheng/tap/extra", "os": "ubuntu-24.04"},
            ]
        })

    def test_platform_only_and_explicitly_disabled_entries(self):
        for extra in ({}, {"update": None}):
            with self.subTest(extra=extra):
                formulae = self.load({
                    "Formula/example.rb": {"platforms": ["linux_amd64"]} | extra,
                })
                self.assertIsNone(formulae["Formula/example.rb"]["update"])
                self.assertEqual(build_matrix(formulae), {
                    "include": [{"formula": "mingcheng/tap/example", "os": "ubuntu-24.04"}]
                })

    def test_rejects_unknown_or_noncanonical_paths(self):
        for path in ("Formula/missing.rb", "../example.rb", "Formula/../Formula/example.rb"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "do not exist"):
                    self.load({path: {}})

    def test_rejects_duplicate_formula_names(self):
        self.add_formula("Formula/tools/example.rb")
        with self.assertRaisesRegex(ValueError, "Duplicate formula name"):
            self.load({})

    def test_rejects_empty_discovery(self):
        (self.root / "Formula/example.rb").unlink()
        with self.assertRaisesRegex(ValueError, "No formulae"):
            self.load({})

    def test_rejects_invalid_platform_lists(self):
        for platforms in ([], ["windows_amd64"], ["darwin_arm64"] * 2, "linux_amd64", [None], [{}]):
            with self.subTest(platforms=platforms):
                with self.assertRaisesRegex(ValueError, "platforms"):
                    self.load({"Formula/example.rb": {"platforms": platforms}})

    def test_rejects_unknown_fields_and_wrong_types(self):
        for entry in ([], None, {"platform": ["linux_amd64"]}, {"update": False}):
            with self.subTest(entry=entry):
                with self.assertRaises(ValueError):
                    self.load({"Formula/example.rb": entry})
        with self.assertRaisesRegex(ValueError, "expected an object"):
            self.load([])

    def test_rejects_invalid_update_fields(self):
        for change in (
            {"repository": None},
            {"repository": "https://github.com/vendor/project"},
            {"repo": "vendor/project"},
            {"assets": {}},
            {"assets": {"linux_amd64": "app.zip"}},
            {"assets": []},
        ):
            with self.subTest(change=change):
                entry = copy.deepcopy(self.entry)
                entry["update"].update(change)
                with self.assertRaises(ValueError):
                    self.load({"Formula/example.rb": entry})
        for field in self.entry["update"]:
            with self.subTest(missing=field):
                entry = copy.deepcopy(self.entry)
                del entry["update"][field]
                with self.assertRaisesRegex(ValueError, "missing fields"):
                    self.load({"Formula/example.rb": entry})

    def test_rejects_invalid_templates(self):
        for field, templates in (
            ("tag", ("v1.0.0", "{name}-{version}", "{version}-{version}", "../{version}",
                     "", None, "{version!r}", "{version:>10}", "{version")),
            ("asset", ("../app.zip", "{platform}.zip", "{name.__class__}.zip",
                       "", None, "{version!r}", "{version:>10}", "{version")),
        ):
            for template in templates:
                with self.subTest(field=field, template=template):
                    entry = copy.deepcopy(self.entry)
                    if field == "tag":
                        entry["update"]["tag"] = template
                    else:
                        entry["update"]["assets"]["darwin_arm64"] = template
                    with self.assertRaises(ValueError):
                        self.load({"Formula/example.rb": entry})

    def test_rejects_duplicate_json_keys(self):
        for contents in (
            '{"Formula/example.rb": {}, "Formula/example.rb": {}}',
            '{"Formula/example.rb": {"update": null, "update": null}}',
        ):
            with self.subTest(contents=contents):
                self.config_path.write_text(contents)
                with self.assertRaisesRegex(ValueError, "Duplicate configuration key"):
                    load_formulae(self.root)

    def test_missing_configuration_is_an_error(self):
        with self.assertRaises(FileNotFoundError):
            load_formulae(self.root)

    def test_checked_in_matrix_covers_existing_packages(self):
        matrix = build_matrix(load_formulae())
        for name in ("aigitcommit", "mp3blstr", "simplyddns", "stupidict"):
            with self.subTest(package=name):
                self.assertEqual(
                    [row for row in matrix["include"] if row["formula"] == f"mingcheng/tap/{name}"],
                    [
                        {"formula": f"mingcheng/tap/{name}", "os": runner}
                        for runner in ("macos-15", "macos-15-intel", "ubuntu-24.04-arm", "ubuntu-24.04")
                    ],
                )


if __name__ == "__main__":
    unittest.main()
