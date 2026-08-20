"""Shared SSL trust-store fallback for natbag scripts.

python.org macOS builds ship with an empty certificate store until
Install Certificates.command is run, and some pyenv/conda builds point
at CA paths that don't exist. get_ssl_context() returns None when the
interpreter's default trust store is usable (so urlopen configures its
own default context — ALPN and all), otherwise a context wired to the
first working CA bundle: certifi, then common OS bundle locations.
"""

import os
import ssl
import sys

OS_BUNDLES = (
    "/etc/ssl/cert.pem",                    # macOS, BSD
    "/etc/ssl/certs/ca-certificates.crt",   # Debian/Ubuntu
    "/etc/pki/tls/certs/ca-bundle.crt",     # RHEL/Fedora/CentOS
    "/etc/ssl/ca-bundle.pem",               # openSUSE
)

_cache = {"resolved": False, "context": None}


def _default_store_usable():
    if ssl.create_default_context().cert_store_stats().get("x509_ca"):
        return True
    # capath-based stores load certs lazily and report zero here, so also
    # trust the default when its verify locations exist on disk.
    # get_default_verify_paths() already nulls out missing paths.
    paths = ssl.get_default_verify_paths()
    return bool(paths.cafile or paths.capath)


def _fallback_context():
    candidates = []
    try:
        import certifi
        candidates.append(certifi.where())
    except ImportError:
        pass
    candidates.extend(OS_BUNDLES)
    for cafile in candidates:
        try:
            ctx = ssl.create_default_context(cafile=cafile)
        except (OSError, ssl.SSLError):
            continue  # missing or corrupt bundle — try the next one
        ctx.set_alpn_protocols(["http/1.1"])  # http.client sets this on its default context
        return ctx
    print(
        "natbag: no usable CA bundle found — HTTPS will fail. "
        "Fix: 'pip install certifi', or on macOS run 'Install Certificates.command'.",
        file=sys.stderr,
    )
    return None


def get_ssl_context():
    """None when the default trust store works; a fallback context otherwise."""
    if not _cache["resolved"]:
        _cache["context"] = None if _default_store_usable() else _fallback_context()
        _cache["resolved"] = True
    return _cache["context"]
