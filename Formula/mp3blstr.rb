class Mp3blstr < Formula
  desc "Terminal music player inspired by mp3blaster"
  homepage "https://github.com/mingcheng/mp3blstr"
  version "1.0.0"
  license "MIT"
  revision 1

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    on_arm do
      url "https://github.com/mingcheng/mp3blstr/releases/download/v1.0.0/mp3blstr_1.0.0_darwin_arm64.tar.gz"
      sha256 "ad1608956665d3d0eb363a3c1013bee6802d2e499f770e954c301cd649064392"
    end
    on_intel do
      url "https://github.com/mingcheng/mp3blstr/releases/download/v1.0.0/mp3blstr_1.0.0_darwin_amd64.tar.gz"
      sha256 "95e3aad01b68888d16c14ddba1c466653a98a05eec667df752af34e77b3e687e"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/mingcheng/mp3blstr/releases/download/v1.0.0/mp3blstr_1.0.0_linux_arm64.tar.gz"
      sha256 "e85f7534924408e4b71a5f54c8126f3ae2c15d8b73c255e8577c37f82a6eddfb"
    end
    on_intel do
      url "https://github.com/mingcheng/mp3blstr/releases/download/v1.0.0/mp3blstr_1.0.0_linux_amd64.tar.gz"
      sha256 "1a0f035cca2d625f3bd59244537f8f1eb7c3523a5c4de93ba3aed49072427600"
    end

    depends_on "alsa-lib"
  end

  conflicts_with "mp3blaster", because: "both install an mp3blaster executable"

  def install
    bin.install "mp3blstr"
    bin.install_symlink "mp3blstr" => "mp3blaster"
    doc.install "README.md", "config.sample.yaml"
    (share/"applications").install "share/applications/mp3blstr.desktop" if OS.linux?
  end

  def caveats
    <<~EOS
      Configuration: ~/.config/mp3blstr/config.yaml
      Example configuration: #{doc}/config.sample.yaml

      On Linux, audio playback requires a working PulseAudio, PipeWire
      (PulseAudio compatibility), or ALSA setup.
    EOS
  end

  test do
    output = shell_output("#{bin}/mp3blstr --version")
    assert_match "version v#{version}", output
    assert_match "Supported audio formats: MP3 WAV OGG/Vorbis FLAC HTTP-streams", output
    assert_predicate bin/"mp3blaster", :symlink?
    assert_equal (bin/"mp3blstr").realpath, (bin/"mp3blaster").realpath
    assert_equal output.sub("mp3blstr version", "mp3blaster version"),
                 shell_output("#{bin}/mp3blaster --version")
    assert_path_exists doc/"config.sample.yaml"
    # assert_path_exists share/"applications/mp3blstr.desktop" if OS.linux?
  end
end
