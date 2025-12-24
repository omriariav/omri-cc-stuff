# /setup-pulse

Install claude-pulse statusline for real-time token usage monitoring.

## Usage

```
/setup-pulse
```

## Description

Installs [claude-pulse](https://github.com/omriariav/claude-pulse) - a statusline script that shows your context usage as `72k/200k (36%)` with color-coded warnings.

## Instructions

When the user runs `/setup-pulse`:

1. Clone or update the claude-pulse repository:
   ```bash
   if [ -d "$HOME/Code/claude-pulse" ]; then
     cd "$HOME/Code/claude-pulse" && git pull
   else
     mkdir -p "$HOME/Code"
     git clone https://github.com/omriariav/claude-pulse.git "$HOME/Code/claude-pulse"
   fi
   ```

2. Run the install script:
   ```bash
   cd "$HOME/Code/claude-pulse" && ./install.sh
   ```

3. Tell the user to add this to their Claude Code `settings.json`:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "~/.claude/statusline-command.sh"
     }
   }
   ```

   For Windows users:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "powershell -ExecutionPolicy Bypass -File C:/Users/USERNAME/.claude/statusline-command.ps1"
     }
   }
   ```

4. Tell them to restart Claude Code to see the statusline.

## Example Output

After installation:
```
claude-pulse installed successfully!

Add to your settings.json:
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline-command.sh"
  }

Then restart Claude Code to see: 72k/200k (36%)
```

## What It Shows

- Real-time token usage matching `/context`
- Color-coded: Green (<50%) | Yellow (50-79%) | Red (80%+)
- Works with all Claude models
- >100% is normal when context is full (Claude will auto-compact)
