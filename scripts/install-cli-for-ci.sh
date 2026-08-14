#!/usr/bin/env bash
set -euo pipefail

runtime="${1:?usage: install-cli-for-ci.sh <codex|grok|cursor> <pinned|latest>}"
track="${2:-pinned}"

if [[ "$track" != "pinned" && "$track" != "latest" ]]; then
  echo "Unsupported CLI version track: $track" >&2
  exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$root/.github/cli-versions.env"

temp_root="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/omri-marketplace-cli"
install_root="$temp_root/$runtime"
bin_dir="$install_root/bin"
mkdir -p "$bin_dir"

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "This CI installer supports the ubuntu-latest Linux x86_64 runner." >&2
  exit 2
fi

resolve_cursor_latest() {
  local installer
  installer="$(curl -fsSL https://cursor.com/install)"
  if [[ "$installer" =~ downloads\.cursor\.com/lab/([^/]+)/ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
  fi
}

validate_version() {
  local candidate="$1"
  if [[ -z "$candidate" || "$candidate" == *[^A-Za-z0-9._-]* ]]; then
    echo "Resolved an invalid $runtime version: '$candidate'" >&2
    exit 1
  fi
}

verify_pinned_checksum() {
  local path="$1"
  local expected="$2"
  if [[ "$track" != "pinned" ]]; then
    return
  fi

  local actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "$runtime checksum mismatch: expected $expected, got $actual" >&2
    exit 1
  fi
}

case "$runtime" in
  codex)
    version="$CODEX_CLI_VERSION"
    if [[ "$track" == "latest" ]]; then
      version="$(npm view @openai/codex version)"
    fi
    validate_version "$version"
    npm install --prefix "$install_root" --no-audit --no-fund "@openai/codex@$version"
    bin_dir="$install_root/node_modules/.bin"
    executable="$bin_dir/codex"
    ;;
  grok)
    version="$GROK_CLI_VERSION"
    if [[ "$track" == "latest" ]]; then
      version="$(curl -fsSL https://x.ai/cli/stable | tr -d '[:space:]')"
    fi
    validate_version "$version"
    executable="$bin_dir/grok"
    curl -fsSL -o "$executable" "https://x.ai/cli/grok-$version-linux-x86_64"
    verify_pinned_checksum "$executable" "$GROK_CLI_LINUX_X64_SHA256"
    chmod 755 "$executable"
    ;;
  cursor)
    version="$CURSOR_CLI_VERSION"
    if [[ "$track" == "latest" ]]; then
      version="$(resolve_cursor_latest)"
    fi
    validate_version "$version"
    archive="$install_root/cursor-agent.tar.gz"
    payload="$install_root/payload"
    mkdir -p "$payload"
    curl -fsSL -o "$archive" \
      "https://downloads.cursor.com/lab/$version/linux/x64/agent-cli-package.tar.gz"
    verify_pinned_checksum "$archive" "$CURSOR_CLI_LINUX_X64_SHA256"
    tar --strip-components=1 -xzf "$archive" -C "$payload"
    ln -sf "$payload/cursor-agent" "$bin_dir/cursor-agent"
    executable="$bin_dir/cursor-agent"
    ;;
  *)
    echo "Unsupported runtime: $runtime" >&2
    exit 2
    ;;
esac

reported_version="$($executable --version)"
if [[ "$reported_version" != *"$version"* ]]; then
  echo "$runtime reported '$reported_version'; expected version $version" >&2
  exit 1
fi

if [[ -n "${GITHUB_PATH:-}" ]]; then
  printf '%s\n' "$bin_dir" >> "$GITHUB_PATH"
fi
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  printf -- '- `%s`: `%s` (%s)\n' "$runtime" "$reported_version" "$track" >> "$GITHUB_STEP_SUMMARY"
fi

printf 'Installed %s CLI: %s (%s track)\n' "$runtime" "$reported_version" "$track"
