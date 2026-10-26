class Socks5lb < Formula
  desc "SOCKS5 proxy load balancer with automatic health checks"
  homepage "https://github.com/mingcheng/socks5lb"
  version "1.3.0"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    depends_on macos: :monterey

    on_arm do
      url "https://github.com/mingcheng/socks5lb/releases/download/1.3.0/socks5lb_1.3.0_darwin_arm64.tar.gz"
      sha256 "9457d20c33d447817c1de631f1d005d667a97ed7c2f52708a46a00fdfd0c87c3"
    end
    on_intel do
      url "https://github.com/mingcheng/socks5lb/releases/download/1.3.0/socks5lb_1.3.0_darwin_amd64.tar.gz"
      sha256 "f60f4512d5c7127451768b687695fd69a00ea4b6f2505143eb25c307c3f87a4f"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/mingcheng/socks5lb/releases/download/1.3.0/socks5lb_1.3.0_linux_arm64.tar.gz"
      sha256 "d959e30be55f854cb3d368fc01f2c8a3c5aa0cb353bfa040db4fafe5191b0de6"
    end
    on_intel do
      url "https://github.com/mingcheng/socks5lb/releases/download/1.3.0/socks5lb_1.3.0_linux_amd64.tar.gz"
      sha256 "edc7ae7d60adf2bf2b3b71e86ac5f337533ed29921d73489d2595745ae491d7c"
    end
  end

  def install
    bin.install "socks5lb"
    doc.install "README.md"
    pkgshare.install "socks5lb.yml"
  end

  def caveats
    <<~EOS
      Copy #{pkgshare}/socks5lb.yml and edit the listener addresses and backends
      before running:
        socks5lb -c /path/to/socks5lb.yml
      Without -c, the configuration path is /etc/socks5lb.yml.

      The HTTP management API has no authentication. Bind it to localhost or
      a trusted interface, or protect it with an authenticated reverse proxy.
    EOS
  end

  test do
    ENV["DEBUG"] = "true"
    (testpath/"socks5lb.yml").write "{}\n"
    output = shell_output("#{bin}/socks5lb -c #{testpath}/socks5lb.yml 2>&1", 1)
    assert_match "socks5lb v#{version}(", output
    assert_match "server.socks5.addr is required", output
    assert_match "-c string", shell_output("#{bin}/socks5lb -h 2>&1")
    assert_path_exists doc/"README.md"
    assert_path_exists pkgshare/"socks5lb.yml"
  end
end
