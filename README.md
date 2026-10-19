# mingcheng's Homebrew Tap

A personally maintained collection of [Homebrew](https://brew.sh/) formulae.
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

| Package                         | Description                                  | Platforms                     | Upstream                                                    |
| ------------------------------- | -------------------------------------------- | ----------------------------- | ----------------------------------------------------------- |
| [mp3blstr](Formula/mp3blstr.rb) | Terminal music player inspired by mp3blaster | macOS / Linux, ARM64 / x86_64 | [mingcheng/mp3blstr](https://github.com/mingcheng/mp3blstr) |

See each project's upstream documentation for features, usage, and configuration.
Run `brew info mingcheng/tap/<package>` for version, dependency, and installation details.
Each package is subject to its upstream license.

**Installation notes:** `mp3blstr` also provides the `mp3blaster` command and conflicts
with the original `mp3blaster` package. They cannot both be linked; do not force
file overwrites. Audio playback on Linux requires a working PulseAudio,
PipeWire (PulseAudio compatibility), or ALSA setup.

## Updating and Uninstalling

The following commands use `mp3blstr` as an example. Substitute another package name as needed:

```sh
brew update
brew upgrade mingcheng/tap/mp3blstr
brew uninstall mingcheng/tap/mp3blstr
```

Uninstalling generally leaves user configuration and data intact. To remove this tap,
first uninstall its packages, then run `brew untap mingcheng/tap`.

## Maintenance and Validation

Formulae are stored in [Formula](Formula/). When adding or updating a package:

1. Verify the upstream release and set the version, download URLs, SHA-256 checksums, and dependencies.
2. Add or update installation logic and tests, and update the package list above.
3. Declare supported platforms and optionally enable automated updates in
   [.github/formulae.json](.github/formulae.json), as described below.
4. Run the script tests, `brew style`, verify installation, and run `brew test`.
   [GitHub Actions](.github/workflows/tests.yml) discovers formulae automatically;
   adding a package does not require package-specific workflow commands.

To validate locally, use a working copy with at least one Git commit:

```sh
brew tap --custom-remote mingcheng/tap /absolute/path/to/homebrew-tap
brew style mingcheng/tap/mp3blstr
brew install mingcheng/tap/mp3blstr
brew test mingcheng/tap/mp3blstr
```

This clones the local repository and includes only committed changes. Commit subsequent
changes and update the tap before testing them. If a tap with the same name already exists,
check its configuration before replacing it. CI supports macOS and Linux on ARM64
and x86_64, selecting runners from each package's configuration. Automated tests
do not replace real-world usage checks.

For formulae with `livecheck`, run `brew livecheck mingcheng/tap/<package>` to check
for upstream releases. This command does not update formulae automatically.

## Reporting Issues

Report installation or formula issues in [this repository's issue tracker](https://github.com/mingcheng/homebrew-tap/issues).
Include your operating system, architecture, Homebrew version, and error output.
Report application-specific issues to the corresponding upstream project.

Installing and using this public tap does not require a personal GitHub token.
Do not include credentials or other sensitive information in commits or issue reports.
