#!/usr/bin/env python3
"""Fix devlog timestamps: add full date, clean up duplicate headers."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = 'd:/translation/skills/proofread-docx/devlog_2026-06-26.md'
with open(path, encoding='utf-8') as f:
    content = f.read()

# Step 1: upgrade HH:MM → 2026-06-26 HH:MM
# Match `HH:MM` that's NOT already prefixed with a date
content = re.sub(r'(?<!2026-06-26 )`(\d{2}:\d{2})`', r'`2026-06-26 \1`', content)

# Step 2: fix each problematic header by reading lines and fixing individually
lines = content.split('\n')
new_lines = []
for line in lines:
    if line.startswith('## ') and '`2026' in line:
        # Remove the mid-title timestamp that breaks flow
        # Pattern: "## N. title  `2026-...` rest-of-title  `2026-...`"
        # We want: "## N. full-title  `2026-...`"

        # Find all backtick timestamps
        timestamps = re.findall(r'`2026-06-26 \d{2}:\d{2}`', line)

        # Remove all timestamps from the middle, keep only the last one at end
        for ts in timestamps[:-1]:
            line = line.replace(' ' + ts, '')
            line = line.replace(ts + ' ', '')
            line = line.replace(ts, '')

        # Ensure exactly one timestamp at the end, separated by two spaces
        if timestamps:
            last_ts = timestamps[-1]
            line = line.replace(last_ts, '')
            line = line.rstrip() + '  ' + last_ts

    new_lines.append(line)

content = '\n'.join(new_lines)

# Clean up double spaces (but not the intentional double-space before timestamp)
# Actually just leave it

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Show headers
for line in content.split('\n'):
    if line.startswith('## ') and '2026' in line:
        print(line[:130])
