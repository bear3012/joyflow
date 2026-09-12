#!/usr/bin/env python3
from __future__ import annotations
import argparse, fnmatch, hashlib, json, os, pathlib, stat, subprocess, sys
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_bytes(repo: pathlib.Path, *args: str) -> bytes:
    proc=subprocess.run(['git','-C',str(repo),*args],capture_output=True)
    if proc.returncode!=0:
        raise RuntimeError(proc.stderr.decode('utf-8','replace').strip() or 'git command failed')
    return proc.stdout

def safe_repo_path(value: str) -> str:
    value=value.replace('\\','/').strip('/')
    pure=pathlib.PurePosixPath(value)
    if not value or pure.is_absolute() or '..' in pure.parts or value.endswith('/**'):
        raise RuntimeError('declared ignored coverage requires an exact safe repository-relative path')
    return value

def lexical_inside(repo: pathlib.Path, name: str) -> pathlib.Path:
    # safe_repo_path already rejects absolute paths and parent traversal. Keep the
    # final component unresolved so lstat can observe an exact symlink object.
    return repo/pathlib.PurePosixPath(safe_repo_path(name))

def manifest_row(repo: pathlib.Path, name: str, *, expected_kind: str | None=None) -> dict[str,Any]:
    name=safe_repo_path(name); path=lexical_inside(repo,name)
    try: mode=path.lstat().st_mode
    except FileNotFoundError: data=b''; kind='MISSING'
    else:
        if stat.S_ISLNK(mode): data=os.readlink(path).encode('utf-8','surrogateescape'); kind='SYMLINK'
        elif stat.S_ISREG(mode): data=path.read_bytes(); kind='FILE'
        elif stat.S_ISDIR(mode): data=b''; kind='DIRECTORY'
        else: data=b''; kind='OTHER'
    if expected_kind=='FILE' and kind not in {'FILE','MISSING'}: raise RuntimeError(f'declared ignored exact file is not a file: {name}')
    if expected_kind=='SYMLINK' and kind not in {'SYMLINK','MISSING'}: raise RuntimeError(f'declared ignored exact symlink is not a symlink: {name}')
    if expected_kind=='DIRECTORY' and kind not in {'DIRECTORY','MISSING'}: raise RuntimeError(f'declared ignored recursive root is not a directory: {name}')
    row={'path':name,'kind':kind,'bytes':len(data),'sha256':sha_bytes(data)}
    if kind=='SYMLINK': row.update({'link_target':data.decode('utf-8','surrogateescape'),'target_followed':False})
    return row

def parse_directory_spec(value: str) -> dict[str,Any]:
    # ROOT optionally followed by repeated ::EXCLUSION glob fragments.
    parts=value.split('::')
    root=safe_repo_path(parts[0])
    exclusions=sorted({p for p in parts[1:] if p})
    return {'root':root,'exclusions':exclusions}

def coverage_path_excluded(inside: str, repository_relative: str, exclusions: list[str]) -> bool:
    inside=inside.strip('/'); repository_relative=repository_relative.strip('/')
    for pattern in exclusions:
        pattern=pattern.replace('\\','/').strip('/')
        if not pattern: continue
        if fnmatch.fnmatch(inside,pattern) or fnmatch.fnmatch(repository_relative,pattern): return True
        prefix=pattern[:-3].rstrip('/') if pattern.endswith('/**') else pattern
        if inside==prefix or inside.startswith(prefix+'/') or repository_relative==prefix or repository_relative.startswith(prefix+'/'): return True
    return False

def recursive_directory_manifest(repo: pathlib.Path, spec: dict[str,Any]) -> list[dict[str,Any]]:
    root_name=safe_repo_path(spec['root']); exclusions=spec.get('exclusions',[])
    root_row=manifest_row(repo,root_name,expected_kind='DIRECTORY'); rows=[root_row]
    if root_row['kind']=='MISSING': return rows
    base=lexical_inside(repo,root_name)
    for current,dirnames,filenames in os.walk(base,topdown=True,followlinks=False):
        current_path=pathlib.Path(current); kept=[]
        for dirname in sorted(dirnames):
            child=current_path/dirname; inside=child.relative_to(base).as_posix(); rel=child.relative_to(repo).as_posix()
            if coverage_path_excluded(inside,rel,exclusions): continue
            kept.append(dirname)
            if child.is_symlink(): rows.append(manifest_row(repo,rel,expected_kind='SYMLINK'))
            else: rows.append({'path':rel,'kind':'DIRECTORY','bytes':0,'sha256':sha_bytes(b'')})
        dirnames[:]=kept
        for filename in sorted(filenames):
            child=current_path/filename; inside=child.relative_to(base).as_posix(); rel=child.relative_to(repo).as_posix()
            if coverage_path_excluded(inside,rel,exclusions): continue
            rows.append(manifest_row(repo,rel))
    return rows

def normalize_coverage(exact_files: list[str], exact_symlinks: list[str], directories: list[str]) -> dict[str,Any]:
    files=sorted({safe_repo_path(x) for x in exact_files})
    links=sorted({safe_repo_path(x) for x in exact_symlinks})
    dirs=sorted((parse_directory_spec(x) for x in directories),key=lambda x:x['root'])
    roots=files+links+[x['root'] for x in dirs]
    if len(roots)!=len(set(roots)):
        raise RuntimeError('ignored coverage entries overlap by exact root identity')
    return {
      'mode':'DECLARED_EXECUTION_RELEVANT_ONLY',
      'exact_files':files,
      'exact_symlinks':links,
      'recursive_directories':dirs,
      'coverage_status':'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS',
      'full_local_filesystem_unchanged_claim':False,
    }

def untracked_manifest(repo: pathlib.Path) -> bytes:
    raw=git_bytes(repo,'ls-files','--others','--exclude-standard','-z')
    rows=[manifest_row(repo,name.decode('utf-8','surrogateescape').replace('\\','/')) for name in sorted(x for x in raw.split(b'\0') if x)]
    return canonical_bytes(rows)+b'\n'

def declared_ignored_manifest(repo: pathlib.Path, coverage: dict[str,Any]) -> bytes:
    rows=[]
    rows.extend(manifest_row(repo,name,expected_kind='FILE') for name in coverage['exact_files'])
    rows.extend(manifest_row(repo,name,expected_kind='SYMLINK') for name in coverage['exact_symlinks'])
    for spec in coverage['recursive_directories']:
        rows.extend(recursive_directory_manifest(repo,spec))
    return canonical_bytes(sorted(rows,key=lambda r:(r['path'],r['kind'])))+b'\n'

def main() -> int:
    ap=argparse.ArgumentParser(description='Capture a deterministic, bounded, read-only Git worktree fingerprint for Joyflow discovery.')
    ap.add_argument('--repo',required=True)
    ap.add_argument('--phase',required=True,choices=['BEFORE','AFTER'])
    ap.add_argument('--capture-id',required=True)
    ap.add_argument('--evidence-ref',required=True)
    ap.add_argument('--output-dir',required=True)
    ap.add_argument('--include-ignored-file',action='append',default=[],help='Exact ignored/runtime file whose bytes affect this task.')
    ap.add_argument('--include-ignored-symlink',action='append',default=[],help='Exact ignored/runtime symbolic link whose target affects this task.')
    ap.add_argument('--include-ignored-directory',action='append',default=[],metavar='ROOT[::EXCLUSION...]',help='One bounded recursive ignored directory. Optional ::glob exclusions are relative to ROOT or repository.')
    args=ap.parse_args()
    repo=pathlib.Path(args.repo).resolve(); out=pathlib.Path(args.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    coverage=normalize_coverage(args.include_ignored_file,args.include_ignored_symlink,args.include_ignored_directory)
    head=git_bytes(repo,'rev-parse','HEAD').decode('ascii').strip()
    index_diff=git_bytes(repo,'diff','--cached','--binary','--no-ext-diff','--no-textconv')
    worktree_diff=git_bytes(repo,'diff','--binary','--no-ext-diff','--no-textconv')
    untracked=untracked_manifest(repo)
    ignored=declared_ignored_manifest(repo,coverage)
    components={
      'head_commit':head,
      'index_diff_sha256':sha_bytes(index_diff),
      'worktree_diff_sha256':sha_bytes(worktree_diff),
      'untracked_manifest_sha256':sha_bytes(untracked),
      'declared_ignored_manifest_sha256':sha_bytes(ignored),
    }
    state_fingerprint=sha_bytes(canonical_bytes(components))
    record={'capture_id':args.capture_id,'capture_phase':args.phase,**components,'evidence_ref':args.evidence_ref,'state_fingerprint_sha256':state_fingerprint}
    record['capture_record_digest']=sha_bytes(canonical_bytes({'capture_id':record['capture_id'],'capture_phase':record['capture_phase'],'evidence_ref':record['evidence_ref'],'state_fingerprint_sha256':state_fingerprint}))
    (out/'index.diff.bin').write_bytes(index_diff)
    (out/'worktree.diff.bin').write_bytes(worktree_diff)
    (out/'untracked_manifest.json').write_bytes(untracked)
    (out/'declared_ignored_manifest.json').write_bytes(ignored)
    raw_manifest={
      'commands':[
        'git rev-parse HEAD',
        'git diff --cached --binary --no-ext-diff --no-textconv',
        'git diff --binary --no-ext-diff --no-textconv',
        'git ls-files --others --exclude-standard -z',
        'read exact files/symlinks and bounded recursive ignored directories declared for this task only',
      ],
      'component_files':{
        'index_diff':'index.diff.bin','worktree_diff':'worktree.diff.bin','untracked_manifest':'untracked_manifest.json','declared_ignored_manifest':'declared_ignored_manifest.json',
      },
      'ignored_path_coverage':coverage,
      'record':record,
    }
    raw_bytes=canonical_bytes(raw_manifest)+b'\n'; (out/'raw_capture_manifest.json').write_bytes(raw_bytes)
    output={'record':record,'ignored_path_coverage':coverage,'raw_output_ref':str((out/'raw_capture_manifest.json').resolve()),'raw_output_sha256':sha_bytes(raw_bytes)}
    (out/'fingerprint.json').write_bytes(canonical_bytes(output)+b'\n')
    sys.stdout.buffer.write(canonical_bytes(output)+b'\n')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc),file=sys.stderr); raise SystemExit(2)
