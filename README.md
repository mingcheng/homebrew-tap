# mingcheng's Homebrew Tap

A personally maintained collection of [Homebrew](https://brew.sh/) formulae.
Packages install prebuilt upstream release binaries rather than build from source.

## Usage

With Homebrew installed, add this tap:

```sh
brew tap mingcheng/tap
```

Install a package with `brew install mingcheng/tap/<package>`, for example:

```sh
brew install mingcheng/tap/mp3blstr
```

You can also skip the tap step and install directly using the fully qualified name above.

## Packages

| Package                               | Description                                                        | Platforms                         | Upstream                                                          |
| ------------------------------------- | ------------------------------------------------------------------ | --------------------------------- | ----------------------------------------------------------------- |
| [aigitcommit](Formula/aigitcommit.rb) | Generate Conventional Commit messages using OpenAI-compatible APIs | macOS / Linux, ARM64 / x86_64     | [mingcheng/aigitcommit](https://github.com/mingcheng/aigitcommit) |
| [mp3blstr](Formula/mp3blstr.rb)       | Terminal music player inspired by mp3blaster                       | macOS / Linux, ARM64 / x86_64     | [mingcheng/mp3blstr](https://github.com/mingcheng/mp3blstr)       |
| [simplyddns](Formula/simplyddns.rb)   | Dynamic DNS client with configurable IP sources and DNS providers  | macOS / Linux, ARM64 / x86_64     | [mingcheng/simplyddns](https://github.com/mingcheng/simplyddns)   |
| [socks5lb](Formula/socks5lb.rb)       | SOCKS5 proxy load balancer with automatic health checks            | macOS 12+ / Linux, ARM64 / x86_64 | [mingcheng/socks5lb](https://github.com/mingcheng/socks5lb)       |
| [stupidict](Formula/stupidict.rb)     | Terminal-based offline English-Chinese dictionary                  | macOS / Linux, ARM64 / x86_64     | [mingcheng/stupidict](https://github.com/mingcheng/stupidict)     |

See each project's upstream documentation for features, usage, and configuration.
Run `brew info mingcheng/tap/<package>` for version, dependency, and installation details.
Each package is subject to its upstream license.

## Updating and Uninstalling

Refresh Homebrew metadata and upgrade an installed package (`mp3blstr` here for example):

```sh
brew update
brew upgrade mingcheng/tap/mp3blstr
```

To uninstall it:

```sh
brew uninstall mingcheng/tap/mp3blstr
```

Uninstalling generally leaves user configuration and data intact. To remove this tap,
first uninstall its packages, then run `brew untap mingcheng/tap`.

## Maintenance and Validation

Formulae are stored in [Formula](Formula/). When adding or updating a package:

1. Verify the upstream release and set the version, download URLs, SHA-256 checksums, and dependencies.
2. Add or update installation logic and tests, and update the package list above.
3. Configure the validation platforms and optionally enable automated updates in
   [.github/formulae.json](.github/formulae.json).
4. Run the script tests, `brew style`, verify installation, and run `brew test`.
   [GitHub Actions](.github/workflows/tests.yml) discovers formulae automatically;
   adding a package does not require package-specific workflow commands.

Markdown files are checked with [prek](https://prek.j178.dev/) locally and in CI.
With prek available through mise, install the commit hook and check all tracked
Markdown files:

```sh
prek install
prek run --all-files
```

The hook configuration is in [.pre-commit-config.yaml](.pre-commit-config.yaml).
[.markdownlint-cli2.yaml](.markdownlint-cli2.yaml) keeps the default Markdown rules
except line length, allowing long links and package tables.

To validate formulae locally, use a working copy with at least one Git commit:

```sh
brew tap --custom-remote mingcheng/tap "$PWD"
brew style mingcheng/tap/mp3blstr
brew install mingcheng/tap/mp3blstr
brew test mingcheng/tap/mp3blstr
```

Homebrew clones the local repository into its tap directory; this does not link
the working tree, and uncommitted changes are not included. After subsequent
commits, run `brew update` to refresh that clone. If `mingcheng/tap` is already
tapped, inspect its remote with `git -C "$(brew --repository mingcheng/tap)"
remote -v` before changing the setup; the tap command above does not replace an
existing tap automatically.

If the package is already installed, use `brew reinstall mingcheng/tap/mp3blstr`
instead of `brew install` to exercise changed installation logic. `brew test`
runs the formula's `test do` block against the installed package; it does not
install the modified formula for you. Substitute another package name as needed.

CI runs style, installation, and formula tests on macOS and Linux, using ARM64
and x86_64 runners selected by the package configuration. Local validation tests
only the current platform. Automated tests do not replace real-world usage checks.

For formulae with `livecheck`, run `brew livecheck mingcheng/tap/<package>` to check
for upstream releases. This command does not update formulae automatically.

## Reporting Issues

Report installation or formula issues in [this repository's issue tracker](https://github.com/mingcheng/homebrew-tap/issues).
Include your operating system, architecture, Homebrew version, and error output.
Report application-specific issues to the corresponding upstream project.

Installing and using this public tap does not require a personal GitHub token.
Do not include credentials or other sensitive information in commits or issue reports.
