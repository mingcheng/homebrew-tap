class Simplyddns < Formula
  desc "Flexible dynamic DNS client with configurable IP sources and DNS providers"
  homepage "https://github.com/mingcheng/simplyddns"
  version "1.6.1"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    on_arm do
      url "https://github.com/mingcheng/simplyddns/releases/download/v1.6.1/simplyddns_1.6.1_darwin_arm64.tar.gz"
      sha256 "216444e43d26c5410a51ebc2fd6fb85dd3cfae830793cb705eeadca6a9df88a6"
    end
    on_intel do
      url "https://github.com/mingcheng/simplyddns/releases/download/v1.6.1/simplyddns_1.6.1_darwin_amd64.tar.gz"
      sha256 "0c314f6ca97a4a61f6f0c52a0ab1c9314693b208966d16fb523e24f252a82f5c"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/mingcheng/simplyddns/releases/download/v1.6.1/simplyddns_1.6.1_linux_arm64.tar.gz"
      sha256 "b5a0aeebca5165639e4658e5f92b079851ceb13bea6ad2cb96e44f056b49f5b0"
    end
    on_intel do
      url "https://github.com/mingcheng/simplyddns/releases/download/v1.6.1/simplyddns_1.6.1_linux_amd64.tar.gz"
      sha256 "fa0dde2d30bcf4cc0457ff526a92674bf2e7e45678a5ace3be1e94bcd1461326"
    end
  end

  def install
    bin.install "simplyddns"
  end

  def caveats
    <<~EOS
      Create simplyddns.yml before running simplyddns.
      Configuration is searched for in this order:
        /etc/simplyddns/
        ~/.config/simplyddns/
        the current working directory

      Configuration examples:
        https://github.com/mingcheng/simplyddns/tree/master/example
      Protect configuration files containing DNS provider credentials.
    EOS
  end

  test do
    (testpath/"simplyddns.yml").write "ddns: [\n"
    output = shell_output("#{bin}/simplyddns 2>&1", 1)
    assert_match "simplyddns #{version}", output
    assert_match "yaml:", output
  end
end
