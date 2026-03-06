# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.

# Parser for natural_language_requests.md test files.

import re


def parse_prompt_file(path: str) -> list[dict]:
    """Parse ## TEST N: Title blocks into test dicts with prompt, keywords, validate_rows."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    tests = []
    blocks = re.split(r'(?=^## TEST )', content, flags=re.MULTILINE)

    for block in blocks:
        match = re.match(r'^## TEST\s+(\w+):\s*(.+)', block)
        if not match:
            continue

        test_id = match.group(1)
        title = match.group(2).strip()

        # Extract keywords directive
        kw_match = re.search(r'\*\*Keywords:\*\*\s*(.+)', block)
        if kw_match:
            keywords = [k.strip().lower() for k in kw_match.group(1).split(',')]
        else:
            # Auto-extract from title words
            stop_words = {'a', 'an', 'the', 'and', 'or', 'for', 'in', 'on',
                          'to', 'with', 'by', 'of', 'vs', 'from', 'is', 'at'}
            keywords = [w.lower() for w in re.findall(r'\w+', title)
                        if w.lower() not in stop_words and len(w) > 1]

        # Extract validate directive
        val_match = re.search(r'\*\*Validate:\*\*\s*(.+)', block)
        validate_rows = val_match.group(1).strip() if val_match else ""

        # Extract prompt: everything between header and directives/separators
        # Remove the header line
        prompt_text = re.sub(r'^## TEST\s+\w+:\s*.+\n?', '', block)
        # Remove directive lines
        prompt_text = re.sub(r'\*\*Keywords:\*\*\s*.+\n?', '', prompt_text)
        prompt_text = re.sub(r'\*\*Validate:\*\*\s*.+\n?', '', prompt_text)
        # Remove separator lines
        prompt_text = re.sub(r'^────.*$', '', prompt_text, flags=re.MULTILINE)
        # Strip blockquote prefixes and surrounding quotes
        lines = []
        for line in prompt_text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('> '):
                stripped = stripped[2:]
            elif stripped == '>':
                stripped = ''
            # Remove surrounding quotes from blockquote lines
            stripped = stripped.strip('"')
            lines.append(stripped)

        prompt = '\n'.join(lines).strip()
        # Collapse multiple blank lines
        prompt = re.sub(r'\n{3,}', '\n\n', prompt)

        if not prompt:
            continue

        tests.append({
            "id": test_id,
            "name": title,
            "prompt": prompt,
            "keywords": keywords,
            "validate_rows": validate_rows,
        })

    if not tests:
        raise ValueError(f"No tests found in {path}")

    return tests
