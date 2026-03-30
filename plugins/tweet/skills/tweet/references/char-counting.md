# Character Counting Rules

**Your markdown char count will NOT match the script's count.** Common mismatches:

- **URLs**: X wraps all URLs to t.co (23 chars), but `post.py` counts raw URL length. Always count the full URL string length, not 23.
- **Backticks**: Backtick characters (`` ` ``) in your preview are real chars in the tweet. Don't use them in length estimation then omit them.
- **Newlines**: Each `\n` counts as a character.
- **Em dashes**: `—` is 1 char but may render wider in preview.

**Best practice**: Aim for **270 chars max** in your preview to leave a safety margin. If the script rejects, you only need to trim a few words instead of multiple retry loops.

**Do NOT estimate char count yourself.** If close to the limit, use `python3 -c "print(len('''tweet text here'''))"` to get the exact count before previewing to the user.
