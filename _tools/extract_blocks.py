#!/usr/bin/env python3
"""Extract balanced top-level XML blocks containing a given defName from RimWorld def files.
Usage: python extract_blocks.py <file> <tag> <defName> [<defName>...]
Prints each matched block (with original indentation) to stdout, separated by blank lines.
"""
import re
import sys

def blocks(path, tag):
    text = open(path, encoding="utf-8-sig").read()
    # match top-level-ish <Tag ...> ... </Tag> with nesting counter
    pattern = re.compile(r"[ \t]*<%s(\s[^>]*)?/?>|</%s>" % (tag, tag))
    out = []
    start = None
    depth = 0
    for m in pattern.finditer(text):
        if m.group(0).lstrip().startswith("</"):
            depth -= 1
            if depth == 0 and start is not None:
                out.append(text[start:m.end()])
                start = None
        else:
            if m.group(0).rstrip().endswith("/>"):
                # self-closing tag
                if depth == 0:
                    out.append(text[m.start():m.end()])
            elif depth == 0:
                start = m.start()
                depth = 1
            else:
                depth += 1
    return out

def main():
    path, tag = sys.argv[1], sys.argv[2]
    wanted = set(sys.argv[3:])
    for b in blocks(path, tag):
        m = re.search(r"<defName>([^<]+)</defName>", b)
        if m and m.group(1) in wanted:
            print(b.strip("\n"))
            print()

if __name__ == "__main__":
    main()
