#!/bin/bash
# Store X API credentials in macOS Keychain via native dialogs
#
# Pops up macOS input dialogs — values never pass through the AI conversation.
# Works both from Claude Code (Bash tool) and from a terminal.

# Ensure keyring is installed
if ! python3 -c "import keyring" 2>/dev/null; then
    echo "Installing keyring..."
    pip3 install keyring
fi

echo "Opening credential dialogs..."
echo ""
echo "Get keys from: https://developer.x.com → your app → Keys and Tokens"
echo "  - Consumer Key + Secret (under Consumer Keys)"
echo "  - Access Token + Secret (under Authentication Tokens — click Generate)"
echo "  - Access Token must have Read+Write permissions"
echo "  - Bearer Token is NOT needed"
echo ""

prompt_key() {
    local label="$1"
    local result
    result=$(osascript -e "display dialog \"$label\" with title \"X API Setup\" default answer \"\" with hidden answer" -e "text returned of result" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$result" ]; then
        echo ""
        return 1
    fi
    echo "$result"
}

api_key=$(prompt_key "Consumer Key:")
[ -z "$api_key" ] && echo "Setup cancelled." && exit 1

api_secret=$(prompt_key "Consumer Secret:")
[ -z "$api_secret" ] && echo "Setup cancelled." && exit 1

access_token=$(prompt_key "Access Token:")
[ -z "$access_token" ] && echo "Setup cancelled." && exit 1

access_token_secret=$(prompt_key "Access Token Secret:")
[ -z "$access_token_secret" ] && echo "Setup cancelled." && exit 1

X_API_KEY="$api_key" \
X_API_SECRET="$api_secret" \
X_ACCESS_TOKEN="$access_token" \
X_ACCESS_TOKEN_SECRET="$access_token_secret" \
python3 - <<'PYEOF'
import keyring, os
keyring.set_password('x-api', 'api_key', os.environ['X_API_KEY'])
keyring.set_password('x-api', 'api_secret', os.environ['X_API_SECRET'])
keyring.set_password('x-api', 'access_token', os.environ['X_ACCESS_TOKEN'])
keyring.set_password('x-api', 'access_token_secret', os.environ['X_ACCESS_TOKEN_SECRET'])
PYEOF

echo "Stored in macOS Keychain."
