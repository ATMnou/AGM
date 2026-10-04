#!/usr/bin/env python3
import re

path = 'build_tw.py'
src = open(path, encoding='utf-8').read()
pat = re.compile(r"^(\s*)(\w+) = strip_block\(\2, r'(.*)'\)$", re.M)
cm_pat = re.compile(r'\\s\*<li Class="([^"]+)">')

def repl(m):
    indent, var, inner = m.group(1), m.group(2), m.group(3)
    if '<li Class=' not in inner or '.*?</li>' not in inner:
        return m.group(0)
    cm = cm_pat.match(inner)
    if not cm:
        return m.group(0)
    cls = cm.group(1).replace('\\.', '.')
    return "%s%s = remove_comp_li(%s, '%s')" % (indent, var, var, cls)

src, n = pat.subn(repl, src)
open(path, 'w', encoding='utf-8').write(src)
print('patched', n)
