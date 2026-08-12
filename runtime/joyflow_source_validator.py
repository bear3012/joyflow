#!/usr/bin/env python3
from __future__ import annotations
import pathlib, re, sys

RULE_RE=re.compile(r'^canonical_rule_id:\s*([A-Z0-9_]+)\s*$',re.M)
SECTION_RE=re.compile(r'^source_section_id:\s*([^\n]+)\s*$',re.M)


def scan(root:pathlib.Path):
    sources=sorted((root/'project_sources').glob('*.md'))
    rows=[]; errors=[]
    for path in sources:
        text=path.read_text(encoding='utf-8')
        rules=list(RULE_RE.finditer(text)); sections=list(SECTION_RE.finditer(text))
        if len(rules)!=len(sections): errors.append(f'{path.name}: rule/section count mismatch')
        for i,rule in enumerate(rules):
            if i>=len(sections): break
            rows.append((rule.group(1),sections[i].group(1).strip(),path.name))
    ids=[r[0] for r in rows]; secs=[r[1] for r in rows]
    dup_ids=sorted({x for x in ids if ids.count(x)>1}); dup_secs=sorted({x for x in secs if secs.count(x)>1})
    if dup_ids: errors.append('duplicate rule IDs: '+', '.join(dup_ids))
    if dup_secs: errors.append('duplicate section IDs: '+', '.join(dup_secs))
    return rows,errors


def index_text(rows):
    lines=['# GENERATED RULE INDEX','', '> Generated from active Project Sources. Do not edit manually.','', '| canonical_rule_id | source_section_id | source |','|---|---|---|']
    for rid,sec,src in sorted(rows): lines.append(f'| `{rid}` | `{sec}` | `{src}` |')
    lines.append('')
    return '\n'.join(lines)


def main():
    root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1])
    rows,errors=scan(root)
    target=root/'project_sources'/'12_GENERATED_RULE_INDEX.md'
    expected=index_text(rows)
    if not target.exists() or target.read_text(encoding='utf-8')!=expected: errors.append('generated rule index drift')
    if errors:
        print('\n'.join(errors),file=sys.stderr); return 2
    print(f'PASS rules={len(rows)} unique={len({r[0] for r in rows})}')
    return 0
if __name__=='__main__': raise SystemExit(main())
