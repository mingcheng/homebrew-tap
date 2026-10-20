class Stupidict < Formula
  desc "Terminal-based offline English-Chinese dictionary"
  homepage "https://github.com/mingcheng/stupidict"
  version "1.0.0"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    on_arm do
      url "https://github.com/mingcheng/stupidict/releases/download/v1.0.0/stupidict_1.0.0_darwin_arm64.tar.gz"
      sha256 "f5636ba5e24a69219abb9e074e6d2c688880ae42a89b8e2465eac0320428d92a"
    end
    on_intel do
      url "https://github.com/mingcheng/stupidict/releases/download/v1.0.0/stupidict_1.0.0_darwin_amd64.tar.gz"
      sha256 "e75ec9a50411855a946d23977dd10c5349bf45a8653127d0de8b5aaaf1f8eca1"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/mingcheng/stupidict/releases/download/v1.0.0/stupidict_1.0.0_linux_arm64.tar.gz"
      sha256 "07b8db8d527e2b0f93684fcc6563025724c1424477043b6befe403389f8f49cb"
    end
    on_intel do
      url "https://github.com/mingcheng/stupidict/releases/download/v1.0.0/stupidict_1.0.0_linux_amd64.tar.gz"
      sha256 "e2abd72aed5cc4b3b3cbcf5add9b68de140ed31c9ac8dcefd94e87a8d1c98029"
    end

    depends_on "alsa-lib"
  end

  def install
    bin.install "stupidict"
    doc.install "README.md"
  end

  def caveats
    <<~EOS
      Configuration and data: ~/.config/stupidict/
      Dictionary and audio data are downloaded automatically on first run.
      To download data without opening the interface, run:
        stupidict -download

      Dictionary and audio data have separate upstream licensing terms.
      On Linux, audio playback requires a working PulseAudio, PipeWire
      (PulseAudio compatibility), or ALSA setup.
    EOS
  end

  test do
    assert_match "stupidict v#{version}\n", shell_output("#{bin}/stupidict -version")
    assert_match "-download", shell_output("#{bin}/stupidict -help 2>&1")
    assert_path_exists doc/"README.md"
  end
end
