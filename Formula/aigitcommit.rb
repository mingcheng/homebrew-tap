class Aigitcommit < Formula
  desc "Generate Conventional Commit messages using OpenAI-compatible APIs"
  homepage "https://github.com/mingcheng/aigitcommit"
  version "1.9.7"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  uses_from_macos "zlib"

  on_macos do
    depends_on macos: :ventura

    on_arm do
      url "https://github.com/mingcheng/aigitcommit/releases/download/v1.9.7/aigitcommit-1.9.7-aarch64-apple-darwin.tar.gz"
      sha256 "734bd64791521f9278dba8d7bce85a16dedbb79b9e678a9b1a12277af345d511"
    end
    on_intel do
      url "https://github.com/mingcheng/aigitcommit/releases/download/v1.9.7/aigitcommit-1.9.7-x86_64-apple-darwin.tar.gz"
      sha256 "695e390fd133ffa42c16fe87431c5acb6aa6441aa07e4fa78f60e13385326b7f"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/mingcheng/aigitcommit/releases/download/v1.9.7/aigitcommit-1.9.7-aarch64-unknown-linux-gnu.tar.gz"
      sha256 "ab3543867dc54fdb634b7c00e3dd4086cb14e1968dd7313b3b6d8738f6ef7615"
    end
    on_intel do
      url "https://github.com/mingcheng/aigitcommit/releases/download/v1.9.7/aigitcommit-1.9.7-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "90a1696829305f9fb909cd5eb7a75a3733855b218663ca206de60f1dc7fbc58a"
    end
  end

  def install
    bin.install "aigitcommit"
    doc.install "README.md"
  end

  def caveats
    <<~EOS
      Set OPENAI_API_TOKEN before generating commit messages.
      Optionally set OPENAI_API_BASE and OPENAI_API_MODEL for your provider.
      Run aigitcommit --check-env to check configuration without an API request.
      Generating messages sends staged changes to the configured API provider.
    EOS
  end

  test do
    assert_match "aigitcommit v#{version}(", shell_output("#{bin}/aigitcommit --version")
    ENV["OPENAI_API_TOKEN"] = ""
    assert_match "OPENAI_API_TOKEN: not set", shell_output("#{bin}/aigitcommit --check-env")
    system "git", "init", "--quiet"
    output = shell_output("#{bin}/aigitcommit 2>&1", 1)
    assert_match "no staged changes found", output
    assert_path_exists doc/"README.md"
  end
end
