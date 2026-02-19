#!/bin/bash
# Verify tweet skill dependencies and credentials

errors=0

# Check requests-oauthlib
if python3 -c "import requests_oauthlib" 2>/dev/null; then
    echo "  requests-oauthlib: installed"
else
    echo "  requests-oauthlib: MISSING — run: pip3 install requests-oauthlib"
    errors=$((errors + 1))
fi

# Check credentials (env vars)
found_env=0
for var in X_API_KEY X_API_SECRET X_ACCESS_TOKEN X_ACCESS_TOKEN_SECRET; do
    if [ -n "${!var}" ]; then
        found_env=$((found_env + 1))
    fi
done

# Check credentials (keyring)
found_keyring=0
if python3 -c "import keyring" 2>/dev/null; then
    kr=$(python3 -c "
import keyring
keys = ['api_key','api_secret','access_token','access_token_secret']
print(sum(1 for k in keys if keyring.get_password('x-api', k)))
" 2>/dev/null)
    found_keyring=${kr:-0}
fi

if [ "$found_env" -eq 4 ]; then
    echo "  Credentials: found via env vars"
elif [ "$found_keyring" -eq 4 ]; then
    echo "  Credentials: found via keyring"
else
    echo "  Credentials: MISSING — run: bash skills/tweet/scripts/setup.sh (keychain) or set env vars in ~/.zshrc"
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    echo ""
    echo "Ready to tweet!"
else
    echo ""
    echo "$errors issue(s) found. Fix them before using /tweet."
    exit 1
fi
