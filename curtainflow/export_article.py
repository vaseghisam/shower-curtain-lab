"""Export the canonical manuscript as one complete TK Markdown file."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'article' / 'why-a-shower-curtain-attacks-you.md'
TARGET = ROOT / 'why-a-shower-curtain-attacks-you-tk.md'


def tk_text(text):
    """Normalize typography and root-relative media; preserve scientific text."""
    replacements = {'\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
                    '\u2013': '-', '\u2014': '--', '\u00a0': ' '}
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    return text.replace('../assets/', 'assets/')


def main():
    text = tk_text(SOURCE.read_text(encoding='utf-8'))
    for line in text.splitlines():
        if '$$' in line and not (line.startswith('$$') and line.endswith('$$') and line.count('$$') == 2):
            raise ValueError('Display equations must each occupy one complete line.')
    temporary = TARGET.with_suffix('.md.tmp')
    temporary.write_text(text, encoding='utf-8')
    temporary.replace(TARGET)
    print(TARGET)


if __name__ == '__main__':
    main()
