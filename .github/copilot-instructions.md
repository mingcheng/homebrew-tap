# Repository instructions

## Architecture

This repository is the `mingcheng/tap` Homebrew tap. Ruby formulae under
`Formula/` install upstream release artifacts rather than build application
source. The current package, `mp3blstr`, provides prebuilt binaries for macOS
and Linux on ARM64 and x86_64. See [README.md](../README.md) for usage and
formula maintenance instructions.

[tests.yml](workflows/tests.yml) runs formula style, installation, and tests
on four runners covering those OS/architecture combinations. It also serves
as a reusable workflow that accepts a formula artifact.

[update-formulae.yml](workflows/update-formulae.yml) runs daily or manually
on `main`: test the Python updater, check upstream releases, upload modified
formulae, validate them through the reusable workflow, then commit and push
the validated artifact directly to `main`. Preserve this validation-before-
publication ordering.

## Validation commands

Run from the repository root. Register the local checkout before validating
formula changes so Homebrew uses the working copy:

```sh
brew tap --custom-remote mingcheng/tap "$PWD"
brew style mingcheng/tap/mp3blstr
brew install mingcheng/tap/mp3blstr
brew test mingcheng/tap/mp3blstr
```

`brew test` above runs the single formula's `test do` block against the
installed package. If it is already installed, use `brew reinstall
mingcheng/tap/mp3blstr` to exercise changed installation logic.

Check upstream version discovery with `brew livecheck mingcheng/tap/mp3blstr`.

Run all updater unit tests using the same command as the update workflow:

```sh
python3 -B -m unittest discover -s .github/scripts -v
```

Run one updater test by making the scripts directory importable:

```sh
PYTHONPATH=.github/scripts python3 -B -m unittest -v test_update_formulae.UpdateFormulaTests.test_updates_every_platform_and_resets_revision
```

## Formula and updater conventions

- Keep platform URLs, SHA-256 checksums, explicit version, dependencies,
  installation logic, and formula tests consistent. Update the README package
  list when adding or removing packages.
- Preserve `mp3blstr`'s `mp3blaster` compatibility symlink and corresponding
  conflict declaration. Linux requires `alsa-lib` and installs a desktop
  entry; documentation is installed on both operating systems.
- The updater's `FORMULAE` mapping in
  [update_formulae.py](scripts/update_formulae.py) selects supported upstream
  repositories. Adding a formula also requires reviewing the validation
  workflow's package-specific commands.
- Automated updates require stable `vMAJOR.MINOR.PATCH` releases and exactly
  one matching asset per platform: `darwin_arm64`, `darwin_amd64`,
  `linux_arm64`, and `linux_amd64`. Asset names follow
  `<formula>_<version>_<platform>.tar.gz`.
- The updater parses formula text: keep one explicit `version` declaration
  and each `url` immediately followed by its equally indented `sha256`.
  Layout changes must be coordinated with the updater and its tests.
- Download and hash every selected asset, verify its size and any supplied
  GitHub digest, and finish all validation before writing the formula.
  Equal or older releases leave it unchanged; a version update removes
  `revision`. Preserve failure-without-partial-update behavior.
- Updater tests use standard-library `unittest`, mocked network responses,
  and temporary formula files. The updater itself accesses GitHub and edits
  formulae: `python3 -B .github/scripts/update_formulae.py`. It optionally uses
  `GITHUB_TOKEN`; this command is a maintenance action, not a test.
