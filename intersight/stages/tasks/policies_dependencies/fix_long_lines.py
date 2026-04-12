#!/usr/bin/env python3
import re
import os

# Pattern to replace long query expressions in when clauses
# Replace the long inline queries with variable references
replacements = [
    # Generalized patterns
    (
        r"when: >-\s+\(query\('ansible\.builtin\.subelements'[^)]+\) \| length > 0\)\s+or\s+\(query\('ansible\.builtin\.subelements'[^)]+\) \| length > 0\)",
        "when: flag1 or flag2  # Need manual fix"
    ),
]

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) > 120 and 'query' in line and "'" in line:
            # This is a long query line, try to shorten it
            if 'when: >' in line or 'when: >-' in line:
                # Multi-line when condition
                print(f"Manual fix needed at {filepath}:{i+1}")
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

# Find all yaml files
for f in os.listdir('.'):
    if f.endswith('.yaml') and f != '_computed_dependency_flags.yaml':
        lines_over_120 = 0
        with open(f, 'r') as file:
            for i, line in enumerate(file, 1):
                if len(line.rstrip()) > 120:
                    lines_over_120 += 1
        if lines_over_120 > 0:
            print(f"{f}: {lines_over_120} lines need fixing")
