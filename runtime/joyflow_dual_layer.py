"""Joyflow Phase 1 repository-anchored dual-layer task compiler.

The repository is the only persistent project truth. This module handles only a
bounded temporary Fibered Task Capsule, deterministic approval/prompt views,
and a merge-only promotion candidate.
"""
from __future__ import annotations
import argparse
import ast
import base64
import contextlib
import copy
import fnmatch
import hashlib
import json
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import zlib
from typing import Any, Iterable
import yaml
from jsonschema import Draft202012Validator
ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / 'machine' / 'joyflow_dual_layer_model.yaml'
CAPSULE_SCHEMA = ROOT / 'schemas' / 'fibered_task_capsule.schema.json'
BRAIN_CAPSULE_MANIFEST_SCHEMA = ROOT / 'schemas' / 'brain_capsule_semantic_manifest.schema.json'
PROJECTION_SCHEMA = ROOT / 'schemas' / 'codex_handoff_projection.schema.json'
APPROVAL_SCHEMA = ROOT / 'schemas' / 'approval_view.schema.json'
CODEX_RETURN_SCHEMA = ROOT / 'schemas' / 'codex_execution_return.schema.json'
EVIDENCE_BUNDLE_SCHEMA = ROOT / 'schemas' / 'codex_execution_evidence_bundle.schema.json'
EVIDENCE_TRANSPORT_RECEIPT_SCHEMA = ROOT / 'schemas' / 'evidence_transport_receipt.schema.json'
EVIDENCE_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA = ROOT / 'schemas' / 'evidence_transport_cleanup_continuation.schema.json'
CURRENT_PR_REVIEW_INPUT_TRANSPORT_SCHEMA = ROOT / 'schemas' / 'current_pr_review_input_transport.schema.json'
CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA = ROOT / 'schemas' / 'current_pr_review_transport_cleanup_continuation.schema.json'
PATH_DISCOVERY_RETURN_SCHEMA = ROOT / 'schemas' / 'path_discovery_return.schema.json'
LONG_TERM_STRUCTURAL_PROJECTION_SCHEMA = ROOT / 'schemas' / 'long_term_structural_projection.schema.json'
GITHUB_PATH_EVIDENCE_SCHEMA = ROOT / 'schemas' / 'github_path_evidence.schema.json'
FINAL_PATH_DECISION_SCHEMA = ROOT / 'schemas' / 'final_path_decision.schema.json'
MERGE_GATE_SCHEMA = ROOT / 'schemas' / 'merge_gate_record.schema.json'
MERGE_FREEZE_SCHEMA = ROOT / 'schemas' / 'merge_candidate_freeze.schema.json'
USER_MERGE_AUTHORIZATION_SCHEMA = ROOT / 'schemas' / 'user_merge_authorization.schema.json'
COMPLETION_POINTER_SCHEMA = ROOT / 'schemas' / 'task_completion_pointer.schema.json'
GENERATOR_PATH = ROOT / 'tools' / 'generate_mechanical_assets.py'
ENVELOPE_RE = re.compile(r'<JOYFLOW_MACHINE_ENVELOPE encoding="zlib\+base64url">([A-Za-z0-9_-]+)</JOYFLOW_MACHINE_ENVELOPE>')
COMPACT_VIEW_RE = re.compile('<JOYFLOW_COMPACT_EXECUTION_VIEW encoding="json">(.*?)</JOYFLOW_COMPACT_EXECUTION_VIEW>', re.DOTALL)

class JoyflowError(Exception):
    pass

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def file_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()




def _canonical_argv(argv: list[str]) -> str:
    if not isinstance(argv,list) or not argv or any(not isinstance(x,str) or not x for x in argv):
        raise JoyflowError('validation argv must be a non-empty string array')
    return shlex.join(argv)

def _run_source_command(argv: list[str], *, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True)

def _git_source_bytes(repo: pathlib.Path, *args: str) -> bytes:
    proc=_run_source_command(['git','-C',str(repo),*args])
    if proc.returncode!=0:
        raise JoyflowError(proc.stderr.decode('utf-8','replace').strip() or f"git source replay failed: {' '.join(args)}")
    return proc.stdout

def _canonical_repository_id(remote: str) -> str:
    remote=remote.strip()
    for pattern in (r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', r'^https?://[^/]+/([^/]+/[^/]+?)(?:\.git)?$'):
        match=re.search(pattern,remote)
        if match:
            return match.group(1)
    raise JoyflowError('repository origin cannot be converted to owner/repo identity')

def _repository_source_identity(repository: str | pathlib.Path) -> tuple[pathlib.Path,str,str]:
    repo=pathlib.Path(repository).resolve()
    root=pathlib.Path(_git_source_bytes(repo,'rev-parse','--show-toplevel').decode().strip()).resolve()
    head=_git_source_bytes(root,'rev-parse','HEAD').decode().strip()
    remote=_git_source_bytes(root,'config','--get','remote.origin.url').decode().strip()
    return root,_canonical_repository_id(remote),head

def _safe_relative_path(name: str) -> str:
    normalized=name.replace('\\','/').strip('/')
    pure=pathlib.PurePosixPath(normalized)
    if not normalized or pure.is_absolute() or '..' in pure.parts or normalized.endswith('/**'):
        raise JoyflowError('declared worktree coverage path must be an exact safe repository-relative path')
    return normalized

def _boundary_safe_repository_object(root: pathlib.Path, name: str) -> tuple[pathlib.Path,str,bytes]:
    """Resolve one declared repository object without following any parent symlink.

    The repository-relative spelling is part of the approved boundary. A lexical
    path is not enough: every parent component must be a real directory. The
    final component is inspected with lstat so an explicitly declared symlink is
    consumed as a symlink object and its target is never followed.
    """
    import os, stat
    name=_safe_relative_path(name)
    root=root.resolve()
    current=root
    parts=pathlib.PurePosixPath(name).parts
    for index,part in enumerate(parts):
        current=current/part
        final=index==len(parts)-1
        try:
            mode=current.lstat().st_mode
        except FileNotFoundError:
            return current,'MISSING',b''
        if not final:
            if stat.S_ISLNK(mode):
                raise JoyflowError(f'declared repository path crosses a parent symlink: {name}')
            if not stat.S_ISDIR(mode):
                raise JoyflowError(f'declared repository path has a non-directory parent: {name}')
            continue
        if stat.S_ISLNK(mode):
            return current,'SYMLINK',os.readlink(current).encode('utf-8','surrogateescape')
        if stat.S_ISREG(mode):
            return current,'FILE',current.read_bytes()
        if stat.S_ISDIR(mode):
            return current,'DIRECTORY',b''
        return current,'OTHER',b''
    raise JoyflowError('declared repository path is empty')


def _manifest_row_for_path(root: pathlib.Path, name: str, *, expected_kind: str | None=None) -> dict[str,Any]:
    name=_safe_relative_path(name)
    _,kind,data=_boundary_safe_repository_object(root,name)
    if expected_kind=='FILE' and kind not in {'FILE','MISSING'}:
        raise JoyflowError(f'declared ignored exact file is not a file: {name}')
    if expected_kind=='SYMLINK' and kind not in {'SYMLINK','MISSING'}:
        raise JoyflowError(f'declared ignored exact symlink is not a symlink: {name}')
    if expected_kind=='DIRECTORY' and kind not in {'DIRECTORY','MISSING'}:
        raise JoyflowError(f'declared ignored recursive root is not a directory: {name}')
    row={'path':name,'kind':kind,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if kind=='SYMLINK':
        row['link_target']=data.decode('utf-8','surrogateescape')
        row['target_followed']=False
    return row

def _coverage_path_excluded(inside: str, repository_relative: str, exclusions: list[str]) -> bool:
    inside=inside.strip('/')
    repository_relative=repository_relative.strip('/')
    for pattern in exclusions:
        pattern=pattern.replace('\\','/').strip('/')
        if not pattern:
            continue
        if fnmatch.fnmatch(inside,pattern) or fnmatch.fnmatch(repository_relative,pattern):
            return True
        # A directory exclusion such as `secret` or `tmp/**` must prune the
        # entire subtree before any descendant is opened.
        prefix=pattern[:-3].rstrip('/') if pattern.endswith('/**') else pattern
        if inside==prefix or inside.startswith(prefix+'/') or repository_relative==prefix or repository_relative.startswith(prefix+'/'):
            return True
    return False

def _recursive_directory_manifest(root: pathlib.Path, spec: dict[str,Any]) -> list[dict[str,Any]]:
    import os
    dir_name=_safe_relative_path(spec['root'])
    exclusions=spec.get('exclusions',[])
    root_row=_manifest_row_for_path(root,dir_name,expected_kind='DIRECTORY')
    rows=[root_row]
    if root_row['kind']=='MISSING':
        return rows
    root=root.resolve(); base=root/pathlib.PurePosixPath(dir_name)
    for current, dirnames, filenames in os.walk(base,topdown=True,followlinks=False):
        current_path=pathlib.Path(current)
        kept=[]
        for dirname in sorted(dirnames):
            child=current_path/dirname
            inside=child.relative_to(base).as_posix(); rel=child.relative_to(root).as_posix()
            if _coverage_path_excluded(inside,rel,exclusions):
                continue
            if child.is_symlink():
                rows.append(_manifest_row_for_path(root,rel,expected_kind='SYMLINK'))
                continue
            kept.append(dirname)
            rows.append({'path':rel,'kind':'DIRECTORY','bytes':0,'sha256':hashlib.sha256(b'').hexdigest()})
        dirnames[:]=kept
        for filename in sorted(filenames):
            child=current_path/filename
            inside=child.relative_to(base).as_posix(); rel=child.relative_to(root).as_posix()
            if _coverage_path_excluded(inside,rel,exclusions):
                continue
            rows.append(_manifest_row_for_path(root,rel))
    return rows

def _normalize_ignored_coverage(coverage: dict[str,Any] | None) -> dict[str,Any]:
    coverage=copy.deepcopy(coverage or {})
    if not coverage:
        coverage={'mode':'DECLARED_EXECUTION_RELEVANT_ONLY','exact_files':[],'exact_symlinks':[],'recursive_directories':[],'coverage_status':'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS','full_local_filesystem_unchanged_claim':False}
    required={'mode','exact_files','exact_symlinks','recursive_directories','coverage_status','full_local_filesystem_unchanged_claim'}
    if set(coverage)!=required or coverage['mode']!='DECLARED_EXECUTION_RELEVANT_ONLY' or coverage['full_local_filesystem_unchanged_claim'] is not False:
        raise JoyflowError('ignored path coverage contract shape mismatch')
    exact_files=sorted({_safe_relative_path(x) for x in coverage['exact_files']})
    exact_symlinks=sorted({_safe_relative_path(x) for x in coverage['exact_symlinks']})
    dirs=[]
    for row in coverage['recursive_directories']:
        if set(row)!={'root','exclusions'}:
            raise JoyflowError('recursive ignored directory coverage shape mismatch')
        dirs.append({'root':_safe_relative_path(row['root']),'exclusions':sorted(set(row['exclusions']))})
    dirs=sorted(dirs,key=lambda r:r['root'])
    all_roots=exact_files+exact_symlinks+[r['root'] for r in dirs]
    if len(all_roots)!=len(set(all_roots)):
        raise JoyflowError('ignored coverage entries overlap by exact root identity')
    coverage['exact_files']=exact_files; coverage['exact_symlinks']=exact_symlinks; coverage['recursive_directories']=dirs
    return coverage

def _coverage_contains_path(coverage: dict[str,Any], path: str) -> bool:
    coverage=_normalize_ignored_coverage(coverage)
    path=_safe_relative_path(path)
    if path in coverage['exact_files'] or path in coverage['exact_symlinks']:
        return True
    for spec in coverage['recursive_directories']:
        root=spec['root'].rstrip('/')
        if path==root or path.startswith(root+'/'):
            inside=path[len(root):].lstrip('/')
            if any(fnmatch.fnmatch(inside,pat) or fnmatch.fnmatch(path,pat) for pat in spec['exclusions']):
                return False
            return True
    return False

def _declared_ignored_manifest(repository: str | pathlib.Path, coverage: dict[str,Any] | None) -> bytes:
    root,_,_=_repository_source_identity(repository)
    coverage=_normalize_ignored_coverage(coverage)
    rows=[]
    rows.extend(_manifest_row_for_path(root,name,expected_kind='FILE') for name in coverage['exact_files'])
    rows.extend(_manifest_row_for_path(root,name,expected_kind='SYMLINK') for name in coverage['exact_symlinks'])
    for spec in coverage['recursive_directories']:
        rows.extend(_recursive_directory_manifest(root,spec))
    rows=sorted(rows,key=lambda r:(r['path'],r['kind']))
    return canonical_bytes(rows)+b'\n'

def _source_worktree_components(repository: str | pathlib.Path, ignored_coverage: dict[str,Any] | None=None) -> dict[str,str]:
    root,_,head=_repository_source_identity(repository)
    index_diff=_git_source_bytes(root,'diff','--cached','--binary','--no-ext-diff','--no-textconv')
    worktree_diff=_git_source_bytes(root,'diff','--binary','--no-ext-diff','--no-textconv')
    raw=_git_source_bytes(root,'ls-files','--others','--exclude-standard','-z')
    rows=[]
    for name_b in sorted(x for x in raw.split(b'\0') if x):
        name=name_b.decode('utf-8','surrogateescape').replace('\\','/')
        rows.append(_manifest_row_for_path(root,name))
    untracked=canonical_bytes(rows)+b'\n'
    ignored=_declared_ignored_manifest(root,ignored_coverage)
    return {
      'head_commit':head,
      'index_diff_sha256':hashlib.sha256(index_diff).hexdigest(),
      'worktree_diff_sha256':hashlib.sha256(worktree_diff).hexdigest(),
      'untracked_manifest_sha256':hashlib.sha256(untracked).hexdigest(),
      'declared_ignored_manifest_sha256':hashlib.sha256(ignored).hexdigest(),
    }

def _repository_current_paths(repository: str | pathlib.Path, ignored_coverage: dict[str,Any] | None=None) -> list[str]:
    root,_,_=_repository_source_identity(repository)
    tracked=_git_source_bytes(root,'ls-files','-z').split(b'\0')
    untracked=_git_source_bytes(root,'ls-files','--others','--exclude-standard','-z').split(b'\0')
    paths={x.decode('utf-8','surrogateescape').replace('\\','/') for x in tracked+untracked if x}
    if ignored_coverage is not None:
        manifest=json.loads(_declared_ignored_manifest(root,ignored_coverage).decode('utf-8'))
        paths.update(row['path'] for row in manifest if row['kind']!='MISSING')
    return sorted(paths)

def _repository_paths_at_ref(repository: str | pathlib.Path, ref: str) -> list[str]:
    root,_,_=_repository_source_identity(repository)
    raw=_git_source_bytes(root,'ls-tree','-r','--name-only',ref)
    return sorted(x for x in raw.decode('utf-8','surrogateescape').splitlines() if x)

def _require_ancestor(repository: str | pathlib.Path, base: str, head: str) -> None:
    root,_,_=_repository_source_identity(repository)
    proc=_run_source_command(['git','-C',str(root),'merge-base','--is-ancestor',base,head])
    if proc.returncode!=0:
        raise JoyflowError('approved repository base is not an ancestor of the execution result head')

@contextlib.contextmanager
def _detached_validation_worktree(repository: str | pathlib.Path, head: str):
    """Create one disposable, Git-administration-isolated validation checkout.

    A linked ``git worktree`` shares refs, object storage, config and worktree
    registration with the authoritative source repository.  An approved
    validation command could therefore change the source repository while the
    checked-out files, HEAD and Diff remain unchanged.  The Validator instead
    uses a short-lived shared-object clone: source objects are read through an
    alternates file, while every ref, index, log, config or new object written
    by the command belongs only to the disposable clone.  The complete clone
    tree, including its local ``.git`` administration, is sealed by
    ``_repository_validation_snapshot`` before and after replay.
    """
    root,_,_=_repository_source_identity(repository)
    remote=_git_source_bytes(root,'config','--get','remote.origin.url').decode('utf-8','surrogateescape').strip()
    tmp=pathlib.Path(tempfile.mkdtemp(prefix='joyflow-validation-')).resolve()
    try:
        proc=_run_source_command(['git','clone','--shared','--no-checkout','--quiet',str(root),str(tmp)])
        if proc.returncode!=0:
            raise JoyflowError(proc.stderr.decode('utf-8','replace').strip() or 'failed to create isolated validation repository')
        for argv in (
            ['git','-C',str(tmp),'config','remote.origin.url',remote],
            ['git','-C',str(tmp),'config','gc.auto','0'],
            ['git','-C',str(tmp),'config','maintenance.auto','false'],
            ['git','-C',str(tmp),'checkout','--detach','--force',head],
        ):
            step=_run_source_command(argv)
            if step.returncode!=0:
                raise JoyflowError(step.stderr.decode('utf-8','replace').strip() or 'failed to prepare isolated validation repository')
        actual=_git_source_bytes(tmp,'rev-parse','HEAD').decode().strip()
        if actual!=head:
            raise JoyflowError('isolated validation repository is not at the exact lifecycle commit')
        yield tmp
    finally:
        shutil.rmtree(tmp,ignore_errors=True)

def _source_pattern_matches(pattern: str, paths: list[str]) -> list[str]:
    if pattern.endswith('/**'):
        prefix=pattern[:-3].rstrip('/')+'/'
        return [p for p in paths if p.startswith(prefix)]
    return [p for p in paths if p==pattern or p.startswith(pattern.rstrip('/')+'/')]

def _github_source_paths(row: dict[str,Any], repository: str | pathlib.Path) -> list[str]:
    root,_,_=_repository_source_identity(repository)
    if row['object_type']=='PR_DIFF':
        base=row.get('base_ref'); head=row.get('head_ref')
        if not base or not head or head!=row['observed_commit_or_head']:
            raise JoyflowError('PR_DIFF evidence requires exact base_ref and head_ref')
        _git_source_bytes(root,'cat-file','-e',f'{base}^{{commit}}')
        _git_source_bytes(root,'cat-file','-e',f'{head}^{{commit}}')
        _require_ancestor(root,base,head)
        raw=_git_source_bytes(root,'diff','--name-only',base,head)
        return sorted(x for x in raw.decode('utf-8','surrogateescape').splitlines() if x)
    return _repository_paths_at_ref(root,row['observed_commit_or_head'])

def _github_source_capture_payload(row: dict[str,Any], repository: str | pathlib.Path) -> dict[str,Any]:
    root,repo_id,_=_repository_source_identity(repository)
    paths=_github_source_paths(row,root)
    matched={pattern:sorted(_source_pattern_matches(pattern,paths)) for pattern in row['scope']['observed_paths']}
    return {
      'repository_id':repo_id,
      'object_type':row['object_type'],
      'observed_commit_or_head':row['observed_commit_or_head'],
      'base_ref':row.get('base_ref'),
      'head_ref':row.get('head_ref'),
      'object_path':row['scope']['object_path'],
      'observed_paths':copy.deepcopy(row['scope']['observed_paths']),
      'matched_paths':matched,
    }

def verify_github_path_evidence_against_repository(row: dict[str,Any], repository: str | pathlib.Path) -> None:
    root,repo_id,_=_repository_source_identity(repository)
    if row['repository_id']!=repo_id:
        raise JoyflowError('GitHub path evidence source replay is bound to another repository')
    _git_source_bytes(root,'cat-file','-e',f"{row['observed_commit_or_head']}^{{commit}}")
    paths=_github_source_paths(row,root)
    for observed in row['scope']['observed_paths']:
        if not _source_pattern_matches(observed,paths):
            raise JoyflowError(f'GitHub path evidence source replay found no matching path in the declared object: {observed}')
    if row['object_type']=='FILE' and row['scope']['object_path'] not in paths:
        raise JoyflowError('GitHub FILE evidence source replay did not find the exact file')
    replay_sha=hashlib.sha256(canonical_bytes(_github_source_capture_payload(row,root))).hexdigest()
    if row['scope']['raw_object_sha256']!=replay_sha:
        raise JoyflowError('GitHub path evidence raw-object SHA-256 differs from repository replay')

def verify_path_discovery_return_against_repository(row: dict[str,Any], projection: dict[str,Any], repository: str | pathlib.Path) -> None:
    root,repo_id,head=_repository_source_identity(repository)
    if row['repository']['repository_id']!=repo_id or projection['task_anchor']['repository_anchor']['baseline_commit']!=head:
        raise JoyflowError('Path Discovery source replay is bound to another repository or HEAD')
    coverage=_normalize_ignored_coverage(row['ignored_path_coverage'])
    current=_source_worktree_components(root,coverage)
    for phase in ('repository_state_before','repository_state_after'):
        record=row[phase]
        if _state_fingerprint_payload(record)!=current or record['state_fingerprint_sha256']!=digest(current):
            raise JoyflowError(f'{phase} does not match the repository state replayed by the validator')
    paths=_repository_current_paths(root,coverage)
    evidence={r['evidence_id']:r for r in row['evidence_rows']}
    direct_paths={}
    for ev in evidence.values():
        if ev['kind'] not in {'PATH_OBSERVATION','SOURCE_SNAPSHOT_OBSERVATION'}:
            continue
        observed=ev.get('observed_path')
        if not observed or not _source_pattern_matches(observed,paths):
            raise JoyflowError('direct local repository observation was not found in the current repository')
        direct_paths[ev['evidence_id']]=observed
        if ev['kind']=='SOURCE_SNAPSHOT_OBSERVATION':
            data=_git_source_bytes(root,'show',f"{head}:{observed}")
            if hashlib.sha256(data).hexdigest()!=ev.get('source_sha256') or ev.get('raw_output_sha256')!=ev.get('source_sha256'):
                raise JoyflowError('direct source snapshot observation differs from current repository bytes')
    for item in row['confirmed_paths']:
        ev=evidence[item['evidence_ref']]
        if ev.get('observed_path')!=item['path']:
            raise JoyflowError('confirmed path does not match its direct path observation')
    for group,id_key,kind,required_paths in (
      ('candidate_paths','path_id','PATH_CANDIDATE_DERIVATION',lambda x:[x['path']]),
      ('dependency_edges','edge_id','DEPENDENCY_DERIVATION',lambda x:[x['from'],x['to']]),
      ('validation_entries','validation_id','VALIDATION_ENTRY_DERIVATION',lambda x:[x['path']]),
      ('local_only_findings','finding_id','LOCAL_FINDING_DERIVATION',lambda x:list(x['affected_paths'])),
    ):
        for item in row[group]:
            ev=evidence[item['evidence_ref']]
            observed_sources={direct_paths[ref] for ref in ev['source_evidence_refs'] if ref in direct_paths}
            for required in required_paths(item):
                if required not in observed_sources:
                    raise JoyflowError(f'{group} derivation lacks a direct observation for {required}')
    for ev in evidence.values():
        if ev['kind'] in {'PATH_OBSERVATION','SOURCE_SNAPSHOT_OBSERVATION'}:
            observed=ev['observed_path']
            proc=_run_source_command(['git','-C',str(root),'check-ignore','-q','--',observed])
            if proc.returncode==0 and not _coverage_contains_path(coverage,observed):
                raise JoyflowError('ignored path used by discovery is absent from declared ignored coverage')

def verify_projection_path_sources_against_repository(projection: dict[str,Any], repository: str | pathlib.Path, path_return: dict[str,Any] | None=None, path_discovery_projection: dict[str,Any] | None=None, *, require_current_head: bool=False) -> None:
    root,repo_id,head=_repository_source_identity(repository)
    anchor=projection['task_anchor'].get('repository_anchor') or {}
    baseline=anchor.get('baseline_commit')
    if anchor.get('repository_id')!=repo_id:
        raise JoyflowError('execution Projection source replay is bound to another repository')
    _git_source_bytes(root,'cat-file','-e',f'{baseline}^{{commit}}')
    if require_current_head and baseline!=head:
        raise JoyflowError('execution Projection preflight requires the approved baseline as current HEAD')
    path_state=projection.get('repository_evidence',{}).get('path_discovery',{})
    for row in path_state.get('github_path_evidence',[]):
        verify_github_path_evidence_against_repository(row,root)
    final=path_state.get('final_path_decision')
    local_basis=bool(final and any(item['basis_type'] in {'LOCAL_DISCOVERY','COMBINED'} for item in final['allowed_path_items']))
    if local_basis:
        if path_return is None or path_discovery_projection is None:
            raise JoyflowError('local/composed execution Projection replay requires the exact discovery Projection and Path Discovery Return')
        validate_path_discovery_return_structure(path_return,path_discovery_projection)
        verify_path_discovery_return_against_repository(path_return,path_discovery_projection,root)
        source=projection.get('task_object_lifecycle',{}).get('discovery_object',{}).get('discovery_source_object') or {}
        if source.get('discovery_projection_digest')!=path_discovery_projection.get('projection_digest') or source.get('path_discovery_return_digest')!=path_return.get('return_digest'):
            raise JoyflowError('execution lifecycle discovery source does not bind the supplied discovery Projection and Return')
        if source.get('selected_item_ids')!=_selected_discovery_item_ids(final):
            raise JoyflowError('execution lifecycle discovery source does not bind the selected Return items')
        if source.get('source_digest')!=digest(strip_digest(source,'source_digest')):
            raise JoyflowError('execution lifecycle discovery source digest mismatch')
    elif path_return is not None or path_discovery_projection is not None:
        raise JoyflowError('non-local execution Projection must not supply local discovery source objects')
    paths=_repository_current_paths(root)
    for path in projection.get('decision_boundary',{}).get('allowed_paths',[]):
        if path.endswith('/**') and not _source_pattern_matches(path,paths):
            raise JoyflowError(f'approved recursive path has no current repository anchor: {path}')

def _exact_file_snapshot(path: pathlib.Path, *, context: str) -> dict[str,Any]:
    import stat
    path=path.absolute()
    try:
        mode=path.lstat().st_mode
    except FileNotFoundError:
        raise JoyflowError(f'{context} is missing')
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise JoyflowError(f'{context} must be one exact regular file, not a symlink or non-file')
    data=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def _validation_workspace_tree_snapshot(root: pathlib.Path) -> dict[str,Any]:
    """Capture the complete lexical object set beneath one validation root.

    Validation is observation-only.  The snapshot therefore includes every
    directory, regular file, symbolic-link object and other filesystem entry
    under the exact command working directory.  Symbolic links are recorded by
    target text and are never followed.  Access time and modification time are
    intentionally excluded because reading a file may update them without
    changing the consumed object.
    """
    import os, stat
    root=root.absolute()
    try:
        root_mode=root.lstat().st_mode
    except FileNotFoundError as exc:
        raise JoyflowError(f'validation workspace root is missing: {root}') from exc
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise JoyflowError(f'validation workspace root must be one real directory: {root}')
    rows=[]
    stack=[root]
    while stack:
        current=stack.pop()
        try:
            entries=sorted(os.scandir(current),key=lambda entry:entry.name)
        except OSError as exc:
            raise JoyflowError(f'validation workspace cannot be read: {current}: {exc}') from exc
        child_dirs=[]
        for entry in entries:
            path=pathlib.Path(entry.path)
            rel=path.relative_to(root).as_posix()
            try:
                mode=entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise JoyflowError(f'validation workspace object cannot be inspected: {rel}: {exc}') from exc
            permissions=stat.S_IMODE(mode)
            if stat.S_ISLNK(mode):
                target=os.readlink(path)
                data=target.encode('utf-8','surrogateescape')
                rows.append({'path':rel,'kind':'SYMLINK','mode':permissions,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'link_target':target,'target_followed':False})
            elif stat.S_ISREG(mode):
                try:
                    data=path.read_bytes()
                except OSError as exc:
                    raise JoyflowError(f'validation workspace file cannot be read: {rel}: {exc}') from exc
                rows.append({'path':rel,'kind':'FILE','mode':permissions,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            elif stat.S_ISDIR(mode):
                rows.append({'path':rel,'kind':'DIRECTORY','mode':permissions,'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()})
                child_dirs.append(path)
            else:
                rows.append({'path':rel,'kind':'OTHER','mode':permissions,'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()})
        stack.extend(reversed(child_dirs))
    return {'root':str(root),'entry_count':len(rows),'manifest_sha256':digest(rows)}


def _validate_artifact_output_root(output_root: pathlib.Path, output_paths: list[pathlib.Path]) -> dict[str,Any]:
    """Bind one Artifact result to a complete dedicated output namespace.

    The current Artifact lifecycle identifies outputs by artifact_id (the
    direct-child filename).  Therefore the operational output namespace is one
    exact real directory whose complete lexical object set must be precisely
    the supplied regular output files.  Extra files, subdirectories, symbolic
    links and other filesystem objects are not part of the sealed result and
    block validation before any approved command is replayed.
    """
    import os, stat
    root=output_root.absolute()
    try:
        root_mode=root.lstat().st_mode
    except FileNotFoundError as exc:
        raise JoyflowError(f'Artifact output root is missing: {root}') from exc
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise JoyflowError('Artifact output root must be one exact real directory, not a symlink or non-directory')
    if not output_paths:
        raise JoyflowError('validated Artifact result requires the exact complete output Artifact set')
    expected_names=[]
    for path in output_paths:
        path=path.absolute()
        if path.parent!=root:
            raise JoyflowError('every Artifact output must be one direct child of the dedicated output root')
        if path.name in expected_names:
            raise JoyflowError('Artifact output paths must have unique artifact IDs')
        _exact_file_snapshot(path,context=f'Artifact output {path.name}')
        expected_names.append(path.name)
    actual=[]
    try:
        entries=sorted(os.scandir(root),key=lambda entry:entry.name)
    except OSError as exc:
        raise JoyflowError(f'Artifact output root cannot be read: {root}: {exc}') from exc
    for entry in entries:
        try:
            mode=entry.stat(follow_symlinks=False).st_mode
        except OSError as exc:
            raise JoyflowError(f'Artifact output-root object cannot be inspected: {entry.name}: {exc}') from exc
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise JoyflowError('Artifact output root contains an undeclared non-regular object')
        actual.append(entry.name)
    if sorted(actual)!=sorted(expected_names):
        raise JoyflowError('Artifact output root complete object set differs from the supplied output Artifact set')
    snapshot=_validation_workspace_tree_snapshot(root)
    return {'output_root':str(root),'artifact_ids':sorted(expected_names),'workspace_snapshot':snapshot,'namespace_digest':digest({'output_root':str(root),'artifact_ids':sorted(expected_names),'workspace_snapshot':snapshot})}


def _artifact_validation_snapshot(input_artifact: pathlib.Path | None, material_paths: dict[str,pathlib.Path], output_paths: list[pathlib.Path], output_root: pathlib.Path) -> dict[str,Any]:
    rows=[]
    roots=set()
    if input_artifact is not None:
        rows.append({'role':'APPROVED_INPUT_ARTIFACT',**_exact_file_snapshot(input_artifact,context='approved input Artifact')})
        roots.add(input_artifact.parent.absolute())
    for material_id,path in sorted(material_paths.items()):
        rows.append({'role':'APPROVED_SOURCE_MATERIAL','material_id':material_id,**_exact_file_snapshot(path,context=f'approved source material {material_id}')})
        roots.add(path.parent.absolute())
    for path in sorted(output_paths,key=lambda x:(x.name,str(x))):
        rows.append({'role':'EXECUTION_RESULT_ARTIFACT','artifact_id':path.name,**_exact_file_snapshot(path,context=f'execution result Artifact {path.name}')})
    workspace_roots=[_validation_workspace_tree_snapshot(root) for root in sorted(roots,key=str)]
    output_namespace=_validate_artifact_output_root(output_root,output_paths)
    payload={'object_rows':rows,'validation_workspace_roots':workspace_roots,'artifact_output_namespace':output_namespace}
    return {**payload,'snapshot_digest':digest(payload)}


def _repository_validation_snapshot(worktree: pathlib.Path, expected_head: str) -> dict[str,Any]:
    actual=_git_source_bytes(worktree,'rev-parse','HEAD').decode().strip()
    if actual!=expected_head:
        raise JoyflowError('validation worktree moved away from the exact sealed commit')
    index=_git_source_bytes(worktree,'diff','--cached','--binary','--no-ext-diff','--no-textconv')
    tracked=_git_source_bytes(worktree,'diff','--binary','--no-ext-diff','--no-textconv')
    workspace=_validation_workspace_tree_snapshot(worktree)
    return {'head_commit':actual,'index_diff_sha256':hashlib.sha256(index).hexdigest(),'worktree_diff_sha256':hashlib.sha256(tracked).hexdigest(),'validation_workspace_root':workspace}


def _repository_source_state_observation(root: pathlib.Path, phase: str, declared_ignored_paths: list[str]) -> dict[str,Any]:
    head=_git_source_bytes(root,'rev-parse','HEAD').decode().strip()
    index=_git_source_bytes(root,'diff','--cached','--binary','--no-ext-diff','--no-textconv')
    worktree=_git_source_bytes(root,'diff','--binary','--no-ext-diff','--no-textconv')
    tracked=_git_source_bytes(root,'ls-files','-s','-z')
    untracked=[]
    for raw in sorted(x for x in _git_source_bytes(root,'ls-files','--others','--exclude-standard','-z').split(b'\0') if x):
        name=raw.decode('utf-8','surrogateescape').replace('\\','/')
        _,kind,data=_boundary_safe_repository_object(root,name)
        untracked.append({'path':name,'kind':kind,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    ignored=[]
    for name in sorted(declared_ignored_paths):
        _,kind,data=_boundary_safe_repository_object(root,name)
        ignored.append({'path':name,'kind':kind,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    components={'head_commit':head,'index_diff_sha256':hashlib.sha256(index).hexdigest(),'worktree_diff_sha256':hashlib.sha256(worktree).hexdigest(),'tracked_source_set_sha256':hashlib.sha256(tracked).hexdigest(),'untracked_manifest_sha256':digest(untracked),'declared_ignored_coverage_sha256':digest(ignored)}
    return {'capture_phase':phase,**components,'declared_ignored_paths':sorted(declared_ignored_paths),'state_fingerprint_sha256':digest(components)}


def _require_observation_only_snapshot(before: dict[str,Any], after: dict[str,Any], *, context: str) -> None:
    if before!=after:
        raise JoyflowError(f'{context} changed a sealed lifecycle object; return to execution, reseal the result and rerun validation')


def verify_execution_evidence_bundle_against_source(bundle: dict[str,Any], projection: dict[str,Any], *, repository: str | pathlib.Path | None=None, artifact: str | pathlib.Path | None=None, artifact_outputs: list[str | pathlib.Path] | None=None, artifact_output_root: str | pathlib.Path | None=None, replay_tests: bool=True, execution_lifecycle_result: dict[str,Any] | None=None, source_materials: dict[str,str | pathlib.Path] | None=None) -> None:
    if replay_tests is not True:
        raise JoyflowError('operational execution evidence validation cannot skip approved test replay')
    validate_task_object_lifecycle(projection)
    _,captures,_=validate_codex_execution_evidence_bundle_structure(bundle,projection)
    expected=projection['execution_object']; lifecycle=projection['task_object_lifecycle']
    result_head=None; approved_base=None; repo_id=None
    output_paths=[pathlib.Path(x).absolute() for x in (artifact_outputs or [])]
    output_root_path=pathlib.Path(artifact_output_root).absolute() if artifact_output_root is not None else None
    input_artifact_path=None; material_paths: dict[str,pathlib.Path]={}
    if expected['object_type']=='REPOSITORY':
        if repository is None or artifact is not None or source_materials or output_paths or output_root_path is not None:
            raise JoyflowError('repository execution evidence replay requires exactly one repository source')
        root,repo_id,current_source_head=_repository_source_identity(repository)
        approved_base=lifecycle['approved_input_object']['base_commit']
        _git_source_bytes(root,'cat-file','-e',f'{approved_base}^{{commit}}')
        replay=lifecycle['route_type']=='EXISTING_PR_REPLAY'
        if replay and current_source_head!=lifecycle['approved_input_object']['head_commit']:
            raise JoyflowError('existing PR replay source Head moved away from the frozen Head')
        if execution_lifecycle_result and execution_lifecycle_result.get('transition_status')=='RESULT_VALIDATED':
            result_obj=execution_lifecycle_result.get('execution_result_object') or {}
            expected_result_type='VALIDATED_EXISTING_PR_HEAD' if replay else 'REPOSITORY_HEAD'
            if result_obj.get('result_type')!=expected_result_type or result_obj.get('repository_id')!=repo_id or result_obj.get('base_commit')!=approved_base:
                raise JoyflowError('repository lifecycle result is bound to another source object')
            result_head=result_obj.get('head_commit'); _git_source_bytes(root,'cat-file','-e',f'{result_head}^{{commit}}'); _require_ancestor(root,approved_base,result_head)
            if replay and result_head!=lifecycle['approved_input_object']['head_commit']:
                raise JoyflowError('existing PR replay validated a substituted Head')
    else:
        if repository is not None:
            raise JoyflowError('Artifact execution evidence replay cannot use a repository source')
        source_mode=expected['source_mode']
        if source_mode=='EXISTING_ARTIFACT':
            if artifact is None or source_materials:
                raise JoyflowError('existing Artifact replay requires exactly one source Artifact')
            input_artifact_path=pathlib.Path(artifact).absolute(); source_snapshot=_exact_file_snapshot(input_artifact_path,context='approved input Artifact'); data=input_artifact_path.read_bytes()
            if input_artifact_path.name!=expected.get('object_id') or hashlib.sha256(data).hexdigest()!=expected.get('expected_ref_or_sha256'):
                raise JoyflowError('Artifact source replay does not match the approved input Artifact')
            root=input_artifact_path.parent
        elif source_mode=='NEW_ARTIFACT':
            if artifact is not None or not source_materials:
                raise JoyflowError('new Artifact replay requires the exact source-material set and no source Artifact')
            anchor_materials=lifecycle['approved_input_object']['source_materials']
            if set(source_materials)!=set(r['material_id'] for r in anchor_materials):
                raise JoyflowError('supplied source-material IDs differ from the approved set')
            actual=[]
            for row in anchor_materials:
                path=pathlib.Path(source_materials[row['material_id']]).absolute(); _exact_file_snapshot(path,context=f"approved source material {row['material_id']}"); data=path.read_bytes()
                if hashlib.sha256(data).hexdigest()!=row['material_digest']:
                    raise JoyflowError('source material bytes differ from approved digest')
                material_paths[row['material_id']]=path
                actual.append({'material_id':row['material_id'],'material_digest':row['material_digest'],'source_ref':row['source_ref']})
            if _source_material_set_digest(actual)!=expected.get('expected_ref_or_sha256'):
                raise JoyflowError('source-material set differs from the approved execution object')
            root=next(iter(material_paths.values())).parent
        else:
            raise JoyflowError('unknown Artifact source mode')
        if execution_lifecycle_result and execution_lifecycle_result.get('transition_status')=='RESULT_VALIDATED':
            result_obj=execution_lifecycle_result.get('execution_result_object') or {}
            if result_obj.get('result_type')!='ARTIFACT_OUTPUT_SET':
                raise JoyflowError('Artifact lifecycle result is not an output set')
            expected_rows=result_obj.get('outputs',[])
            if result_obj.get('output_set_digest')!=_artifact_output_set_digest(expected_rows):
                raise JoyflowError('Artifact lifecycle result output-set digest mismatch')
            if output_root_path is None:
                raise JoyflowError('validated Artifact result requires one exact dedicated output root')
            supplied=[]
            for path in output_paths:
                _exact_file_snapshot(path,context=f'supplied Artifact output {path.name}')
                data=path.read_bytes(); matches=[r for r in expected_rows if r['artifact_id']==path.name]
                if len(matches)!=1: raise JoyflowError('supplied Artifact output is extra or ambiguously identified')
                row=matches[0]
                if hashlib.sha256(data).hexdigest()!=row['artifact_digest'] or len(data)!=row['bytes']:
                    raise JoyflowError('supplied Artifact output bytes differ from the lifecycle result')
                supplied.append(row)
            if _canonical_artifact_outputs(supplied)!=_canonical_artifact_outputs(expected_rows):
                raise JoyflowError('supplied Artifact outputs are missing, extra or replaced')
            _validate_artifact_output_root(output_root_path,output_paths)
            protected_sources=[p for p in ([input_artifact_path] if input_artifact_path is not None else [])+list(material_paths.values())]
            if any(path.absolute().parent==output_root_path for path in protected_sources):
                raise JoyflowError('Artifact source inputs and source materials must remain outside the dedicated output root')
        elif output_paths or output_root_path is not None:
            raise JoyflowError('blocked Artifact execution cannot supply validated outputs or an output root')

    artifact_candidates=[]
    if input_artifact_path is not None: artifact_candidates.append(input_artifact_path)
    artifact_candidates.extend(output_paths)
    def resolve_artifact_capture(obj: dict[str,Any]) -> pathlib.Path:
        matches=[]
        for candidate in artifact_candidates:
            try:
                _exact_file_snapshot(candidate,context=f'supplied Artifact candidate {candidate.name}')
            except JoyflowError:
                continue
            else:
                data=candidate.read_bytes()
                if candidate.name==obj['object_id'] and hashlib.sha256(data).hexdigest()==obj['ref_or_sha256']:
                    matches.append(candidate)
        if len(matches)!=1: raise JoyflowError('Artifact capture cannot be resolved to one supplied Artifact file')
        return matches[0]
    output_identity={(p.name,hashlib.sha256(p.read_bytes()).hexdigest()):p for p in output_paths}
    test_replay_cache={}
    with contextlib.ExitStack() as stack:
        input_validation_root=root; result_validation_root=root
        if expected['object_type']=='REPOSITORY':
            input_validation_root=stack.enter_context(_detached_validation_worktree(root,approved_base))
            if result_head is not None: result_validation_root=stack.enter_context(_detached_validation_worktree(root,result_head))
            if lifecycle['route_type']=='EXISTING_PR_REPLAY': input_validation_root=result_validation_root
            input_target=result_head if lifecycle['route_type']=='EXISTING_PR_REPLAY' else approved_base
            sealed_input_snapshot=_repository_validation_snapshot(input_validation_root,input_target)
            sealed_result_snapshot=_repository_validation_snapshot(result_validation_root,result_head or approved_base)
        else:
            if output_root_path is None:
                raise JoyflowError('validated Artifact replay requires one exact dedicated output root')
            sealed_artifact_snapshot=_artifact_validation_snapshot(input_artifact_path,material_paths,output_paths,output_root_path)
        def exact_capture_output(capture: dict[str,Any], stdout_bytes: bytes, stderr_bytes: bytes=b'') -> bool:
            return (capture['stdout']==stdout_bytes.decode('utf-8','replace') and capture['stderr']==stderr_bytes.decode('utf-8','replace') and capture['stdout_sha256']==hashlib.sha256(stdout_bytes).hexdigest() and capture['stderr_sha256']==hashlib.sha256(stderr_bytes).hexdigest())
        for capture in captures.values():
            kind=capture['capture_kind']; obs=capture['observation']; obj=capture['observed_object']
            if kind in {'REPOSITORY_HEAD','REPOSITORY_COMMIT','REPOSITORY_STATE','REPOSITORY_FILE','REPOSITORY_DIFF'}:
                if expected['object_type']!='REPOSITORY' or obj.get('object_type')!='REPOSITORY' or obj.get('object_id')!=repo_id:
                    raise JoyflowError('repository capture is bound to another source object')
            if kind=='REPOSITORY_HEAD':
                target_root=result_validation_root if result_head and obj.get('ref_or_sha256')==result_head else root
                actual=_git_source_bytes(target_root,'rev-parse','HEAD').decode().strip(); remote=_git_source_bytes(root,'config','--get','remote.origin.url').decode().strip()
                expected_obs={'repository_id':repo_id,'remote_url':remote,'head_sha':actual}
                if obj.get('ref_or_sha256')!=actual or obs!=expected_obs or not exact_capture_output(capture,(actual+'\n').encode('utf-8')) or capture['exit_code']!=0: raise JoyflowError('repository-head capture differs from the actual checked-out HEAD')
            elif kind=='REPOSITORY_COMMIT':
                actual=_git_source_bytes(root,'rev-parse',f"{obj['ref_or_sha256']}^{{commit}}").decode().strip(); remote=_git_source_bytes(root,'config','--get','remote.origin.url').decode().strip()
                expected_obs={'repository_id':repo_id,'remote_url':remote,'commit_sha':actual,'role':obs.get('role')}
                if obs.get('role') not in {'APPROVED_INPUT','EXECUTION_RESULT'} or obs!=expected_obs or not exact_capture_output(capture,(actual+'\n').encode('utf-8')) or capture['exit_code']!=0: raise JoyflowError('repository-commit capture differs from validator resolution')
                if obs['role']=='APPROVED_INPUT' and actual!=approved_base: raise JoyflowError('approved-input commit capture differs from lifecycle base')
                if obs['role']=='EXECUTION_RESULT' and actual!=result_head: raise JoyflowError('execution-result commit capture differs from lifecycle result head')
            elif kind=='REPOSITORY_STATE':
                expected_obs=_repository_source_state_observation(root,obs['capture_phase'],obs['declared_ignored_paths'])
                expected_stdout=canonical_bytes(expected_obs)+b'\n'
                if obj!={'object_type':'REPOSITORY','source_mode':'EXISTING_PR_HEAD','object_id':repo_id,'ref_or_sha256':expected_obs['head_commit']} or obs!=expected_obs or not exact_capture_output(capture,expected_stdout) or capture['exit_code']!=0:
                    raise JoyflowError('repository-state capture differs from the authoritative frozen PR source')
            elif kind=='ARTIFACT_SHA256':
                path=resolve_artifact_capture(obj); data=path.read_bytes(); expected_obs={'artifact_id':path.name,'artifact_path':str(path),'artifact_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
                if obs!=expected_obs or not exact_capture_output(capture,b'') or capture['exit_code']!=0: raise JoyflowError('artifact-sha256 capture differs from validator replay')
            elif kind=='SOURCE_MATERIAL_SET':
                if expected.get('source_mode')!='NEW_ARTIFACT' or obj!=_return_object_shape(expected): raise JoyflowError('source-material capture is bound to another execution object')
                materials=lifecycle['approved_input_object']['source_materials']; expected_obs={'materials':materials,'source_material_set_digest':_source_material_set_digest(materials)}
                if obs!=expected_obs or not exact_capture_output(capture,(obs['source_material_set_digest']+'\n').encode('utf-8')) or capture['exit_code']!=0: raise JoyflowError('source-material-set capture differs from validator replay')
            elif kind=='REPOSITORY_FILE':
                data=_git_source_bytes(root,'show',f"{obj['ref_or_sha256']}:{obs['path']}"); expected_obs={'path':obs['path'],'file_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
                if obs!=expected_obs or not exact_capture_output(capture,data) or capture['exit_code']!=0: raise JoyflowError('repository-file capture differs from validator replay')
            elif kind=='REPOSITORY_DIFF':
                base=obs['base_ref']; head=obs['head_ref']; _require_ancestor(root,base,head)
                if result_head is not None and (base!=approved_base or head!=result_head): raise JoyflowError('repository diff does not connect the lifecycle approved base to result head')
                diff=_git_source_bytes(root,'diff','--binary',base,head); names=sorted(x for x in _git_source_bytes(root,'diff','--name-only',base,head).decode().splitlines() if x)
                expected_obs={'base_ref':base,'head_ref':head,'changed_paths':names,'diff_sha256':hashlib.sha256(diff).hexdigest()}
                if obs!=expected_obs or not exact_capture_output(capture,diff) or capture['exit_code']!=0: raise JoyflowError('repository-diff capture differs from exact base-to-head replay')
            elif kind=='TEST_COMMAND':
                argv=obs['argv']
                if capture['command']!=_canonical_argv(argv) or obs.get('cwd_scope')!='SOURCE_ROOT': raise JoyflowError('test capture command/cwd differs from canonical approved argv and SOURCE_ROOT')
                if expected['object_type']=='REPOSITORY':
                    if obj.get('object_type')!='REPOSITORY' or obj.get('object_id')!=repo_id: raise JoyflowError('test capture is bound to another repository')
                    is_final=capture['subject_type']=='VALIDATION_CHECK'; replay_root=result_validation_root if is_final else input_validation_root; target_ref=result_head if (is_final or lifecycle['route_type']=='EXISTING_PR_REPLAY') else approved_base
                    if obs.get('target_ref')!=target_ref or obj.get('ref_or_sha256')!=target_ref: raise JoyflowError('test capture is not bound to the correct repository lifecycle target')
                else:
                    is_final=capture['subject_type']=='VALIDATION_CHECK'
                    if is_final:
                        key=(obj.get('object_id'),obj.get('ref_or_sha256'))
                        if key not in output_identity: raise JoyflowError('final Artifact validation must target one exact output, not the source input')
                        replay_root=output_identity[key].parent
                    elif expected['source_mode']=='EXISTING_ARTIFACT':
                        replay_root=resolve_artifact_capture(obj).parent
                    else:
                        if obj!=_return_object_shape(expected): raise JoyflowError('new Artifact preflight test is bound to another source-material set')
                        replay_root=root
                    if obs.get('target_ref')!=obj.get('ref_or_sha256'): raise JoyflowError('Artifact test capture target differs from the exact lifecycle target')
                key=(str(replay_root),*argv); proc=test_replay_cache.get(key)
                if proc is None:
                    proc=_run_source_command(argv,cwd=replay_root); test_replay_cache[key]=proc
                    if expected['object_type']=='REPOSITORY':
                        _require_observation_only_snapshot(sealed_input_snapshot,_repository_validation_snapshot(input_validation_root,input_target),context='approved-input validation')
                        _require_observation_only_snapshot(sealed_result_snapshot,_repository_validation_snapshot(result_validation_root,result_head or approved_base),context='final repository validation')
                    else:
                        _require_observation_only_snapshot(sealed_artifact_snapshot,_artifact_validation_snapshot(input_artifact_path,material_paths,output_paths,output_root_path),context='Artifact final validation')
                if proc.returncode!=capture['exit_code'] or not exact_capture_output(capture,proc.stdout,proc.stderr):
                    raise JoyflowError('test capture differs from exact lifecycle-target command replay')

def load_json(path: str | pathlib.Path) -> Any:
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))

def write_json(path: str | pathlib.Path, value: Any) -> None:
    text=json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if '\r' in text: raise JoyflowError('Joyflow canonical JSON must use LF newlines')
    pathlib.Path(path).write_bytes(text.encode('utf-8'))

_MODEL_CACHE: tuple[str, dict[str, Any]] | None = None
_SCHEMA_CACHE: dict[str, tuple[str, Draft202012Validator]] = {}


def load_model() -> dict[str, Any]:
    global _MODEL_CACHE
    current_sha = file_sha256(MODEL_PATH)
    if _MODEL_CACHE is None or _MODEL_CACHE[0] != current_sha:
        model = yaml.safe_load(MODEL_PATH.read_text(encoding='utf-8'))
        if not isinstance(model, dict):
            raise JoyflowError('mechanical model is not an object')
        _MODEL_CACHE = (current_sha, model)
    return _MODEL_CACHE[1]


def validate_schema(instance: Any, schema_path: pathlib.Path) -> None:
    key = str(schema_path.resolve())
    current_sha = file_sha256(schema_path)
    cached = _SCHEMA_CACHE.get(key)
    if cached is None or cached[0] != current_sha:
        schema = json.loads(schema_path.read_text(encoding='utf-8'))
        cached = (current_sha, Draft202012Validator(schema))
        _SCHEMA_CACHE[key] = cached
    errors = sorted(cached[1].iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        err = errors[0]
        where = '.'.join((str(p) for p in err.absolute_path)) or '<root>'
        raise JoyflowError(f'schema validation failed at {where}: {err.message}')

def strip_digest(value: dict[str, Any], *fields: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    for field in fields:
        result.pop(field, None)
    return result

def require_refs(refs: Iterable[str], registry: dict[str, Any], context: str) -> None:
    missing = sorted(set(refs) - set(registry))
    if missing:
        raise JoyflowError(f'{context} references unknown evidence: {missing}')

def semantic_items(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    fiber = capsule.get('active_fibers', {}).get('semantic')
    return fiber.get('payload', {}).get('semantic_items', []) if fiber else []

def item_map(capsule: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = semantic_items(capsule)
    ids = [r.get('item_id') for r in rows]
    if None in ids or len(ids) != len(set(ids)):
        raise JoyflowError('semantic item IDs must be present and unique')
    return {r['item_id']: r for r in rows}

def all_effects(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in semantic_items(capsule):
        for effect in item.get('effects', []):
            row = copy.deepcopy(effect)
            row['source_item_id'] = item['item_id']
            row['source_meaning_digest'] = item['meaning_digest']
            out.append(row)
    ids = [r.get('effect_id') for r in out]
    if None in ids or len(ids) != len(set(ids)):
        raise JoyflowError('semantic effect IDs must be present and unique')
    return out

def active_material(item: dict[str, Any]) -> bool:
    return item.get('material_class') in {'CURRENT_SLICE', 'GLOBAL_INVARIANT'}

def normalize_markers(values: list[str], allowed: set[str], name: str) -> list[str]:
    if not values:
        raise JoyflowError(f'{name} classification must be explicit')
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise JoyflowError(f'unknown {name}: {unknown}')
    if 'NONE' in values and len(values) != 1:
        raise JoyflowError(f'NONE is exclusive in {name}')
    return sorted(set(values))

def expected_classification(model: dict[str, Any], capsule: dict[str, Any]) -> dict[str, Any]:
    risks: set[str] = set()
    lanes: set[str] = set()
    for item in semantic_items(capsule):
        if not active_material(item):
            continue
        values = item.get('risk_markers', [])
        if values != ['NONE']:
            risks.update(values)
        item_lanes = item.get('domain_lanes', [])
        if item_lanes != ['GENERAL']:
            lanes.update(item_lanes)
    decision = capsule.get('active_fibers', {}).get('decision_boundary', {}).get('payload', {})
    for row in decision.get('technical_decisions', []):
        if row.get('risk_markers') != ['NONE']:
            risks.update(row.get('risk_markers', []))
        if row.get('domain_lanes') != ['GENERAL']:
            lanes.update(row.get('domain_lanes', []))
    return {'risk_markers': sorted(risks) if risks else ['NONE'], 'domain_lanes': sorted(lanes) if lanes else ['GENERAL']}

def expected_boundary_obligations(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = {'MUST_DO': 'MUST_DO', 'MUST_NOT_DO': 'MUST_NOT_DO', 'MUST_PRESERVE': 'MUST_PRESERVE', 'ALLOW_PATH': 'ALLOW_PATH', 'FORBID_PATH': 'FORBID_PATH'}
    rows = []
    for effect in all_effects(capsule):
        if effect['effect_type'] in mapping:
            rows.append({'obligation_id': f"OBL_{effect['effect_id']}", 'effect_id': effect['effect_id'], 'kind': mapping[effect['effect_type']], 'statement': effect['value'], 'source_item_id': effect['source_item_id'], 'source_meaning_digest': effect['source_meaning_digest']})
    return sorted(rows, key=lambda r: r['obligation_id'])

def expected_validation_cases(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for effect in all_effects(capsule):
        if effect['effect_type'] == 'VALIDATE':
            rows.append({'case_id': f"CASE_{effect['effect_id']}", 'effect_id': effect['effect_id'], 'assertion': effect['value'], 'source_item_id': effect['source_item_id'], 'source_meaning_digest': effect['source_meaning_digest'], 'required': True, 'evidence_kind': effect.get('evidence_kind', 'TEST_OR_HUMAN')})
    return sorted(rows, key=lambda r: r['case_id'])

def expected_mechanical_walkthrough(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    obligations = {r['effect_id']: r['obligation_id'] for r in expected_boundary_obligations(capsule)}
    cases = {r['effect_id']: r['case_id'] for r in expected_validation_cases(capsule)}
    rows = []
    for item in semantic_items(capsule):
        if not active_material(item):
            continue
        effects = item.get('effects', [])
        rows.append({'item_id': item['item_id'], 'meaning_digest': item['meaning_digest'], 'effect_ids': [e['effect_id'] for e in effects], 'boundary_obligation_ids': [obligations[e['effect_id']] for e in effects if e['effect_id'] in obligations], 'validation_case_ids': [cases[e['effect_id']] for e in effects if e['effect_id'] in cases], 'user_visible_preview': [e['value'] for e in effects if e['effect_type'] == 'USER_VISIBLE_RESULT'], 'unresolved_execution_details': []})
    return sorted(rows, key=lambda r: r['item_id'])

def expected_risk_controls(capsule: dict[str, Any]) -> set[str]:
    markers = set(capsule['task_classification']['risk_markers'])
    markers.discard('NONE')
    return markers

def glob_prefix(pattern: str) -> str:
    pos = len(pattern)
    for token in ('*', '?', '['):
        idx = pattern.find(token)
        if idx >= 0:
            pos = min(pos, idx)
    return pattern[:pos].rstrip('/')

def paths_overlap(a: str, b: str) -> bool:
    if a == b or fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
        return True
    pa, pb = (glob_prefix(a), glob_prefix(b))
    return bool(pa and pb and (pa == pb or pa.startswith(pb + '/') or pb.startswith(pa + '/')))

def path_is_covered_by_observation(path: str, observed_path: str) -> bool:
    """Return whether a final/derived path stays inside a typed GitHub observation.

    Coverage is directional. An observed directory boundary such as ``runtime/**``
    covers a narrower file or subdirectory, but an observed file never authorizes a
    broader directory boundary.
    """
    if not _valid_repo_path(path) or not _valid_repo_path(observed_path):
        return False
    if observed_path.endswith('/**'):
        observed_prefix=observed_path[:-3].rstrip('/')
        candidate_prefix=path[:-3].rstrip('/') if path.endswith('/**') else path.rstrip('/')
        return candidate_prefix == observed_prefix or candidate_prefix.startswith(observed_prefix + '/')
    return path == observed_path

def validate_semantic_classification_review(capsule: dict[str, Any]) -> None:
    payload = capsule.get('active_fibers', {}).get('semantic', {}).get('payload', {})
    review = payload.get('classification_review')
    if not review or review.get('risk_review_complete') is not True or review.get('domain_review_complete') is not True:
        raise JoyflowError('semantic risk/domain classification review is incomplete')
    if not review.get('reviewer_basis'):
        raise JoyflowError('classification review requires explicit basis')

def validate_exclusions(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    items = item_map(capsule)
    registry = evidence_map(capsule)
    active_ids = {i for i, row in items.items() if active_material(row)}
    strong = {'depends_on', 'required_by', 'affects', 'constrained_by', 'validated_by', 'fails_as', 'conflicts_with', 'preserves'}
    for item in items.values():
        cls = item['material_class']
        if cls in {'SIBLING_SLICE', 'OUT_OF_SCOPE_WITH_PROOF'}:
            proof = item.get('exclusion_proof')
            if not proof:
                raise JoyflowError(f"excluded item lacks proof: {item['item_id']}")
            require_refs(proof.get('evidence_refs', []), registry, f"exclusion proof {item['item_id']}")
            for rel, targets in item.get('relations', {}).items():
                if rel in strong and set(targets) & active_ids:
                    raise JoyflowError(f"excluded item is materially connected to active work: {item['item_id']}")
            for active in active_ids:
                for rel, targets in items[active].get('relations', {}).items():
                    if rel in strong and item['item_id'] in targets:
                        raise JoyflowError(f"active work depends on excluded item: {item['item_id']}")
            independence = proof.get('independence', {})
            required = {'no_shared_state_dependency', 'no_shared_behavior_dependency', 'no_acceptance_dependency', 'no_failure_path_dependency'}
            if set(independence) != required or not all(independence.values()):
                raise JoyflowError(f"exclusion proof independence invalid: {item['item_id']}")
        elif cls == 'SUPERSEDED_WITH_REFERENCE':
            target = item.get('superseded_by')
            if not target or target not in items or (not active_material(items[target])):
                raise JoyflowError(f"superseded item target invalid: {item['item_id']}")
        elif item.get('exclusion_proof'):
            raise JoyflowError(f"active material cannot carry exclusion proof: {item['item_id']}")

def validate_mechanical_walkthrough(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    validation = capsule.get('active_fibers', {}).get('validation')
    if not validation:
        return
    actual = validation['payload'].get('mechanical_walkthrough', [])
    expected = expected_mechanical_walkthrough(capsule)
    if actual != expected:
        raise JoyflowError('mechanical walkthrough is not an exact literal projection of active semantics')
    if any((row.get('unresolved_execution_details') for row in actual)):
        raise JoyflowError('unresolved execution details block the walkthrough')

def validate_repair_extension(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    decision = capsule.get('active_fibers', {}).get('decision_boundary')
    if not decision:
        return
    payload = decision['payload']
    mode = payload.get('mode')
    ext = payload.get('repair_extension')
    if capsule['route_profile'] == 'REPAIR_STANDARD' or mode == 'REPAIR':
        if not ext:
            raise JoyflowError('repair route requires repair_extension')
        required = {'failure_source_refs', 'root_cause', 'source_projection_digest', 'retained_boundary_digest', 'compatibility_verdict'}
        if set(ext) != required or ext['compatibility_verdict'] != 'PASS':
            raise JoyflowError('repair_extension incomplete or incompatible')
        require_refs(ext['failure_source_refs'], evidence_map(capsule), 'repair extension')
    elif ext:
        raise JoyflowError('repair_extension only allowed in repair mode')

def validate_pr_goal_scenario_grounding(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    ctx = capsule.get('task_anchor', {}).get('planning_context')
    if not isinstance(ctx, dict):
        raise JoyflowError('task anchor lacks PR/change-unit planning context')
    registry = evidence_map(capsule)
    parent = ctx.get('parent_goal')
    if parent is not None and not isinstance(parent, str):
        raise JoyflowError('parent goal must be text or null')
    exits = ctx.get('exit_conditions') or []
    if not exits or any(not isinstance(x, str) or not x.strip() for x in exits):
        raise JoyflowError('current change unit requires explicit exit conditions')
    assumptions = ctx.get('material_operating_assumptions') or []
    status_by_basis={'USER_CONFIRMED':'CONFIRMED','REPOSITORY_OBSERVED':'OBSERVED','BRAIN_INFERENCE':'INFERRED'}
    for row in assumptions:
        if row.get('condition_type') not in {'DESCRIPTIVE_CONDITION','PRODUCT_TOLERANCE'}:
            raise JoyflowError('operating assumption condition_type must distinguish description from product tolerance')
        if not row.get('assumption') or not row.get('material_effect') or not row.get('reopen_trigger'):
            raise JoyflowError('material operating assumptions must state effect and reopen trigger')
        basis=row.get('source_basis')
        if basis not in status_by_basis or row.get('epistemic_status')!=status_by_basis[basis]:
            raise JoyflowError('operating assumption source basis / epistemic status mismatch')
        if row['condition_type']=='PRODUCT_TOLERANCE' and basis!='USER_CONFIRMED':
            raise JoyflowError('product tolerance is a USER-owned product tradeoff and cannot be invented by Brain or repository observation')
        refs=row.get('source_refs') or []
        if basis=='USER_CONFIRMED':
            require_relevant_evidence(refs,registry,{'USER_DECISION':{'PRODUCT_DECISION'}},subject_type='OPERATING_ASSUMPTION',subject_id=support_subject_id(row['assumption']),context='user-confirmed operating assumption')
        elif basis=='REPOSITORY_OBSERVED':
            require_relevant_evidence(refs,registry,{'REPOSITORY_EVIDENCE':None},subject_type='OPERATING_ASSUMPTION',subject_id=support_subject_id(row['assumption']),context='repository-observed operating assumption')
        else:
            require_relevant_evidence(refs,registry,{'BRAIN_DERIVATION':{'TECHNICAL_INFERENCE','ROUTE_ANALYSIS','PR_REVIEW','COLD_REVIEW'}},subject_type='OPERATING_ASSUMPTION',subject_id=support_subject_id(row['assumption']),context='Brain-inferred operating assumption')
    prior = ctx.get('relevant_prior_behaviors') or []
    ids = [r.get('behavior_id') for r in prior]
    if None in ids or len(ids) != len(set(ids)):
        raise JoyflowError('relevant prior behavior IDs must be present and unique')
    for row in prior:
        refs = row.get('source_refs') or []
        if not row.get('statement') or not row.get('why_relevant') or not refs:
            raise JoyflowError('relevant prior behavior requires statement, source refs and relevance basis')
        require_relevant_evidence(refs,registry,{'USER_DECISION':{'PRODUCT_DECISION'},'REPOSITORY_EVIDENCE':None,'BRAIN_DERIVATION':{'TECHNICAL_INFERENCE','PR_REVIEW','COLD_REVIEW'}},subject_type='PRIOR_BEHAVIOR',subject_id=row.get('behavior_id'),context=f"prior behavior {row.get('behavior_id')}")
        disposition=row.get('expected_disposition')
        auth_refs=row.get('authorization_refs') or []
        if disposition=='PRESERVE_REQUIRED':
            if auth_refs:
                raise JoyflowError('preserve-required prior behavior must not carry change authorization refs')
        elif disposition in {'CHANGE_AUTHORIZED','SUPERSEDE_AUTHORIZED'}:
            require_relevant_evidence(auth_refs,registry,{'USER_DECISION':{'PRODUCT_DECISION'}},subject_type='PRIOR_BEHAVIOR_DISPOSITION',subject_id=f"{row.get('behavior_id')}:{disposition}",context=f"authorized prior behavior disposition {row.get('behavior_id')}")
        else:
            raise JoyflowError('prior behavior expected disposition invalid')
    # This context is task-local planning input, not a new authority or durable project truth.
    if capsule['task_anchor']['change_scope'] == 'REPOSITORY_CHANGE' and capsule['route_profile'] in {'DEVELOPMENT_LIGHT','DEVELOPMENT_STANDARD','DEVELOPMENT_STRICT','REPAIR_STANDARD'}:
        if parent is None or not parent.strip():
            raise JoyflowError('repository PR work requires a parent product goal')

def _build_current_source_context(capsule: dict[str, Any]) -> dict[str, Any]:
    anchor = capsule.get('task_anchor', {}).get('repository_anchor') or {}
    planning = capsule.get('task_anchor', {}).get('planning_context') or {}
    prior_refs = sorted({ref for row in planning.get('relevant_prior_behaviors', []) for ref in row.get('source_refs', [])})
    repo = capsule.get('active_fibers', {}).get('repository_evidence', {}).get('payload', {})
    decision = capsule.get('active_fibers', {}).get('decision_boundary', {}).get('payload', {})
    reality = decision.get('problem_reality', 'NOT_APPLICABLE')
    if capsule['task_anchor']['change_scope'] != 'REPOSITORY_CHANGE' and capsule['route_profile'] != 'READ_ONLY_DISCOVERY':
        return {'problem_reality':'NOT_APPLICABLE','context_status':'NOT_APPLICABLE','historical_retrieval_refs':prior_refs,'selected_paths':[],'current_product_mutation_paths':[],'review_coverage_paths':[],'impact_coverage':[],'excluded_context':[],'unresolved_questions':[],'expansion_triggers':['MATERIAL_SCOPE_OR_OBJECT_CHANGE'],'source_binding':{'repository_id':None,'baseline_commit':None,'final_path_decision_digest':None}}
    path_state = repo.get('path_discovery', {})
    final = path_state.get('final_path_decision')
    selected = []
    if final:
        selected = sorted({r['path'] for r in final.get('allowed_path_items', [])})
    elif capsule['route_profile'] == 'READ_ONLY_DISCOVERY':
        selected = sorted({r['path'] for r in path_state.get('candidate_paths', []) + path_state.get('confirmed_paths', [])})
    unresolved = list(repo.get('unresolved_repository_questions', []))
    if final: unresolved += list(final.get('unresolved_path_questions', []))
    coverage = repo.get('impact_coverage', [])
    if any(r.get('status') == 'UNRESOLVED' for r in coverage): unresolved.append('IMPACT_COVERAGE_UNRESOLVED')
    if capsule['route_profile'] == 'READ_ONLY_DISCOVERY': status='DISCOVERY_ONLY'
    elif final and path_state.get('final_allowed_paths_status') == 'CONFIRMED' and not unresolved: status='SUFFICIENT'
    else: status='INCOMPLETE_BLOCKED'
    replay=capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY'
    mutation_paths=[] if replay else selected
    review_paths=sorted(anchor.get('review_coverage_paths',[])) if replay else []
    return {'problem_reality':reality,'context_status':status,'historical_retrieval_refs':prior_refs,'selected_paths':mutation_paths,'current_product_mutation_paths':mutation_paths,'review_coverage_paths':review_paths,'impact_coverage':coverage,'excluded_context':repo.get('context_exclusions', []),'unresolved_questions':sorted(set(unresolved)),'expansion_triggers':['CURRENT_COMMIT_CHANGED','NEW_MATERIAL_DEPENDENCY_FOUND','RUNTIME_OR_TEST_CONTRADICTION','OBSERVED_IMPACT_EXCEEDS_EXPECTED'],'source_binding':{'repository_id':anchor.get('repository_id'),'baseline_commit':anchor.get('baseline_commit'),'final_path_decision_digest':final.get('decision_digest') if final else None}}

def validate_current_source_task_grounding(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    decision = capsule.get('active_fibers', {}).get('decision_boundary', {}).get('payload', {})
    reality = decision.get('problem_reality', 'NOT_APPLICABLE')
    allowed={'NOT_APPLICABLE','CHANGE_REQUIRED','PARTIAL_CHANGE_REQUIRED','NO_CHANGE_REQUIRED','CANNOT_DETERMINE_BLOCKED'}
    if reality not in allowed: raise JoyflowError('problem reality outcome invalid')
    if capsule['route_profile']=='REPAIR_STANDARD' and capsule['task_anchor']['change_scope']=='REPOSITORY_CHANGE' and reality=='NOT_APPLICABLE':
        raise JoyflowError('repository repair requires a current problem-reality conclusion')
    if reality in {'NO_CHANGE_REQUIRED','CANNOT_DETERMINE_BLOCKED'} and capsule['task_progress']['stage'] in {'USER_APPROVAL','CODEX_EXECUTION'}:
        raise JoyflowError('no-change or indeterminate repair cannot proceed to mutating execution approval')
    if capsule['task_anchor']['change_scope']=='REPOSITORY_CHANGE':
        ctx=_build_current_source_context(capsule)
        if capsule['task_progress']['stage'] in {'USER_APPROVAL','CODEX_EXECUTION'} and ctx['context_status']!='SUFFICIENT':
            raise JoyflowError('repository mutation requires sufficient current-source context')
        dims={r.get('dimension') for r in ctx['impact_coverage']}
        required={'DIRECT_IMPLEMENTATION','DIRECT_CALLERS','INTERFACES_SCHEMA','DATA_STATE_BOUNDARIES','SHARED_CORE','RELEVANT_TESTS','RUNTIME_CHAIN'}
        if capsule['task_progress']['stage'] in {'USER_APPROVAL','CODEX_EXECUTION'} and dims!=required:
            raise JoyflowError('current-source impact coverage dimensions incomplete')
        if capsule['task_progress']['stage'] in {'USER_APPROVAL','CODEX_EXECUTION'}:
            rows={r['dimension']:r for r in ctx['impact_coverage']}
            if rows['DIRECT_IMPLEMENTATION']['status']!='CHECKED':
                raise JoyflowError('repository mutation requires checked direct implementation impact')
            if any(r['status']=='UNRESOLVED' for r in rows.values()):
                raise JoyflowError('unresolved impact coverage blocks repository mutation')

def validate_repository_anchor(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    profile = model['route_profiles'][capsule['route_profile']]
    anchor = capsule['task_anchor'].get('repository_anchor')
    if profile['requires_repository_binding'] is True and (not anchor):
        raise JoyflowError('route requires repository anchor')
    if capsule['task_anchor']['change_scope'] == 'REPOSITORY_CHANGE':
        operation=capsule['task_anchor'].get('repository_operation')
        if operation not in {'CURRENT_ROUND_REPOSITORY_CHANGE','EXISTING_FROZEN_PR_REPLAY'}:
            raise JoyflowError('repository change requires an exact repository operation')
        decision = capsule['active_fibers']['decision_boundary']['payload']
        binding = decision.get('repository_binding')
        if not anchor or not binding:
            raise JoyflowError('repository change requires anchor and execution binding')
        if binding['repository_id'] != anchor['repository_id'] or binding['expected_base_commit'] != anchor['baseline_commit']:
            raise JoyflowError('repository binding does not match canonical-state anchor')
        if binding['working_branch'] == binding['default_branch']:
            raise JoyflowError('repository change cannot execute on default branch')
        if operation=='EXISTING_FROZEN_PR_REPLAY':
            required={'repository_id','baseline_commit','pr_number','pr_url','base_branch','working_branch','frozen_head_sha','review_coverage_paths'}
            if set(anchor)!=required or not isinstance(anchor.get('pr_number'),int) or anchor['pr_number']<1 or not anchor.get('pr_url') or not anchor.get('frozen_head_sha') or not anchor.get('review_coverage_paths'):
                raise JoyflowError('existing PR replay requires one exact frozen PR anchor')
            if binding['default_branch']!=anchor['base_branch'] or binding['working_branch']!=anchor['working_branch']:
                raise JoyflowError('existing PR replay branches differ from the repository binding')
            if any(not _valid_repo_path(path) for path in anchor['review_coverage_paths']) or len(anchor['review_coverage_paths'])!=len(set(anchor['review_coverage_paths'])):
                raise JoyflowError('existing PR replay review coverage paths are invalid or duplicated')
    elif capsule['task_anchor'].get('repository_operation')!='NOT_APPLICABLE':
        raise JoyflowError('non-repository task cannot carry a repository operation')

def _external_implementation_exists(reference: str) -> bool:
    if "::" not in reference:
        return False
    relative_name, function_name = reference.split("::", 1)
    pure = pathlib.PurePosixPath(relative_name)
    if pure.is_absolute() or ".." in pure.parts or not function_name.isidentifier():
        return False
    target = (ROOT / pathlib.Path(*pure.parts)).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return False
    if not target.is_file() or target.suffix != ".py":
        return False
    try:
        tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    except (OSError, SyntaxError, UnicodeError):
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
        for node in tree.body
    )

def validate_registry_implementation(model: dict[str, Any]) -> None:
    missing = []
    for row in model.get('invariants', []):
        implementation = row['implementation']
        if callable(globals().get(implementation)) or _external_implementation_exists(implementation):
            continue
        missing.append(implementation)
    if missing:
        raise JoyflowError(f'mechanical invariant implementation missing: {sorted(missing)}')

def validate_prompt_round_trip(projection: dict[str, Any], approval_record: dict[str, Any], prompt: str) -> None:
    verify_prompt(projection, approval_record, prompt)

def current_resume_view(capsule: dict[str, Any], projection: dict[str, Any] | None=None) -> dict[str, Any]:
    validate_capsule(capsule, require_projection_ready=False, require_approval=False)
    planning=capsule['task_anchor'].get('planning_context',{})
    review=capsule.get('active_fibers',{}).get('execution_review',{}).get('payload',{})
    cumulative=review.get('cumulative_review',{}) if isinstance(review,dict) else {}
    remaining=[]
    for item in capsule.get('unresolved_blockers',[]):
        remaining.append({'kind':'BLOCKER','value':copy.deepcopy(item)})
    for item in review.get('unresolved_followups',[]) if isinstance(review,dict) else []:
        remaining.append({'kind':'FOLLOWUP','value':copy.deepcopy(item)})
    for item in cumulative.get('residuals',[]) if isinstance(cumulative,dict) else []:
        remaining.append({'kind':'RESIDUAL','value':copy.deepcopy(item)})
    for item in review.get('rework_delta',[]) if isinstance(review,dict) else []:
        remaining.append({'kind':'REWORK_DELTA','value':copy.deepcopy(item)})
    reopen=[]
    for row in planning.get('material_operating_assumptions',[]):
        reopen.append(row['reopen_trigger'])
    if projection is not None:
        validate_schema(projection,PROJECTION_SCHEMA)
        if projection.get('projection_digest')!=digest(projection_payload(projection)):
            raise JoyflowError('resume projection digest mismatch')
        if projection.get('capsule_digest')!=capsule.get('capsule_digest') or projection.get('project_id')!=capsule['task_anchor']['project_id'] or projection.get('task_id')!=capsule['task_anchor']['task_id'] or projection.get('round_id')!=capsule['task_progress']['cycle']:
            raise JoyflowError('resume projection does not bind current capsule/project/task/round')
        if capsule.get('approval_record',{}).get('status') in {'APPROVED_FINAL','AUTHORIZED_READ_ONLY_DISCOVERY'}:
            validate_approval(capsule,projection)
        reopen.extend(projection.get('current_source_context',{}).get('expansion_triggers',[]))
    next_action={
      'INTENT_DISCUSSION':'CLOSE_CURRENT_INTENT_OR_DISCOVER',
      'REPOSITORY_DISCOVERY':'COMPLETE_CURRENT_SOURCE_DISCOVERY',
      'DECISION_CLOSURE':'CLOSE_DECISION_OR_RECORD_NO_CHANGE',
      'USER_APPROVAL':'OBTAIN_OR_RECONFIRM_EXPLICIT_EXECUTION_APPROVAL',
      'CODEX_EXECUTION':'COMPLETE_BOUNDED_EXECUTION_OR_RETURN_BLOCKER',
      'BRAIN_REVIEW':'REVIEW_CURRENT_RETURN_OR_RECLOSE_REMAINING_DELTA',
      'USER_ACCEPTANCE':'COMPLETE_APPLICABLE_USER_ACCEPTANCE',
      'MERGE_DECISION':'OBTAIN_SEPARATE_USER_MERGE_DECISION',
      'CLOSED':'NONE_TASK_CLOSED',
      'BLOCKED':'RESOLVE_RECORDED_BLOCKER_THEN_RECLOSE'}[capsule['task_progress']['stage']]
    if capsule['route_profile']=='READ_ONLY_DISCOVERY' and capsule['task_progress']['stage']=='DECISION_CLOSURE' and _valid_execution_approval_record(capsule,projection):
        next_action='EXECUTE_BOUNDED_READ_ONLY_DISCOVERY'
    if review and review.get('rework_delta'):
        next_action='RECLOSE_RECORDED_REWORK_DELTA'
    source_digests={'capsule_digest':capsule['capsule_digest']}
    if projection is not None:
        source_digests['projection_digest']=projection['projection_digest']
    if review:
        source_digests['execution_review_fiber_digest']=capsule['active_fibers']['execution_review']['fiber_digest']
    return {
      'artifact_type':'CURRENT_RESUME_VIEW','persistence':'DERIVED_VIEW_ONLY',
      'current_exact_object':{
        'project_id':capsule['task_anchor']['project_id'],'task_id':capsule['task_anchor']['task_id'],
        'round_id':capsule['task_progress']['cycle'],'stage':capsule['task_progress']['stage'],
        'repository_anchor':copy.deepcopy(capsule['task_anchor'].get('repository_anchor')),
        'artifact_anchor':copy.deepcopy(capsule['task_anchor'].get('artifact_anchor'))},
      'parent_goal':planning.get('parent_goal'),'current_goal':capsule['task_anchor']['goal'],
      'settled':{
        'desired_result':capsule['task_anchor']['desired_result'],'non_goals':copy.deepcopy(capsule['task_anchor']['non_goals']),
        'material_operating_assumptions':copy.deepcopy(planning.get('material_operating_assumptions',[])),
        'relevant_prior_behaviors':copy.deepcopy(planning.get('relevant_prior_behaviors',[])),
        'exit_conditions':copy.deepcopy(planning.get('exit_conditions',[])),
        'brain_review_verdict':review.get('brain_review_verdict') if review else None,
        'user_acceptance_status':review.get('user_acceptance') if review else None},
      'remaining':remaining,'next_allowed_action':next_action,
      'reopen_conditions':sorted(set(x for x in reopen if isinstance(x,str) and x.strip())),
      'source_digests':source_digests}

def validate_compact_handoff_delta_resume(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    # Resume is downstream of the validated Task Capsule. Never make a derived view
    # a prerequisite for its own source object's validity. This boundary checker is
    # intentionally non-recursive; rendering performs source validation separately.
    if model.get('phase2_extension',{}).get('skill_system') is not False:
        raise JoyflowError('Phase 2D compact handoff cannot depend on a Skill layer')
    if model.get('phase2_extension',{}).get('persistent_new_truth_source') is not False:
        raise JoyflowError('Phase 2D resume cannot introduce a persistent truth source')
    if not isinstance(capsule,dict) or capsule.get('artifact_type')!='FIBERED_TASK_CAPSULE':
        raise JoyflowError('compact handoff/resume boundary requires a Task Capsule source')

def draft_handoff(capsule: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, str]]:
    projection = build_projection(capsule)
    view = render_approval_view(projection)
    binding = approval_binding(projection)
    return (projection, view, binding)

def b64url_encode(value: Any) -> str:
    return base64.urlsafe_b64encode(canonical_bytes(value)).decode('ascii').rstrip('=')

def b64url_decode(text: str) -> Any:
    padding = '=' * (-len(text) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(text + padding).decode('utf-8'))
    except Exception as exc:
        raise JoyflowError('invalid machine envelope') from exc

def compressed_envelope_encode(value: Any) -> str:
    raw=canonical_bytes(value)
    return base64.urlsafe_b64encode(zlib.compress(raw,9)).decode('ascii').rstrip('=')

def compressed_envelope_decode(text: str) -> Any:
    padding='=' * (-len(text) % 4)
    try:
        raw=zlib.decompress(base64.urlsafe_b64decode(text + padding))
        return json.loads(raw.decode('utf-8'))
    except Exception as exc:
        raise JoyflowError('invalid compressed machine envelope') from exc

def visible_json(value: Any) -> str:
    # Keep the model-visible dynamic view compact. Escaping angle brackets prevents
    # task text from forging the surrounding machine marker.
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).replace('<','\u003c').replace('>','\u003e')

def tag(kind: str, path: str, value: Any) -> str:
    return f'<{kind} path="{path}" encoding="base64url">{b64url_encode(value)}</{kind}>'

def set_path(target: dict[str, Any], path: str, value: Any) -> None:
    target[path] = value

def verify_prompt(projection: dict[str, Any], approval_record: dict[str, Any], prompt: str) -> None:
    parsed_projection, parsed_approval, parsed = parse_prompt(prompt)
    if parsed_projection != projection or parsed_approval != approval_record:
        raise JoyflowError('prompt envelope differs from expected artifacts')
    expected = compact_execution_view(projection)
    if parsed != expected:
        raise JoyflowError('prompt compact semantic view differs from projection')
    if approval_record.get('binding') != approval_binding(projection):
        raise JoyflowError('prompt projection is outside the active authorization envelope')
    if prompt.replace('\r\n', '\n') != render_prompt(projection, approval_record):
        raise JoyflowError('prompt bytes differ from deterministic rendering')
SOURCE_FILES = [ROOT / '00_PROJECT_INSTRUCTIONS_BOOTLOADER_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE.md']
SOURCE_FILES += sorted((ROOT / 'project_sources').glob('*.md'))

def source_set_identity() -> dict[str, Any]:
    rows = []
    for path in SOURCE_FILES:
        rows.append({'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': file_sha256(path)})
    value = {'files': rows}
    value['source_set_digest'] = digest(value)
    return value

def build_identity() -> dict[str, Any]:
    assets = {'model_sha256': file_sha256(MODEL_PATH), 'capsule_schema_sha256': file_sha256(CAPSULE_SCHEMA), 'brain_capsule_manifest_schema_sha256': file_sha256(BRAIN_CAPSULE_MANIFEST_SCHEMA), 'projection_schema_sha256': file_sha256(PROJECTION_SCHEMA), 'approval_schema_sha256': file_sha256(APPROVAL_SCHEMA), 'codex_return_schema_sha256': file_sha256(CODEX_RETURN_SCHEMA), 'evidence_bundle_schema_sha256': file_sha256(EVIDENCE_BUNDLE_SCHEMA), 'evidence_transport_receipt_schema_sha256': file_sha256(EVIDENCE_TRANSPORT_RECEIPT_SCHEMA), 'evidence_transport_cleanup_schema_sha256': file_sha256(EVIDENCE_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA), 'current_pr_review_input_transport_schema_sha256': file_sha256(CURRENT_PR_REVIEW_INPUT_TRANSPORT_SCHEMA), 'current_pr_review_transport_cleanup_schema_sha256': file_sha256(CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA), 'path_discovery_return_schema_sha256': file_sha256(PATH_DISCOVERY_RETURN_SCHEMA), 'long_term_structural_projection_schema_sha256': file_sha256(LONG_TERM_STRUCTURAL_PROJECTION_SCHEMA), 'github_path_evidence_schema_sha256': file_sha256(GITHUB_PATH_EVIDENCE_SCHEMA), 'final_path_decision_schema_sha256': file_sha256(FINAL_PATH_DECISION_SCHEMA), 'merge_gate_schema_sha256': file_sha256(MERGE_GATE_SCHEMA), 'completion_pointer_schema_sha256': file_sha256(COMPLETION_POINTER_SCHEMA), 'phase1_review_runtime_sha256': file_sha256(ROOT / 'runtime/joyflow_phase1_review.py'), 'pr_record_schema_sha256': file_sha256(ROOT / 'schemas/pr_record.schema.json'), 'pr_ci_result_schema_sha256': file_sha256(ROOT / 'schemas/pr_ci_result.schema.json'), 'stage_lineage_sha256': file_sha256(ROOT / 'PHASE1_STAGE_LINEAGE.json'), 'phase1_merge_runtime_sha256': file_sha256(ROOT / 'runtime/joyflow_phase1_merge.py'), 'merge_candidate_freeze_schema_sha256': file_sha256(ROOT / 'schemas/merge_candidate_freeze.schema.json'), 'merged_change_projection_schema_sha256': file_sha256(ROOT / 'schemas/merged_change_projection.schema.json'), 'user_merge_authorization_schema_sha256': file_sha256(ROOT / 'schemas/user_merge_authorization.schema.json'), 'phase1_projection_runtime_sha256': file_sha256(ROOT / 'runtime/joyflow_phase1_projection.py'), 'unified_example_generator_sha256': file_sha256(ROOT / 'tools/generate_all_examples.py'), 'old_rule_migration_sha256': file_sha256(ROOT / 'OLD_RULE_MIGRATION.json'), 'migration_verification_registry_sha256': file_sha256(ROOT / 'machine/verification_registry.json'), 'candidate_capability_status_sha256': file_sha256(ROOT / 'CAPABILITY_STATUS.json'), 'migration_claim_validator_sha256': file_sha256(ROOT / 'tools/validate_migration_claims.py'), 'migration_generator_sha256': file_sha256(ROOT / 'tools/generate_old_rule_migration.py'), 'legacy_rule_migration_schema_sha256': file_sha256(ROOT / 'schemas/legacy_rule_migration.schema.json'), 'migration_registry_schema_sha256': file_sha256(ROOT / 'schemas/migration_verification_registry.schema.json'), 'candidate_capability_schema_sha256': file_sha256(ROOT / 'schemas/candidate_capability_status.schema.json'), 'compiler_sha256': file_sha256(pathlib.Path(__file__).resolve()), 'generator_sha256': file_sha256(GENERATOR_PATH)}
    model = load_model()
    identity = {'model_id': model['model_id'], 'model_version': model['model_version'], 'source_set': source_set_identity(), 'assets': assets}
    identity['build_identity_digest'] = digest(identity)
    return identity

def evidence_map(capsule: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = capsule.get('evidence_registry', [])
    ids = [r.get('evidence_id') for r in rows]
    if None in ids or len(ids) != len(set(ids)):
        raise JoyflowError('evidence IDs must be present and unique')
    model = load_model()
    authorities = set(model['evidence_authorities'])
    kinds_by_authority = {k: set(v) for k, v in model['evidence_kinds_by_authority'].items()}
    allowed_roles = {'USER', 'WEB_BRAIN', 'CODEX', 'TOOL'}
    result = {}
    for row in rows:
        authority = row.get('authority')
        kind = row.get('kind')
        if authority not in authorities or kind not in kinds_by_authority.get(authority, set()):
            raise JoyflowError(f"evidence authority/kind mismatch: {row.get('evidence_id')}")
        if row.get('produced_by') not in allowed_roles or not row.get('subject_type') or not row.get('subject_id'):
            raise JoyflowError(f"evidence role/subject incomplete: {row.get('evidence_id')}")
        if not row.get('ref') or not row.get('claim'):
            raise JoyflowError(f"evidence record incomplete: {row.get('evidence_id')}")
        if row.get('claim_digest') != digest(row['claim']):
            raise JoyflowError(f"evidence claim digest mismatch: {row.get('evidence_id')}")
        if authority == 'USER_DECISION' and row['produced_by'] not in {'USER', 'WEB_BRAIN'}:
            raise JoyflowError(f"user decision evidence cannot be produced by {row['produced_by']}")
        if authority == 'BRAIN_DERIVATION' and row['produced_by'] != 'WEB_BRAIN':
            raise JoyflowError('Brain derivation evidence must be recorded by WEB_BRAIN')
        if authority == 'EXECUTION_EVIDENCE' and row['produced_by'] not in {'CODEX', 'TOOL'}:
            raise JoyflowError('execution evidence must be returned by CODEX or TOOL')
        if kind in {'TEST_RESULT', 'PR_CHECK', 'RUNTIME_OUTPUT'} and not row.get('raw_output_ref'):
            raise JoyflowError(f"raw output reference required for {kind}: {row.get('evidence_id')}")
        result[row['evidence_id']] = row
    return result

def require_authority(refs: Iterable[str], registry: dict[str, dict[str, Any]], authority: str, context: str) -> None:
    require_refs(refs, registry, context)
    if not any((registry[r]['authority'] == authority for r in refs)):
        raise JoyflowError(f'{context} requires {authority} evidence')


def require_compatible_evidence(refs: Iterable[str], registry: dict[str, dict[str, Any]], allowed: dict[str, set[str] | None], context: str) -> list[dict[str, Any]]:
    refs=list(refs)
    require_refs(refs, registry, context)
    matched=[]
    for ref in refs:
        row=registry[ref]
        kinds=allowed.get(row['authority'])
        if row['authority'] in allowed and (kinds is None or row['kind'] in kinds):
            matched.append(row)
    if not matched:
        desc={k:(sorted(v) if isinstance(v,set) else None) for k,v in allowed.items()}
        raise JoyflowError(f'{context} lacks compatible evidence: {desc}')
    return matched


def support_subject_id(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise JoyflowError('support subject text must be non-empty')
    return digest(text.strip())


def require_relevant_evidence(refs: Iterable[str], registry: dict[str, dict[str, Any]], allowed: dict[str, set[str] | None], *, subject_type: str, subject_id: str, context: str) -> list[dict[str, Any]]:
    matched=require_compatible_evidence(refs, registry, allowed, context)
    relevant=[row for row in matched if row.get('subject_type')==subject_type and row.get('subject_id')==subject_id]
    if not relevant:
        raise JoyflowError(f'{context} lacks evidence bound to {subject_type}:{subject_id}')
    return relevant

def validate_evidence_authority(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    registry = evidence_map(capsule)
    reqs = model['semantic_status_authority_requirements']
    for item in semantic_items(capsule):
        refs = item.get('provenance_refs', [])
        require_refs(refs, registry, f"semantic item {item['item_id']}")
        status = item['status']
        requirement = reqs[status]
        if item['item_type'] == 'UNKNOWN':
            if status != 'UNRESOLVED':
                raise JoyflowError(f"UNKNOWN item must remain UNRESOLVED: {item['item_id']}")
        if requirement in model['evidence_authorities']:
            require_authority(refs, registry, requirement, f"semantic item {item['item_id']}")
        elif requirement == 'ANY_SOURCE_PLUS_DERIVATION':
            if not refs or not item.get('derivation'):
                raise JoyflowError(f"Brain inference requires source refs and derivation: {item['item_id']}")
        if active_material(item) and status == 'UNRESOLVED':
            raise JoyflowError(f"unresolved active material blocks: {item['item_id']}")

def _valid_repo_path(pattern: str) -> bool:
    if not isinstance(pattern, str) or not pattern or pattern != pattern.strip():
        return False
    if pattern in {'*', '**', './**', '.', './'}:
        return False
    if pattern.startswith(('/', '\\', './')) or re.match(r'^[A-Za-z]:', pattern):
        return False
    if '\\' in pattern or '..' in pathlib.PurePosixPath(pattern).parts:
        return False
    if any(token in pattern for token in ('?', '[', ']', '{', '}')):
        return False
    if '*' not in pattern:
        return True
    if not pattern.endswith('/**') or pattern.count('*') != 2:
        return False
    prefix = pattern[:-3].rstrip('/')
    if not prefix or prefix in {'*', '**'}:
        return False
    segments = prefix.split('/')
    return all(segment and '*' not in segment for segment in segments)

def _allow_paths(capsule: dict[str, Any]) -> list[str]:
    return [r['statement'] for r in expected_boundary_obligations(capsule) if r['kind'] == 'ALLOW_PATH']

def _forbid_paths(capsule: dict[str, Any]) -> list[str]:
    return [r['statement'] for r in expected_boundary_obligations(capsule) if r['kind'] == 'FORBID_PATH']

def validate_digest_chain(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    anchor = capsule['task_anchor']
    if anchor['anchor_digest'] != digest(strip_digest(anchor, 'anchor_digest')):
        raise JoyflowError('task anchor digest mismatch')
    for name, fiber in capsule['active_fibers'].items():
        if fiber['fiber_digest'] != digest(strip_digest(fiber, 'fiber_digest')):
            raise JoyflowError(f'fiber digest mismatch: {name}')

def validate_progress(model: dict[str, Any], capsule: dict[str, Any], previous: dict[str, Any] | None) -> None:
    progress = capsule['task_progress']
    profile = model['route_profiles'][capsule['route_profile']]
    trigger = progress.get('cycle_trigger', 'NONE')
    event = progress.get('transition_event')
    if progress['cycle'] < 1:
        raise JoyflowError('cycle must start at 1')
    if trigger != 'NONE' and trigger not in model['cycle_triggers']:
        raise JoyflowError('unknown cycle trigger')
    if previous is None:
        if progress['cycle'] != 1 or progress.get('parent_capsule_digest') is not None:
            raise JoyflowError('initial capsule must start at cycle 1 without parent')
        if progress.get('previous_stage') is not None:
            raise JoyflowError('initial capsule previous_stage must be null')
        if progress['stage'] != profile['initial_stage']:
            raise JoyflowError(f"initial stage must be {profile['initial_stage']} for route {capsule['route_profile']}")
        if not event or event.get('event_type') != 'CREATE_TASK' or event.get('from_stage') is not None or (event.get('to_stage') != progress['stage']):
            raise JoyflowError('initial capsule requires exact CREATE_TASK event')
        if event.get('changed_anchor_fields') or event.get('removed_fibers'):
            raise JoyflowError('CREATE_TASK cannot report prior-state changes')
        if set(event.get('added_fibers', [])) != set(capsule['active_fibers']):
            raise JoyflowError('CREATE_TASK added_fibers must equal active fibers')
        require_refs(event.get('evidence_refs', []), evidence_map(capsule), 'CREATE_TASK event')
        if not event.get('reason'):
            raise JoyflowError('CREATE_TASK event requires reason')
        return
    if progress.get('parent_capsule_digest') != previous.get('capsule_digest'):
        raise JoyflowError('parent capsule digest mismatch')
    if progress.get('previous_stage') != previous['task_progress']['stage']:
        raise JoyflowError('previous_stage does not match parent capsule')
    old_stage = previous['task_progress']['stage']
    new_stage = progress['stage']
    if new_stage != old_stage and new_stage not in model['stage_transitions'].get(old_stage, []):
        raise JoyflowError(f'illegal stage transition: {old_stage} -> {new_stage}')
    old_cycle = previous['task_progress']['cycle']
    if trigger == 'NONE':
        if progress['cycle'] != old_cycle:
            raise JoyflowError('ordinary progress must not increment cycle')
    elif progress['cycle'] != old_cycle + 1:
        raise JoyflowError('substantive rework must increment cycle exactly once')
    if new_stage != old_stage and (not event):
        raise JoyflowError('stage transition requires transition event')
    if event:
        if event.get('event_type') not in model['transition_event_types'] or event.get('event_type') == 'CREATE_TASK':
            raise JoyflowError('invalid transition event type')
        if event.get('from_stage') != old_stage or event.get('to_stage') != new_stage:
            raise JoyflowError('transition event stage binding mismatch')
        require_refs(event.get('evidence_refs', []), evidence_map(capsule), 'transition event')
        if not event.get('reason'):
            raise JoyflowError('transition event requires reason')
        if trigger != 'NONE' and event.get('event_type') != model['cycle_trigger_event_map'][trigger]:
            raise JoyflowError('cycle trigger and transition event type mismatch')
    elif trigger != 'NONE':
        raise JoyflowError('cycle increment requires transition event')
    old_anchor = strip_digest(previous['task_anchor'], 'anchor_digest')
    new_anchor = strip_digest(capsule['task_anchor'], 'anchor_digest')
    changed_anchor = sorted((k for k in set(old_anchor) | set(new_anchor) if old_anchor.get(k) != new_anchor.get(k)))
    route_changed = capsule['route_profile'] != previous['route_profile']
    declared = sorted((event or {}).get('changed_anchor_fields', []))
    if declared != changed_anchor:
        raise JoyflowError('transition event changed_anchor_fields mismatch')
    if changed_anchor:
        if capsule['task_anchor']['task_version'] != previous['task_anchor']['task_version'] + 1:
            raise JoyflowError('material anchor change requires task_version increment')
        if trigger != 'MATERIAL_SCOPE_CHANGE' or (event or {}).get('event_type') != 'SCOPE_CHANGED':
            raise JoyflowError('material anchor change requires SCOPE_CHANGED rework event')
    elif capsule['task_anchor']['task_version'] != previous['task_anchor']['task_version']:
        raise JoyflowError('task_version changed without anchor change')
    if route_changed:
        old_rank = model['route_rank'].get(previous['route_profile'], 0)
        new_rank = model['route_rank'].get(capsule['route_profile'], 0)
        expected_event = 'ROUTE_DOWNGRADE_APPROVED' if new_rank < old_rank else 'ROUTE_ESCALATED'
        if not event or event.get('event_type') != expected_event:
            raise JoyflowError('route change requires explicit route transition event')
        if new_rank < old_rank:
            if trigger != 'MATERIAL_SCOPE_CHANGE':
                raise JoyflowError('route downgrade requires substantive cycle')
            require_authority(event.get('evidence_refs', []), evidence_map(capsule), 'USER_DECISION', 'route downgrade')

def validate_active_fibers(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    profile = model['route_profiles'][capsule['route_profile']]
    active = set(capsule.get('active_fibers', {}))
    required = set(profile['required_fibers'])
    optional = set(profile['optional_fibers'])
    missing = sorted(required - active)
    extra = sorted(active - required - optional)
    if missing or extra:
        raise JoyflowError(f'active fiber mismatch; missing={missing}, extra={extra}')
    if profile['executable'] and capsule['task_progress']['stage'] in model['execution_review_required_stages'] and ('execution_review' not in active):
        raise JoyflowError('execution_review fiber required at current executable stage')
    for name, fiber in capsule['active_fibers'].items():
        if fiber.get('fiber_type') != name or fiber.get('status') not in model['fiber_statuses']:
            raise JoyflowError(f'invalid active fiber: {name}')

def validate_lineage(model: dict[str, Any], capsule: dict[str, Any], previous: dict[str, Any] | None) -> None:
    if previous is None:
        for name, fiber in capsule['active_fibers'].items():
            if fiber['revision'] != 1 or fiber.get('previous_digest') is not None:
                raise JoyflowError(f'initial fiber lineage invalid: {name}')
        return
    event = capsule['task_progress'].get('transition_event')
    old_fibers = previous.get('active_fibers', {})
    new_fibers = capsule.get('active_fibers', {})
    added = set(new_fibers) - set(old_fibers)
    removed = set(old_fibers) - set(new_fibers)
    changed: set[str] = set()
    for name in set(new_fibers) & set(old_fibers):
        fiber, old = (new_fibers[name], old_fibers[name])
        payload_changed = fiber['payload'] != old['payload'] or fiber['status'] != old['status']
        if payload_changed:
            changed.add(name)
            if fiber['revision'] != old['revision'] + 1 or fiber.get('previous_digest') != old['fiber_digest']:
                raise JoyflowError(f'changed fiber lacks lineage: {name}')
        elif fiber['revision'] != old['revision'] or fiber.get('previous_digest') != old.get('previous_digest'):
            raise JoyflowError(f'unchanged fiber lineage drift: {name}')
    for name in added:
        fiber = new_fibers[name]
        if fiber['revision'] != 1 or fiber.get('previous_digest') is not None:
            raise JoyflowError(f'new fiber lineage invalid: {name}')
    if added or removed or changed:
        if not event:
            raise JoyflowError('fiber changes require transition event')
        if set(event.get('added_fibers', [])) != added or set(event.get('removed_fibers', [])) != removed or set(event.get('changed_fibers', [])) != changed:
            raise JoyflowError('transition event fiber delta mismatch')
        for source in changed | removed:
            for dependent in model['fiber_types'].get(source, {}).get('invalidates_on_change', []):
                if dependent in old_fibers and dependent in new_fibers and (dependent not in changed):
                    raise JoyflowError(f'changed/removed {source} requires dependent update or invalidation: {dependent}')
    elif event and any((event.get(k) for k in ('added_fibers', 'removed_fibers', 'changed_fibers'))):
        raise JoyflowError('transition event declares nonexistent fiber changes')

def validate_materiality(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    registry = evidence_map(capsule)
    allowed_status = set(model['semantic_statuses'])
    allowed_types = set(model['semantic_item_types'])
    allowed_classes = set(model['material_classes'])
    allowed_risks = set(model['risk_markers'])
    allowed_lanes = set(model['domain_lanes'])
    allowed_effects = set(model['effect_types'])
    for item in semantic_items(capsule):
        if item.get('status') not in allowed_status or item.get('item_type') not in allowed_types or item.get('material_class') not in allowed_classes:
            raise JoyflowError(f"invalid semantic item classification: {item.get('item_id')}")
        if item['meaning_digest'] != digest(item['meaning']):
            raise JoyflowError(f"semantic meaning digest mismatch: {item['item_id']}")
        require_refs(item.get('provenance_refs', []), registry, f"semantic item {item['item_id']}")
        normalize_markers(item.get('risk_markers', []), allowed_risks, 'risk markers')
        lanes = item.get('domain_lanes', [])
        if not lanes or set(lanes) - allowed_lanes or ('GENERAL' in lanes and len(lanes) != 1):
            raise JoyflowError(f"invalid domain lane classification: {item['item_id']}")
        for effect in item.get('effects', []):
            if effect.get('effect_type') not in allowed_effects or not effect.get('value'):
                raise JoyflowError(f"invalid semantic effect: {item['item_id']}")
            if effect.get('effect_digest') != digest(strip_digest(effect, 'effect_digest')):
                raise JoyflowError(f"effect digest mismatch: {effect.get('effect_id')}")
    items = item_map(capsule)
    for item in items.values():
        for rel, targets in item.get('relations', {}).items():
            if rel not in model['material_relations']:
                raise JoyflowError(f'unknown material relation: {rel}')
            missing = sorted(set(targets) - set(items))
            if missing:
                raise JoyflowError(f'relation points to unknown items: {missing}')
    required_types = set(model['validation_requirements']['required_material_types'])
    for item in items.values():
        if active_material(item) and item['item_type'] in required_types and (not any((e['effect_type'] == 'VALIDATE' for e in item.get('effects', [])))):
            raise JoyflowError(f"material item lacks validation effect: {item['item_id']}")
    validate_evidence_authority(model, capsule)

def validate_risk_route(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    expected = expected_classification(model, capsule)
    if capsule.get('task_classification') != expected:
        raise JoyflowError(f'task classification must equal material classification union: expected={expected}')
    selected = capsule['route_profile']
    selected_rank = model['route_rank'].get(selected, 0)
    hard_floors=model.get('risk_minimum_route',{})
    contextual=set(model.get('risk_contextual_markers',[]))
    for marker in expected['risk_markers']:
        minimum = hard_floors.get(marker)
        if minimum and selected_rank < model['route_rank'][minimum]:
            raise JoyflowError(f'hard-floor risk marker {marker} requires at least {minimum}')
    for marker, lanes in model.get('risk_required_lanes', {}).items():
        if marker in expected['risk_markers'] and (not set(lanes).issubset(expected['domain_lanes'])):
            raise JoyflowError(f'risk marker {marker} requires domain lanes {lanes}')
    decision = capsule.get('active_fibers', {}).get('decision_boundary', {}).get('payload', {})
    controls = decision.get('risk_controls', [])
    markers = expected_risk_controls(capsule)
    by_marker={row.get('marker'):row for row in controls}
    if markers - set(by_marker):
        raise JoyflowError(f'risk controls missing markers: {sorted(markers - set(by_marker))}')
    registry = evidence_map(capsule)
    depth_rank={'BASIC':1,'STANDARD':2,'STRICT':3,'PROTOCOL':4}
    selected_depth=model['route_profiles'][selected].get('validation_depth','NONE')
    for row in controls:
        marker=row.get('marker')
        if not row.get('statement'):
            raise JoyflowError('risk control statement required')
        require_refs(row.get('evidence_refs', []), registry, f"risk control {row.get('control_id')}")
        if marker in contextual:
            required={'control_id','marker','statement','evidence_refs','failure_mechanism','technical_consequence','recoverability','operating_condition_refs','required_assurance_depth','hard_floor_applied'}
            if set(row)!=required:
                raise JoyflowError(f'contextual risk control {marker} must record consequence/recoverability/reality disposition')
            if not all(isinstance(row.get(k),str) and row[k].strip() for k in ('failure_mechanism','technical_consequence','recoverability')):
                raise JoyflowError(f'contextual risk control {marker} lacks material consequence analysis')
            if row.get('required_assurance_depth') not in {'BASIC','STANDARD','STRICT'}:
                raise JoyflowError(f'contextual risk control {marker} assurance depth invalid')
            if row.get('hard_floor_applied') is not False:
                raise JoyflowError(f'contextual risk control {marker} cannot claim a hard floor')
            assumption_ids={support_subject_id(a['assumption']) for a in capsule['task_anchor']['planning_context'].get('material_operating_assumptions',[])}
            if any(ref not in assumption_ids for ref in row.get('operating_condition_refs',[])):
                raise JoyflowError(f'contextual risk control {marker} cites unknown operating condition')
            if depth_rank.get(selected_depth,0) < depth_rank[row['required_assurance_depth']]:
                raise JoyflowError(f'contextual risk disposition for {marker} requires {row["required_assurance_depth"]} validation depth')
        elif marker in hard_floors:
            # Hard-floor markers may use the compact legacy control shape; the route floor is mechanical.
            pass

def validate_effect_transport(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    decision = capsule.get('active_fibers', {}).get('decision_boundary')
    if decision:
        actual = sorted(decision['payload'].get('boundary_obligations', []), key=lambda r: r['obligation_id'])
        expected = expected_boundary_obligations(capsule)
        if actual != expected:
            raise JoyflowError('decision boundary is not exact semantic-effect projection')
        allowed = [r['statement'] for r in actual if r['kind'] == 'ALLOW_PATH']
        forbidden = [r['statement'] for r in actual if r['kind'] == 'FORBID_PATH']
        if any((not _valid_repo_path(p) for p in allowed + forbidden)):
            raise JoyflowError('invalid repository-relative path boundary')
        conflicts = [(a, b) for a in allowed for b in forbidden if paths_overlap(a, b)]
        if conflicts:
            raise JoyflowError(f'allowed/forbidden path contradiction: {conflicts}')
    validation = capsule.get('active_fibers', {}).get('validation')
    if validation:
        actual_cases = sorted(validation['payload'].get('acceptance_cases', []), key=lambda r: r['case_id'])
        expected_cases = expected_validation_cases(capsule)
        if actual_cases != expected_cases:
            raise JoyflowError('validation cases are not exact semantic-effect projection')

def _required_fact_slots(model: dict[str, Any], capsule: dict[str, Any]) -> list[str]:
    profile = model['route_profiles'][capsule['route_profile']]
    if capsule['route_profile'] == 'PROTOCOL_CHANGE' and capsule['task_anchor']['change_scope'] == 'REPOSITORY_CHANGE':
        return profile.get('required_repository_fact_slots_when_repository_change', [])
    return profile.get('required_repository_fact_slots', [])

def _canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode('utf-8')

def _github_scope_payload(row: dict[str, Any]) -> dict[str, Any]:
    scope=row['scope']
    return {
        'scope_type':scope['scope_type'],
        'object_path':scope['object_path'],
        'observed_paths':sorted(scope['observed_paths']),
        'observed_paths_digest':scope['observed_paths_digest'],
        'raw_object_sha256':scope['raw_object_sha256'],
        'base_ref':row.get('base_ref'),
        'head_ref':row.get('head_ref'),
    }

def _github_scope_claim(row: dict[str, Any]) -> str:
    return 'GITHUB_PATH_SCOPE:'+_canonical_text({
        'object_type':row['object_type'],
        'object_ref':row['object_ref'],
        'observed_commit_or_head':row['observed_commit_or_head'],
        'base_ref':row.get('base_ref'),
        'head_ref':row.get('head_ref'),
        'scope_digest':row['scope']['scope_digest'],
        'raw_object_sha256':row['scope']['raw_object_sha256'],
    })

def _state_fingerprint_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {k:row[k] for k in ('head_commit','index_diff_sha256','worktree_diff_sha256','untracked_manifest_sha256','declared_ignored_manifest_sha256')}

def _capture_record_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        'capture_id':row['capture_id'],
        'capture_phase':row['capture_phase'],
        'evidence_ref':row['evidence_ref'],
        'state_fingerprint_sha256':row['state_fingerprint_sha256'],
    }

def _git_state_claim(row: dict[str, Any]) -> str:
    return 'GIT_STATE_FINGERPRINT:'+_canonical_text({
        'capture_id':row['capture_id'],
        'capture_phase':row['capture_phase'],
        **_state_fingerprint_payload(row),
        'state_fingerprint_sha256':row['state_fingerprint_sha256'],
        'capture_record_digest':row['capture_record_digest'],
    })

def _path_observation_claim(observation_id: str, path: str) -> str:
    return 'PATH_OBSERVATION:'+_canonical_text({'observation_id':observation_id,'path':path})

def _source_snapshot_claim(observation_id: str, path: str, source_sha256: str) -> str:
    return 'SOURCE_SNAPSHOT_OBSERVATION:'+_canonical_text({'observation_id':observation_id,'path':path,'source_sha256':source_sha256})

def _structural_goal_binding(projection: dict[str, Any]) -> str:
    anchor=projection.get('task_anchor',{})
    return digest({'goal':anchor.get('goal'),'desired_result':anchor.get('desired_result'),'non_goals':anchor.get('non_goals',[])})


def _structural_frame_payload(frame: dict[str, Any]) -> dict[str, Any]:
    return {k:frame[k] for k in ('owner','required','question_id','statement','materiality_basis','goal_binding_digest','required_dimensions','protected_product_semantics','non_goals','discovery_scope_seed')}

def _structural_frame_digest(frame: dict[str, Any]) -> str:
    return digest(_structural_frame_payload(frame))

def _brain_architecture_disposition_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {k:row[k] for k in ('owner','source_structural_return_digest','source_question_id','source_route_id','disposition','review_basis')}

def _validate_structural_frame(frame: dict[str, Any] | None, *, goal_binding_digest: str) -> None:
    if frame is None:
        return
    required={'owner','required','question_id','statement','materiality_basis','goal_binding_digest','required_dimensions','protected_product_semantics','non_goals','discovery_scope_seed','frame_digest'}
    if set(frame)!=required or frame['owner']!='WEB_BRAIN' or frame['required'] is not True:
        raise JoyflowError('structural decision frame shape/authority mismatch')
    if frame['goal_binding_digest']!=goal_binding_digest or not frame['question_id'] or not frame['statement'] or not frame['materiality_basis'] or not frame['required_dimensions']:
        raise JoyflowError('structural decision frame is not bound to the current task goal/question')
    if frame['frame_digest']!=_structural_frame_digest(frame):
        raise JoyflowError('structural decision frame digest mismatch')

def _validate_brain_architecture_disposition(row: dict[str, Any] | None, frame: dict[str, Any] | None) -> None:
    if row is None:
        return
    required={'owner','source_structural_return_digest','source_question_id','source_route_id','disposition','review_basis','disposition_digest'}
    if set(row)!=required or row['owner']!='WEB_BRAIN' or row['disposition'] not in {'ACCEPT','REWORK','USER_DECISION_REQUIRED'} or not row['review_basis']:
        raise JoyflowError('Brain architecture disposition shape/authority mismatch')
    if frame is None or row['source_question_id']!=frame['question_id']:
        raise JoyflowError('Brain architecture disposition is bound to another structural question')
    if row['disposition_digest']!=digest(_brain_architecture_disposition_payload(row)):
        raise JoyflowError('Brain architecture disposition digest mismatch')

def _local_item_claim(kind: str, row: dict[str, Any]) -> str:
    if kind=='PATH_CANDIDATE_DERIVATION':
        payload={k:row[k] for k in ('path_id','path','why_relevant','confidence')}
    elif kind=='DEPENDENCY_DERIVATION':
        payload={k:row[k] for k in ('edge_id','from','to','relation')}
    elif kind=='VALIDATION_ENTRY_DERIVATION':
        payload={k:row[k] for k in ('validation_id','path','command')}
    elif kind=='LOCAL_FINDING_DERIVATION':
        payload={'finding_id':row['finding_id'],'finding':row['finding'],'affected_paths':sorted(row['affected_paths'])}
    elif kind=='STRUCTURAL_RELATION_DERIVATION':
        payload={k:row[k] for k in ('relation_id','relation_type','subject','source','semantic_claim','materiality')}
        payload['basis_evidence_refs']=sorted(row['basis_evidence_refs'])
    elif kind=='ARCHITECTURE_ROUTE_DERIVATION':
        payload={k:row[k] for k in ('route_id','summary')}
        payload['advantages']=sorted(row['advantages']); payload['known_costs']=sorted(row['known_costs']); payload['known_risks']=sorted(row['known_risks']); payload['evidence_refs']=sorted(row['evidence_refs'])
    else:
        raise JoyflowError(f'unsupported local discovery derivation kind: {kind}')
    return kind+':'+_canonical_text(payload)

def validate_worktree_fingerprint(row: dict[str, Any], evidence: dict[str, Any], *, expected_phase: str) -> None:
    required={'capture_id','capture_phase','head_commit','index_diff_sha256','worktree_diff_sha256','untracked_manifest_sha256','declared_ignored_manifest_sha256','evidence_ref','state_fingerprint_sha256','capture_record_digest'}
    if set(row) != required or row['capture_phase']!=expected_phase:
        raise JoyflowError('worktree fingerprint shape or phase mismatch')
    for key in ('index_diff_sha256','worktree_diff_sha256','untracked_manifest_sha256','declared_ignored_manifest_sha256'):
        if not re.fullmatch(r'[0-9a-f]{64}', row[key]):
            raise JoyflowError('worktree fingerprint component is not a SHA-256')
    if row['state_fingerprint_sha256'] != digest(_state_fingerprint_payload(row)):
        raise JoyflowError('worktree state fingerprint digest mismatch')
    if row['capture_record_digest'] != digest(_capture_record_payload(row)):
        raise JoyflowError('worktree capture record digest mismatch')
    ev=evidence.get(row['evidence_ref'])
    if not ev or ev.get('kind')!='GIT_STATE_FINGERPRINT' or ev.get('subject_type')!='PATH_DISCOVERY_CAPTURE' or ev.get('subject_id')!=row['capture_id']:
        raise JoyflowError('worktree fingerprint lacks exact typed capture evidence')
    if ev.get('claim')!=_git_state_claim(row) or ev.get('claim_digest')!=digest(ev.get('claim')):
        raise JoyflowError('worktree fingerprint evidence claim does not bind the exact capture')
    if not re.fullmatch(r'[0-9a-f]{64}',ev.get('raw_output_sha256','')) or not ev.get('raw_output_ref'):
        raise JoyflowError('worktree fingerprint evidence lacks raw capture binding')

def validate_github_path_evidence(row: dict[str, Any], *, repository_id: str, baseline_commit: str, registry: dict[str, Any]) -> None:
    validate_schema(row, GITHUB_PATH_EVIDENCE_SCHEMA)
    if row['evidence_digest'] != digest(strip_digest(row,'evidence_digest')):
        raise JoyflowError('GitHub path evidence digest mismatch')
    if row['repository_id'] != repository_id or row['observed_commit_or_head'] != baseline_commit:
        raise JoyflowError('GitHub path evidence is bound to another repository object')
    if row['object_ref'] != f"github:{repository_id}@{baseline_commit}":
        raise JoyflowError('GitHub path evidence object_ref does not bind the current repository ref')
    if row['object_type']=='PR_DIFF':
        if not row.get('base_ref') or row.get('head_ref')!=baseline_commit:
            raise JoyflowError('PR_DIFF GitHub evidence requires exact base_ref and current head_ref')
        if row['base_ref']==row['head_ref']:
            raise JoyflowError('PR_DIFF GitHub evidence requires distinct base and head refs')
    elif row.get('base_ref') is not None or row.get('head_ref') is not None:
        raise JoyflowError('non-PR_DIFF GitHub evidence cannot carry diff bounds')
    scope=row['scope']; observed=scope['observed_paths']
    if any(not _valid_repo_path(path) for path in observed):
        raise JoyflowError('GitHub path evidence contains an invalid repository path')
    if scope['observed_paths_digest']!=digest(sorted(observed)) or scope['scope_digest']!=digest(_github_scope_payload(row)):
        raise JoyflowError('GitHub path evidence scope digest mismatch')
    if row['object_type']=='FILE':
        if scope['scope_type']!='EXACT_FILE' or scope['object_path'] is None or observed!=[scope['object_path']] or scope['object_path'].endswith('/**'):
            raise JoyflowError('FILE GitHub evidence must bind one exact file and cannot authorize a directory')
    else:
        if scope['scope_type']!='PATH_SET' or scope['object_path'] is not None:
            raise JoyflowError('non-FILE GitHub evidence must use an explicit path-set scope')
    source=registry.get(row['evidence_id'])
    kind_by_object={'REPOSITORY_TREE':'GITHUB_TREE_SNAPSHOT','FILE':'GITHUB_FILE','COMMIT':'GITHUB_COMMIT_PATHS','PR_DIFF':'GITHUB_PR_DIFF_PATHS'}
    if not source or source.get('authority')!='REPOSITORY_EVIDENCE' or source.get('kind')!=kind_by_object[row['object_type']]:
        raise JoyflowError('typed GitHub path evidence is not backed by compatible repository evidence')
    if source.get('ref')!=row['raw_evidence_ref'] or source.get('raw_output_ref')!=row['raw_evidence_ref'] or source.get('raw_output_sha256')!=scope['raw_object_sha256'] or source.get('subject_type')!='GITHUB_OBJECT' or source.get('subject_id')!=row['object_ref']:
        raise JoyflowError('typed GitHub path evidence does not match its exact GitHub object evidence record')
    if source.get('claim')!=_github_scope_claim(row) or source.get('claim_digest')!=digest(source.get('claim')):
        raise JoyflowError('typed GitHub path evidence scope is not bound to the backing evidence claim')
    if source.get('produced_by') not in {'WEB_BRAIN','TOOL'}:
        raise JoyflowError('GitHub path evidence must be observed by the Web Brain or a read-only tool')

def _return_maps(path_return: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        'paths':{x['path_id']:x for x in path_return['confirmed_paths']},
        'dependencies':{x['edge_id']:x for x in path_return['dependency_edges']},
        'validations':{x['validation_id']:x for x in path_return['validation_entries']},
        'findings':{x['finding_id']:x for x in path_return['local_only_findings']},
    }

def _require_ids(ids: list[str], rows: dict[str, Any], context: str) -> list[dict[str, Any]]:
    missing=[item_id for item_id in ids if item_id not in rows]
    if missing:
        raise JoyflowError(f'{context} references missing current Return items: {missing}')
    return [rows[item_id] for item_id in ids]

def validate_final_path_decision(row: dict[str, Any], capsule: dict[str, Any], *, expected_path_return_digest: str | None = None, path_return: dict[str, Any] | None = None) -> None:
    validate_schema(row, FINAL_PATH_DECISION_SCHEMA)
    if row['decision_digest'] != digest(strip_digest(row,'decision_digest')):
        raise JoyflowError('Final Path Decision digest mismatch')
    anchor=capsule['task_anchor'].get('repository_anchor') or {}
    expected={'project_id':capsule['task_anchor']['project_id'],'task_id':capsule['task_anchor']['task_id'],'round_id':capsule['task_progress']['cycle'],'repository_id':anchor.get('repository_id'),'baseline_commit':anchor.get('baseline_commit')}
    if any(row.get(k)!=v for k,v in expected.items()):
        raise JoyflowError('Final Path Decision is bound to another current object')
    if row['owner']!='WEB_BRAIN' or row['unresolved_path_questions']:
        raise JoyflowError('Final Path Decision requires WEB_BRAIN ownership and no unresolved path questions')
    path_state=capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{})
    frame=path_state.get('structural_decision_frame'); disposition=path_state.get('brain_architecture_disposition')
    sb=row['structural_closure_binding']
    if frame is None:
        if sb!={'status':'NOT_REQUIRED','source_structural_return_digest':None,'structural_question_id':None,'source_route_id':None,'brain_disposition_digest':None}:
            raise JoyflowError('non-structural Final Path Decision cannot carry a structural closure claim')
    else:
        if not disposition or disposition.get('disposition')!='ACCEPT':
            raise JoyflowError('structural Final Path Decision requires an accepted Brain architecture disposition')
        expected_sb={'status':'CLOSED','source_structural_return_digest':disposition['source_structural_return_digest'],'structural_question_id':frame['question_id'],'source_route_id':disposition['source_route_id'],'brain_disposition_digest':disposition['disposition_digest']}
        if sb!=expected_sb:
            raise JoyflowError('Final Path Decision does not bind the exact accepted structural closure')
        if expected_path_return_digest and sb['source_structural_return_digest']!=expected_path_return_digest:
            raise JoyflowError('Final Path structural closure is bound to another Path Discovery Return')
        if path_return is not None:
            structural=path_return['structural_discovery']
            if structural['task_structural_projection']['status']!='CLOSED' or structural['unresolved_structural_questions'] or structural['recommended_route_id']!=sb['source_route_id'] or structural['architecture_question']['question_id']!=sb['structural_question_id']:
                raise JoyflowError('Final Path cannot consume an incomplete or different structural discovery result')

    registry=evidence_map(capsule)
    github_rows={r['evidence_id']:r for r in path_state.get('github_path_evidence',[]) if isinstance(r,dict) and r.get('evidence_id')}
    decision_paths=[]
    return_maps=_return_maps(path_return) if path_return is not None else None

    def require_current_github_sources(source_ids: list[str], context: str) -> list[str]:
        if not source_ids:
            raise JoyflowError(f'{context} requires current typed GitHub path evidence')
        missing=[source_id for source_id in source_ids if source_id not in github_rows]
        if missing:
            raise JoyflowError(f'{context} references non-path or non-current GitHub evidence: {missing}')
        observed=[]
        for source_id in source_ids:
            observed.extend(github_rows[source_id]['scope']['observed_paths'])
        return observed

    for item in row['allowed_path_items']:
        path=item['path']; decision_paths.append(path)
        if not _valid_repo_path(path):
            raise JoyflowError('Final Path Decision contains invalid repository path')
        basis=item['basis_type']; github_source_ids=item['source_github_path_evidence_ids']; derived_from_paths=item['derived_from_paths']
        supporting_refs=item['supporting_evidence_refs']; ret=item['source_path_discovery_return_digest']
        local_path_ids=item['source_return_path_ids']; local_dep_ids=item['source_return_dependency_ids']; local_validation_ids=item['source_return_validation_ids']; local_finding_ids=item['source_return_finding_ids']
        require_refs(supporting_refs,registry,'Final Path Decision supporting evidence')
        if set(github_source_ids) & set(supporting_refs):
            raise JoyflowError('typed GitHub path sources and supporting evidence must use separate fields')
        if any(not _valid_repo_path(source_path) for source_path in derived_from_paths):
            raise JoyflowError('Final Path Decision contains an invalid derived-from path')

        observed=[]
        if basis=='GITHUB_CONFIRMED':
            observed=require_current_github_sources(github_source_ids,'GitHub-confirmed final path')
            if derived_from_paths or not any(path_is_covered_by_observation(path,p) for p in observed):
                raise JoyflowError('GitHub-confirmed final path is not directly covered by current typed GitHub evidence')
        elif basis=='GITHUB_DERIVED':
            observed=require_current_github_sources(github_source_ids,'GitHub-derived final path')
            if not derived_from_paths:
                raise JoyflowError('GitHub-derived final path requires explicit observed source paths')
            if any(not any(path_is_covered_by_observation(source_path,p) for p in observed) for source_path in derived_from_paths):
                raise JoyflowError('GitHub-derived final path starts from a path not covered by current typed GitHub evidence')
        elif basis=='COMBINED':
            observed=require_current_github_sources(github_source_ids,'combined final path')
            if not derived_from_paths or any(not any(path_is_covered_by_observation(source_path,p) for p in observed) for source_path in derived_from_paths):
                raise JoyflowError('combined final path lacks covered GitHub source paths')
        elif basis=='LOCAL_DISCOVERY':
            if github_source_ids or derived_from_paths:
                raise JoyflowError('local-only final path may not claim GitHub path sources')
        elif basis=='BRAIN_TASK_DERIVATION':
            if github_source_ids or derived_from_paths:
                raise JoyflowError('task-derived final path may not masquerade as GitHub path evidence')
            if not supporting_refs or not any(registry[ref]['authority']=='BRAIN_DERIVATION' for ref in supporting_refs):
                raise JoyflowError('Brain-derived final path requires an explicit Brain derivation evidence record')

        local_fields=local_path_ids+local_dep_ids+local_validation_ids+local_finding_ids
        if basis in {'LOCAL_DISCOVERY','COMBINED'}:
            if not expected_path_return_digest or ret != expected_path_return_digest or not local_path_ids:
                raise JoyflowError('local/composed final path must bind the exact Return and at least one confirmed local path item')
            if path_return is not None:
                if path_return['return_digest']!=ret or path_return['unresolved_questions']:
                    raise JoyflowError('final local path cannot use a mismatched or unresolved Path Discovery Return')
                selected_paths=_require_ids(local_path_ids,return_maps['paths'],'Final Path Decision local path')
                if not any(path_is_covered_by_observation(path,src['path']) for src in selected_paths):
                    raise JoyflowError('final local path is not covered by the selected confirmed Return paths')
                selected_deps=_require_ids(local_dep_ids,return_maps['dependencies'],'Final Path Decision dependency')
                selected_vals=_require_ids(local_validation_ids,return_maps['validations'],'Final Path Decision validation')
                selected_findings=_require_ids(local_finding_ids,return_maps['findings'],'Final Path Decision finding')
                relevant=[path]+[src['path'] for src in selected_paths]
                for edge in selected_deps:
                    if not any(paths_overlap(edge['from'],r) or paths_overlap(edge['to'],r) for r in relevant):
                        raise JoyflowError('selected local dependency does not concern the final path')
                for val in selected_vals:
                    if not any(paths_overlap(val['path'],r) for r in relevant):
                        raise JoyflowError('selected local validation entry does not concern the final path')
                for finding in selected_findings:
                    if not any(paths_overlap(p,r) for p in finding['affected_paths'] for r in relevant):
                        raise JoyflowError('selected local finding does not concern the final path')
        else:
            if ret is not None or local_fields:
                raise JoyflowError('non-local final path may not claim Path Discovery Return items')
        if not item['derivation_summary']:
            raise JoyflowError('Final Path Decision requires an explicit bounded derivation summary')

    allowed=_allow_paths(capsule)
    if sorted(decision_paths)!=sorted(allowed):
        raise JoyflowError('Final Path Decision paths differ from the user-facing allowed-path obligations')

def validate_path_discovery_state(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    fiber = capsule.get('active_fibers', {}).get('repository_evidence')
    if not fiber:
        return
    state = fiber.get('payload', {}).get('path_discovery')
    if not isinstance(state, dict):
        raise JoyflowError('repository evidence requires bounded path_discovery state')
    required = {'github_discovery_status','github_ref','github_path_evidence','confirmed_paths','candidate_paths','local_discovery_required','local_discovery_reason','local_discovery_status','local_discovery_binding','path_discovery_source','final_boundary_owner','final_allowed_paths_status','final_path_decision','structural_decision_frame','brain_architecture_disposition'}
    if set(state) != required:
        raise JoyflowError('path_discovery state contains missing or unbounded fields')
    if state['github_discovery_status'] not in model['github_discovery_statuses']:
        raise JoyflowError('invalid GitHub discovery status')
    anchor=capsule['task_anchor'].get('repository_anchor') or {}
    repository_id=anchor.get('repository_id'); baseline=anchor.get('baseline_commit'); expected_ref=f'github:{repository_id}@{baseline}'
    if state.get('github_ref') != expected_ref:
        raise JoyflowError('GitHub-first path discovery must bind the current repository baseline')
    github_rows={row['evidence_id']:row for row in state['github_path_evidence']}
    if len(github_rows)!=len(state['github_path_evidence']):
        raise JoyflowError('GitHub path evidence IDs must be unique')
    for row in github_rows.values():
        validate_github_path_evidence(row,repository_id=repository_id,baseline_commit=baseline,registry=evidence_map(capsule))
    if state['local_discovery_status'] not in model['local_discovery_statuses'] or state['path_discovery_source'] not in model['path_discovery_sources']:
        raise JoyflowError('invalid local/path discovery state')
    if state['final_boundary_owner'] != 'WEB_BRAIN':
        raise JoyflowError('final path boundary must be owned by WEB_BRAIN')
    if state['final_allowed_paths_status'] not in model['final_allowed_paths_statuses']:
        raise JoyflowError('invalid final allowed-path status')
    frame=state.get('structural_decision_frame')
    _validate_structural_frame(frame,goal_binding_digest=digest({'goal':capsule['task_anchor'].get('goal'),'desired_result':capsule['task_anchor'].get('desired_result'),'non_goals':capsule['task_anchor'].get('non_goals',[])}))
    disposition=state.get('brain_architecture_disposition')
    _validate_brain_architecture_disposition(disposition,frame)
    if state.get('local_discovery_reason')=='MATERIAL_ARCHITECTURE_UNCERTAINTY' and frame is None:
        raise JoyflowError('material architecture uncertainty requires a Brain-owned structural decision frame')
    if frame is None and disposition is not None:
        raise JoyflowError('non-structural path state cannot carry a Brain architecture disposition')
    registry=evidence_map(capsule)
    for row in state['confirmed_paths']:
        if not isinstance(row, dict) or set(row) != {'path','role','evidence_ref'} or not _valid_repo_path(row['path']):
            raise JoyflowError('invalid GitHub-confirmed path row')
        if row['evidence_ref'] not in github_rows or row['path'] not in github_rows[row['evidence_ref']]['scope']['observed_paths']:
            raise JoyflowError('GitHub-confirmed path is not covered by current typed GitHub evidence')
        require_authority([row['evidence_ref']],registry,'REPOSITORY_EVIDENCE','GitHub-confirmed path')
    for row in state['candidate_paths']:
        if not isinstance(row, dict) or set(row) != {'path','why_relevant','evidence_ref'} or not _valid_repo_path(row['path']):
            raise JoyflowError('invalid GitHub-derived candidate path row')
        if row['evidence_ref'] not in github_rows:
            raise JoyflowError('GitHub-derived candidate path lacks current typed GitHub evidence')
        require_authority([row['evidence_ref']],registry,'REPOSITORY_EVIDENCE','GitHub-derived candidate path')
    if state['local_discovery_required']:
        if state['github_discovery_status'] not in {'COMPLETED_INSUFFICIENT','UNAVAILABLE'}:
            raise JoyflowError('local discovery may be requested only after insufficient or unavailable GitHub discovery')
        if state['local_discovery_status'] not in {'PENDING','COMPLETED'} or not state['local_discovery_reason']:
            raise JoyflowError('local discovery requires explicit pending/completed state and reason')
    else:
        if state['local_discovery_status'] != 'NOT_REQUIRED' or state['local_discovery_reason'] is not None or state['local_discovery_binding'] is not None:
            raise JoyflowError('unneeded local discovery must remain NOT_REQUIRED without binding')
    route=capsule['route_profile']
    if route == 'READ_ONLY_DISCOVERY':
        if not state['local_discovery_required'] or state['local_discovery_status'] != 'PENDING' or state['final_allowed_paths_status'] != 'PENDING' or state['final_path_decision'] is not None or state['local_discovery_binding'] is not None:
            raise JoyflowError('READ_ONLY_DISCOVERY requires pending local supplementation and no final path decision')
        if state['path_discovery_source'] not in {'GITHUB_DERIVED','GITHUB_CONFIRMED'}:
            raise JoyflowError('pre-local discovery source must describe the completed GitHub pass')
    elif capsule['task_anchor']['change_scope'] == 'REPOSITORY_CHANGE':
        if state['final_allowed_paths_status'] != 'CONFIRMED' or not isinstance(state['final_path_decision'],dict):
            raise JoyflowError('mutating repository execution requires a Brain-confirmed Final Path Decision')
        return_digest=None
        if state['local_discovery_required']:
            if state['local_discovery_status']!='COMPLETED' or not isinstance(state['local_discovery_binding'],dict):
                raise JoyflowError('required local discovery must bind its exact completed Return')
            bind=state['local_discovery_binding']; required_bind={'source_projection_digest','path_discovery_return_digest','project_id','task_id','round_id'}
            if set(bind)!=required_bind:
                raise JoyflowError('local discovery binding shape mismatch')
            if bind['project_id']!=capsule['task_anchor']['project_id'] or bind['task_id']!=capsule['task_anchor']['task_id'] or bind['round_id']!=capsule['task_progress']['cycle']:
                raise JoyflowError('local discovery binding belongs to another task round')
            if not re.fullmatch(r'[0-9a-f]{64}',bind['source_projection_digest']) or not re.fullmatch(r'[0-9a-f]{64}',bind['path_discovery_return_digest']):
                raise JoyflowError('local discovery binding digests are invalid')
            return_digest=bind['path_discovery_return_digest']
            if state['path_discovery_source'] not in {'LOCAL_CODEX_DISCOVERED','COMBINED'}:
                raise JoyflowError('completed local discovery must be represented in the path source')
        if frame is not None:
            if not disposition or disposition['disposition']!='ACCEPT':
                raise JoyflowError('mutating structural execution requires an ACCEPT Brain architecture disposition')
            if disposition['source_structural_return_digest']!=return_digest:
                raise JoyflowError('Brain architecture disposition is bound to another structural discovery Return')
        validate_final_path_decision(state['final_path_decision'],capsule,expected_path_return_digest=return_digest)

def validate_repository_readiness(model: dict[str, Any], capsule: dict[str, Any], *, require_complete: bool=False) -> None:
    profile = model['route_profiles'][capsule['route_profile']]
    anchor = capsule['task_anchor'].get('repository_anchor')
    fiber = capsule.get('active_fibers', {}).get('repository_evidence')
    if profile['requires_repository_binding'] is True and (not anchor):
        raise JoyflowError('route requires repository anchor')
    if not fiber:
        if _required_fact_slots(model, capsule):
            raise JoyflowError('route requires repository evidence fiber')
    else:
        payload = fiber['payload']
        if set(payload) != {'baseline_commit', 'fact_slots', 'path_discovery', 'impact_coverage', 'context_exclusions', 'unresolved_repository_questions'}:
            raise JoyflowError('repository evidence fiber may contain only baseline, fact slots, bounded path-discovery state, task-local impact coverage, reversible context exclusions, and bounded questions')
        coverage=payload.get('impact_coverage', [])
        dims=[r.get('dimension') for r in coverage]
        if len(dims)!=len(set(dims)):
            raise JoyflowError('impact coverage dimensions must be unique')
        allowed_dims={'DIRECT_IMPLEMENTATION','DIRECT_CALLERS','INTERFACES_SCHEMA','DATA_STATE_BOUNDARIES','SHARED_CORE','RELEVANT_TESTS','RUNTIME_CHAIN'}
        registry = evidence_map(capsule)
        direct_impact_allowed={
            'REPOSITORY_EVIDENCE':None,
            'EXECUTION_EVIDENCE':{'PATH_OBSERVATION','DEPENDENCY_DERIVATION','VALIDATION_ENTRY_DERIVATION','LOCAL_FINDING_DERIVATION','REPOSITORY_FILE_SNAPSHOT','REPOSITORY_HEAD_OBSERVATION','REPOSITORY_COMMIT_OBSERVATION','RUNTIME_OUTPUT','TEST_RESULT'}
        }
        for row in coverage:
            if set(row)!={'dimension','status','evidence_refs','applicability_basis'} or row.get('dimension') not in allowed_dims or row.get('status') not in {'CHECKED','NOT_APPLICABLE','UNRESOLVED'} or not isinstance(row.get('applicability_basis'),str) or not row['applicability_basis'].strip():
                raise JoyflowError('impact coverage row is invalid')
            refs=row.get('evidence_refs') or []
            if row.get('status') in {'CHECKED','NOT_APPLICABLE'}:
                if not refs:
                    raise JoyflowError('checked or not-applicable impact coverage requires evidence refs')
                require_relevant_evidence(refs,registry,direct_impact_allowed,subject_type='IMPACT_DIMENSION',subject_id=row.get('dimension'),context=f"impact coverage {row.get('dimension')}")
            elif refs:
                require_refs(refs,registry,f"unresolved impact coverage {row.get('dimension')}")
        exclusions=payload.get('context_exclusions', [])
        seen=set()
        for row in exclusions:
            if set(row)!={'item','basis','reopen_when'} or not all(isinstance(row.get(k),str) and row[k].strip() for k in ('item','basis','reopen_when')):
                raise JoyflowError('context exclusion requires item, basis and reopen trigger')
            if row['item'] in seen: raise JoyflowError('context exclusions must be unique')
            seen.add(row['item'])
        if anchor and payload.get('baseline_commit') != anchor.get('baseline_commit'):
            raise JoyflowError('repository evidence baseline differs from repository anchor')
        registry = evidence_map(capsule)
        required_slots = set(_required_fact_slots(model, capsule))
        actual_slots = payload.get('fact_slots', {})
        missing = required_slots - set(actual_slots)
        if missing:
            raise JoyflowError(f'repository evidence missing required fact slots: {sorted(missing)}')
        for slot, row in actual_slots.items():
            if slot not in model['repository_fact_slot_policy']:
                raise JoyflowError(f'unknown repository fact slot: {slot}')
            if set(row) != {'status', 'claim', 'evidence_ref', 'not_applicable_reason'}:
                raise JoyflowError(f'repository fact slot contains unbounded content: {slot}')
            if row['status'] not in {'PROVEN', 'NOT_APPLICABLE'}:
                raise JoyflowError(f'invalid repository fact slot status: {slot}')
            require_refs([row['evidence_ref']], registry, f'repository fact slot {slot}')
            require_authority([row['evidence_ref']], registry, 'REPOSITORY_EVIDENCE', f'repository fact slot {slot}')
            if row['status'] == 'PROVEN' and (not row['claim']):
                raise JoyflowError(f'proven repository fact slot lacks claim: {slot}')
            if row['status'] == 'NOT_APPLICABLE':
                if not model['repository_fact_slot_policy'][slot]['allow_not_applicable'] or not row['not_applicable_reason']:
                    raise JoyflowError(f'repository fact slot cannot be not applicable: {slot}')
        if require_complete and payload.get('unresolved_repository_questions'):
            raise JoyflowError('unresolved repository questions block executable projection')
    if capsule['task_anchor']['change_scope'] == 'REPOSITORY_CHANGE':
        decision = capsule['active_fibers']['decision_boundary']['payload']
        binding = decision.get('repository_binding')
        if not anchor or not binding:
            raise JoyflowError('repository change requires anchor and execution binding')
        if binding.get('repository_id') != anchor.get('repository_id') or binding.get('expected_base_commit') != anchor.get('baseline_commit'):
            raise JoyflowError('repository binding does not match canonical-state anchor')
        if binding.get('working_branch') == binding.get('default_branch'):
            raise JoyflowError('repository change cannot execute on default branch')
        allowed = _allow_paths(capsule)
        operation=capsule['task_anchor']['repository_operation']
        if operation=='CURRENT_ROUND_REPOSITORY_CHANGE' and not allowed:
            raise JoyflowError('current-round repository change requires at least one confirmed ALLOW_PATH')
        if operation=='EXISTING_FROZEN_PR_REPLAY' and allowed:
            raise JoyflowError('existing PR replay requires exactly zero current product mutation paths')

def validate_repository_evidence(capsule: dict[str, Any], *, require_complete: bool=False) -> None:
    validate_repository_readiness(load_model(), capsule, require_complete=require_complete)

def _validation_bindings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.get('obligation_registry', [])

def expected_validation_obligations(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in semantic_items(capsule):
        if not active_material(item):
            continue
        for effect in item.get('effects', []):
            if effect.get('effect_type') != 'VALIDATE':
                continue
            mode = effect.get('validation_mode')
            check_ids = effect.get('check_ids', [])
            human_ids = effect.get('human_validation_ids', [])
            rows.append({'obligation_id': f"VAL_{effect['effect_id']}", 'case_id': f"CASE_{effect['effect_id']}", 'source_item_id': item['item_id'], 'source_meaning_digest': item['meaning_digest'], 'assertion_digest': digest(effect['value']), 'mode': mode, 'required': True, 'check_ids': sorted(check_ids), 'human_validation_ids': sorted(human_ids)})
    return sorted(rows, key=lambda r: r['obligation_id'])

def validate_validation_closure(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    validation = capsule.get('active_fibers', {}).get('validation')
    if not validation:
        return
    payload = validation['payload']
    checks = payload.get('checks', [])
    humans = payload.get('human_validation', [])
    check_ids = [r.get('check_id') for r in checks]
    human_ids = [r.get('validation_id') for r in humans]
    if None in check_ids or len(check_ids) != len(set(check_ids)):
        raise JoyflowError('check IDs must be unique')
    if None in human_ids or len(human_ids) != len(set(human_ids)):
        raise JoyflowError('human validation IDs must be unique')
    check_map = {r['check_id']: r for r in checks}
    human_map = {r['validation_id']: r for r in humans}
    actual = sorted(payload.get('obligation_registry', []), key=lambda r: r.get('obligation_id', ''))
    expected = expected_validation_obligations(capsule)
    if actual != expected:
        raise JoyflowError('validation obligation registry is not exact semantic-effect projection')
    case_map = {r['case_id']: r for r in payload.get('acceptance_cases', [])}
    if set(case_map) != {r['case_id'] for r in expected}:
        raise JoyflowError('every validation obligation must have one acceptance case')
    for row in expected:
        mode = row['mode']
        cids, hids = (row['check_ids'], row['human_validation_ids'])
        if mode not in model['validation_modes']:
            raise JoyflowError('validation obligation mode invalid')
        if set(cids) - set(check_map) or set(hids) - set(human_map):
            raise JoyflowError('validation obligation references unknown evidence path')
        if mode in {'MACHINE', 'BOTH'} and (not cids):
            raise JoyflowError('machine validation obligation requires check IDs')
        if mode in {'HUMAN', 'BOTH'} and (not hids):
            raise JoyflowError('human validation obligation requires human validation IDs')
        if any((not check_map[x].get('required') for x in cids)) or any((not human_map[x].get('required') for x in hids)):
            raise JoyflowError('validation obligation must bind required evidence paths')
        assertion = case_map[row['case_id']]['assertion']
        if digest(assertion) != row['assertion_digest']:
            raise JoyflowError('validation obligation assertion digest mismatch')
    profile = model['route_profiles'][capsule['route_profile']]
    if profile['executable'] and (not expected):
        raise JoyflowError('executable task requires validation obligations')
    if any((not case.get('required') for case in payload.get('acceptance_cases', []))):
        raise JoyflowError('semantic acceptance cases cannot be optional')
    for check in checks:
        if set(check)!={'check_id','command','argv','cwd_scope','required','evidence_kind'}:
            raise JoyflowError('validation check must bind exact argv plus SOURCE_ROOT cwd')
        if check.get('cwd_scope')!='SOURCE_ROOT' or check.get('command')!=_canonical_argv(check.get('argv')):
            raise JoyflowError('validation command display must be derived from approved argv and SOURCE_ROOT cwd')
        if check['command'].strip().lower() in {'echo ok', 'true', 'exit 0'}:
            raise JoyflowError('placeholder validation command is not allowed')
    if profile['validation_depth'] == 'STRICT':
        rows = payload.get('adversarial_review', [])
        categories = {r.get('category') for r in rows}
        required = set(model['validation_requirements']['strict_adversarial_categories'])
        if categories != required:
            raise JoyflowError('strict adversarial review categories incomplete')
        registry = evidence_map(capsule)
        mandatory = set(model['validation_requirements']['strict_mandatory_categories'])
        for row in rows:
            if row.get('verdict') not in {'PASS', 'NOT_APPLICABLE'}:
                raise JoyflowError('invalid adversarial review verdict')
            require_refs(row.get('evidence_refs', []), registry, f"adversarial review {row.get('category')}")
            if row['category'] in mandatory and row['verdict'] != 'PASS':
                raise JoyflowError(f"strict adversarial category cannot be NOT_APPLICABLE: {row['category']}")
            if row['verdict'] == 'NOT_APPLICABLE':
                proof = row.get('applicability_proof')
                if not proof or not proof.get('reason') or (not proof.get('evidence_refs')):
                    raise JoyflowError('NOT_APPLICABLE adversarial result requires proof')
                require_refs(proof['evidence_refs'], registry, f"adversarial applicability {row['category']}")

def _evidence_for_subject(registry: dict[str, dict[str, Any]], evidence_ref: str, *, authority: str, kinds: set[str], subject_type: str, subject_id: str, producers: set[str], context: str) -> dict[str, Any]:
    require_refs([evidence_ref], registry, context)
    row = registry[evidence_ref]
    if row['authority'] != authority or row['kind'] not in kinds or row['subject_type'] != subject_type or row['subject_id'] != subject_id or row['produced_by'] not in producers:
        raise JoyflowError(f'{context} evidence does not match authority/kind/subject/producer')
    return row

def _requires_pr(capsule: dict[str, Any]) -> bool:
    profile = load_model()['route_profiles'][capsule['route_profile']]
    return bool(profile['requires_pr'] is True or (profile['requires_pr'] == 'conditional' and capsule['task_anchor']['change_scope'] == 'REPOSITORY_CHANGE'))

def validate_single_active_round_binding(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    """Validate the current round object identity without creating a global scheduler.

    The Web Brain owns the one-active-task-per-project-round rule. Mechanical
    artifacts must all carry the same project, task and cycle (round) identity.
    """
    anchor = capsule['task_anchor']
    if not anchor.get('project_id') or not anchor.get('task_id'):
        raise JoyflowError('project_id and task_id are required for the active task round')
    if capsule['task_progress']['cycle'] < 1:
        raise JoyflowError('active task round must be positive')

def _round_packet_subject(project_id: str, task_id: str, round_id: int, projection_digest: str) -> str:
    return f'{project_id}:{task_id}:{round_id}:{projection_digest}'

def _canonical_source_materials(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    normalized=[]
    for row in rows:
        normalized.append({'material_id':row['material_id'],'material_digest':row['material_digest'],'source_ref':row['source_ref']})
    normalized=sorted(normalized,key=lambda r:r['material_id'])
    if len({r['material_id'] for r in normalized})!=len(normalized):
        raise JoyflowError('source material IDs must be unique')
    return normalized

def _source_material_set_digest(rows: list[dict[str,Any]]) -> str:
    return digest(_canonical_source_materials(rows))

def _artifact_output_identity(row: dict[str,Any]) -> dict[str,Any]:
    return {k:row[k] for k in ('artifact_id','artifact_digest','bytes','media_type','role')}

def _canonical_artifact_outputs(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    normalized=[_artifact_output_identity(row) for row in rows]
    normalized=sorted(normalized,key=lambda r:r['artifact_id'])
    if len({r['artifact_id'] for r in normalized})!=len(normalized):
        raise JoyflowError('Artifact output IDs must be unique')
    return normalized

def _artifact_output_set_digest(rows: list[dict[str,Any]]) -> str:
    return digest(_canonical_artifact_outputs(rows))

def _execution_object_from_capsule(capsule: dict[str, Any]) -> dict[str, Any]:
    anchor=capsule['task_anchor']
    if anchor.get('repository_anchor') is not None:
        repo=anchor.get('repository_anchor') or {}
        replay=anchor.get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY'
        return {'object_type':'REPOSITORY','source_mode':'EXISTING_PR_HEAD' if replay else 'REPOSITORY_REF','object_id':repo.get('repository_id'),'expected_ref_or_sha256':repo.get('frozen_head_sha') if replay else repo.get('baseline_commit'),'source_material_refs':[]}
    artifact=anchor.get('artifact_anchor') or {}
    if artifact.get('source_mode')=='NEW_ARTIFACT':
        materials=_canonical_source_materials(artifact.get('source_materials',[]))
        return {'object_type':'ARTIFACT','source_mode':'NEW_ARTIFACT','object_id':'SOURCE_MATERIAL_SET','expected_ref_or_sha256':_source_material_set_digest(materials),'source_material_refs':copy.deepcopy(artifact.get('source_material_refs',[]))}
    return {'object_type':'ARTIFACT','source_mode':'EXISTING_ARTIFACT','object_id':artifact.get('artifact_id'),'expected_ref_or_sha256':artifact.get('artifact_sha256'),'source_material_refs':copy.deepcopy(artifact.get('source_material_refs',[]))}

def _return_object_shape(obj: dict[str, Any]) -> dict[str, Any]:
    return {'object_type':obj['object_type'],'source_mode':obj['source_mode'],'object_id':obj.get('object_id'),'ref_or_sha256':obj.get('expected_ref_or_sha256') if 'expected_ref_or_sha256' in obj else obj.get('ref_or_sha256')}


def _approved_input_object_from_capsule(capsule: dict[str,Any]) -> dict[str,Any]:
    anchor=capsule['task_anchor']
    if anchor.get('repository_anchor') is not None:
        repo=anchor['repository_anchor']
        if anchor.get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY':
            row={'object_type':'EXISTING_FROZEN_PR','repository_id':repo['repository_id'],'pr_number':repo['pr_number'],'base_commit':repo['baseline_commit'],'head_commit':repo['frozen_head_sha'],'base_branch':repo['base_branch'],'working_branch':repo['working_branch'],'pr_url':repo['pr_url']}
        else:
            row={'object_type':'REPOSITORY_BASE','repository_id':repo['repository_id'],'base_commit':repo['baseline_commit']}
    else:
        artifact=anchor['artifact_anchor']
        if artifact['source_mode']=='NEW_ARTIFACT':
            materials=_canonical_source_materials(artifact.get('source_materials',[]))
            row={'object_type':'SOURCE_MATERIAL_SET','source_mode':'NEW_ARTIFACT','source_materials':materials,'source_material_set_digest':_source_material_set_digest(materials),'source_material_refs':copy.deepcopy(artifact.get('source_material_refs',[]))}
        else:
            row={'object_type':'ARTIFACT_SOURCE','source_mode':'EXISTING_ARTIFACT','artifact_id':artifact.get('artifact_id'),'artifact_sha256':artifact.get('artifact_sha256'),'source_material_refs':copy.deepcopy(artifact.get('source_material_refs',[]))}
    row['object_digest']=digest(row)
    return row

def _selected_discovery_item_ids(final: dict[str,Any] | None) -> dict[str,list[str]]:
    selected={'path_ids':[],'dependency_ids':[],'validation_ids':[],'finding_ids':[]}
    if not isinstance(final,dict):
        return selected
    for item in final.get('allowed_path_items',[]):
        selected['path_ids'].extend(item.get('source_return_path_ids',[]))
        selected['dependency_ids'].extend(item.get('source_return_dependency_ids',[]))
        selected['validation_ids'].extend(item.get('source_return_validation_ids',[]))
        selected['finding_ids'].extend(item.get('source_return_finding_ids',[]))
    return {k:sorted(set(v)) for k,v in selected.items()}

def _discovery_object_from_capsule(capsule: dict[str,Any]) -> dict[str,Any]:
    approved_digest=_approved_input_object_from_capsule(capsule)['object_digest']
    if capsule['task_anchor'].get('repository_anchor') is None:
        row={'discovery_mode':'NOT_APPLICABLE','source_object_digest':approved_digest,'final_path_decision_digest':None,'discovery_source_object':None}
    else:
        path_state=capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{}) or {}
        final=path_state.get('final_path_decision')
        binding=path_state.get('local_discovery_binding') or {}
        mode='GITHUB_PLUS_LOCAL' if path_state.get('path_discovery_source') in {'LOCAL_DISCOVERY','COMBINED'} or path_state.get('local_discovery_status')=='COMPLETED' else 'GITHUB_ONLY'
        source=None
        if mode=='GITHUB_PLUS_LOCAL':
            selected=_selected_discovery_item_ids(final)
            source={'discovery_projection_digest':binding.get('source_projection_digest'),'path_discovery_return_digest':binding.get('path_discovery_return_digest'),'selected_item_ids':selected,'source_digest':None}
            source['source_digest']=digest(strip_digest(source,'source_digest'))
        row={'discovery_mode':mode,'source_object_digest':approved_digest,'final_path_decision_digest':final.get('decision_digest') if isinstance(final,dict) else None,'discovery_source_object':source}
    row['discovery_digest']=digest(row)
    return row

def _approved_execution_boundary_from_capsule(capsule: dict[str,Any]) -> dict[str,Any]:
    decision=capsule['active_fibers']['decision_boundary']['payload']
    validation=capsule['active_fibers']['validation']['payload']
    allowed=[r['statement'] for r in decision.get('boundary_obligations',[]) if r.get('kind')=='ALLOW_PATH']
    commands=[{'check_id':r['check_id'],'argv':copy.deepcopy(r['argv']),'cwd_scope':r['cwd_scope']} for r in validation.get('checks',[])]
    semantics=[{'item_id':r['item_id'],'meaning_digest':r['meaning_digest']} for r in semantic_items(capsule) if active_material(r)]
    repo=capsule['task_anchor'].get('repository_anchor') or {}
    review_coverage=sorted(repo.get('review_coverage_paths',[])) if capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else []
    row={'allowed_paths':sorted(allowed),'review_coverage_paths':review_coverage,'validation_commands':sorted(commands,key=lambda r:r['check_id']),'protected_semantics':sorted(semantics,key=lambda r:r['item_id']),'non_goals_digest':digest(capsule['task_anchor']['non_goals']),'candidate_route_ids':sorted(r['route_id'] for r in decision.get('technical_route_space',{}).get('candidate_routes',[]))}
    row['boundary_digest']=digest(row)
    return row

def _expected_result_contract_from_capsule(capsule: dict[str,Any]) -> dict[str,Any]:
    scope=capsule['task_anchor']['change_scope']
    if scope=='REPOSITORY_CHANGE':
        if capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY':
            return {'result_type':'VALIDATED_EXISTING_PR_HEAD','source_head_must_remain_unchanged':True,'base_must_be_ancestor_of_head':True,'validation_target_must_equal_frozen_head':True,'validation_environment':'TEMPORARY_DETACHED_WORKTREE'}
        return {'result_type':'REPOSITORY_HEAD','requires_ancestry_from_input':True,'validation_target_must_equal_result':True,'validation_environment':'TEMPORARY_DETACHED_WORKTREE'}
    if scope=='READ_ONLY':
        return {'result_type':'PATH_DISCOVERY_RETURN','requires_ancestry_from_input':False,'validation_target_must_equal_result':True,'validation_environment':'APPROVED_BASE_WORKTREE'}
    return {'result_type':'ARTIFACT_OUTPUT_SET','requires_ancestry_from_input':False,'validation_target_must_equal_result':True,'validation_environment':'EXACT_OUTPUT_FILES'}

def task_object_lifecycle_from_capsule(capsule: dict[str,Any]) -> dict[str,Any]:
    scope=capsule['task_anchor']['change_scope']
    if scope=='ARTIFACT_CHANGE':
        route_type='NEW_ARTIFACT' if capsule['task_anchor']['artifact_anchor']['source_mode']=='NEW_ARTIFACT' else 'ARTIFACT_REPAIR'
    else:
        route_type='EXISTING_PR_REPLAY' if scope=='REPOSITORY_CHANGE' and capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else {'REPOSITORY_CHANGE':'REPOSITORY_CHANGE','READ_ONLY':'REPOSITORY_DISCOVERY'}[scope]
    row={'lifecycle_version':1,'route_type':route_type,'approved_input_object':_approved_input_object_from_capsule(capsule),'discovery_object':_discovery_object_from_capsule(capsule),'approved_execution_boundary':_approved_execution_boundary_from_capsule(capsule),'expected_result_contract':_expected_result_contract_from_capsule(capsule),'lifecycle_digest':None}
    row['lifecycle_digest']=digest(strip_digest(row,'lifecycle_digest'))
    return row

def validate_task_object_lifecycle(projection: dict[str,Any]) -> None:
    row=projection.get('task_object_lifecycle')
    if not isinstance(row,dict) or row.get('lifecycle_version')!=1 or row.get('lifecycle_digest')!=digest(strip_digest(row,'lifecycle_digest')):
        raise JoyflowError('task object lifecycle is missing or has an invalid digest')
    scope=projection['task_anchor']['change_scope']
    expected_route=('NEW_ARTIFACT' if projection['task_anchor']['artifact_anchor']['source_mode']=='NEW_ARTIFACT' else 'ARTIFACT_REPAIR') if scope=='ARTIFACT_CHANGE' else ('EXISTING_PR_REPLAY' if scope=='REPOSITORY_CHANGE' and projection['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else {'REPOSITORY_CHANGE':'REPOSITORY_CHANGE','READ_ONLY':'REPOSITORY_DISCOVERY'}[scope])
    if row.get('route_type')!=expected_route:
        raise JoyflowError('task object lifecycle route does not match the task anchor')
    approved=row.get('approved_input_object',{})
    execution=projection['execution_object']
    if expected_route in {'REPOSITORY_CHANGE','EXISTING_PR_REPLAY','REPOSITORY_DISCOVERY'}:
        anchor=projection['task_anchor']['repository_anchor']
        expected=({'object_type':'EXISTING_FROZEN_PR','repository_id':anchor['repository_id'],'pr_number':anchor['pr_number'],'base_commit':anchor['baseline_commit'],'head_commit':anchor['frozen_head_sha'],'base_branch':anchor['base_branch'],'working_branch':anchor['working_branch'],'pr_url':anchor['pr_url']} if expected_route=='EXISTING_PR_REPLAY' else {'object_type':'REPOSITORY_BASE','repository_id':anchor['repository_id'],'base_commit':anchor['baseline_commit']})
        if any(approved.get(k)!=v for k,v in expected.items()) or approved.get('object_digest')!=digest(expected):
            raise JoyflowError('task lifecycle approved repository input differs from the Projection anchor')
        expected_execution_ref=anchor['frozen_head_sha'] if expected_route=='EXISTING_PR_REPLAY' else anchor['baseline_commit']
        expected_source_mode='EXISTING_PR_HEAD' if expected_route=='EXISTING_PR_REPLAY' else 'REPOSITORY_REF'
        if execution['object_id']!=anchor['repository_id'] or execution['expected_ref_or_sha256']!=expected_execution_ref or execution['source_mode']!=expected_source_mode:
            raise JoyflowError('execution object and lifecycle repository input differ')
    else:
        anchor=projection['task_anchor']['artifact_anchor']
        if expected_route=='NEW_ARTIFACT':
            materials=_canonical_source_materials(anchor.get('source_materials',[]))
            expected={'object_type':'SOURCE_MATERIAL_SET','source_mode':'NEW_ARTIFACT','source_materials':materials,'source_material_set_digest':_source_material_set_digest(materials),'source_material_refs':copy.deepcopy(anchor.get('source_material_refs',[]))}
            if execution['object_id']!='SOURCE_MATERIAL_SET' or execution['expected_ref_or_sha256']!=expected['source_material_set_digest']:
                raise JoyflowError('execution object and new Artifact source-material set differ')
        else:
            expected={'object_type':'ARTIFACT_SOURCE','source_mode':'EXISTING_ARTIFACT','artifact_id':anchor.get('artifact_id'),'artifact_sha256':anchor.get('artifact_sha256'),'source_material_refs':copy.deepcopy(anchor.get('source_material_refs',[]))}
            if execution['object_id']!=anchor.get('artifact_id') or execution['expected_ref_or_sha256']!=anchor.get('artifact_sha256'):
                raise JoyflowError('execution object and Artifact source differ')
        if any(approved.get(k)!=v for k,v in expected.items()) or approved.get('object_digest')!=digest(expected):
            raise JoyflowError('task lifecycle approved Artifact input differs from the Projection anchor')
    boundary=row.get('approved_execution_boundary',{})
    actual_allowed=sorted(r['statement'] for r in projection['decision_boundary'].get('boundary_obligations',[]) if r.get('kind')=='ALLOW_PATH')
    actual_commands=sorted([{'check_id':r['check_id'],'argv':copy.deepcopy(r['argv']),'cwd_scope':r['cwd_scope']} for r in projection['validation'].get('checks',[])],key=lambda r:r['check_id'])
    actual_review=sorted((projection['task_anchor'].get('repository_anchor') or {}).get('review_coverage_paths',[])) if expected_route=='EXISTING_PR_REPLAY' else []
    if boundary.get('allowed_paths')!=actual_allowed or boundary.get('review_coverage_paths')!=actual_review or boundary.get('validation_commands')!=actual_commands:
        raise JoyflowError('task lifecycle execution boundary differs from the approved Projection')
    if boundary.get('boundary_digest')!=digest(strip_digest(boundary,'boundary_digest')):
        raise JoyflowError('task lifecycle approved boundary digest mismatch')
    discovery=row.get('discovery_object',{})
    if discovery.get('source_object_digest')!=approved.get('object_digest') or discovery.get('discovery_digest')!=digest(strip_digest(discovery,'discovery_digest')):
        raise JoyflowError('task lifecycle discovery object is not bound to the approved input object')
    path_state=projection.get('repository_evidence',{}).get('path_discovery',{}) if expected_route in {'REPOSITORY_CHANGE','EXISTING_PR_REPLAY','REPOSITORY_DISCOVERY'} else {}
    final=path_state.get('final_path_decision') if isinstance(path_state,dict) else None
    if discovery.get('final_path_decision_digest')!=(final.get('decision_digest') if isinstance(final,dict) else None):
        raise JoyflowError('task lifecycle discovery object differs from the exact final path decision')
    source=discovery.get('discovery_source_object')
    if discovery.get('discovery_mode')=='GITHUB_PLUS_LOCAL':
        binding=path_state.get('local_discovery_binding') or {}
        if not isinstance(source,dict) or source.get('source_digest')!=digest(strip_digest(source,'source_digest')):
            raise JoyflowError('local discovery lifecycle source object is missing or invalid')
        if source.get('discovery_projection_digest')!=binding.get('source_projection_digest') or source.get('path_discovery_return_digest')!=binding.get('path_discovery_return_digest') or source.get('selected_item_ids')!=_selected_discovery_item_ids(final):
            raise JoyflowError('local discovery lifecycle source differs from the sealed discovery Projection, Return or selected items')
    elif source is not None:
        raise JoyflowError('non-local lifecycle cannot carry a local discovery source object')


def _execution_lifecycle_result_payload(row: dict[str,Any]) -> dict[str,Any]:
    return strip_digest(row,'transition_digest')

def execution_lifecycle_result_digest(row: dict[str,Any]) -> str:
    return digest(_execution_lifecycle_result_payload(row))

def validate_execution_lifecycle_result_structure(row: dict[str,Any], projection: dict[str,Any], codex_return: dict[str,Any]) -> None:
    lifecycle=projection['task_object_lifecycle']
    if row.get('approved_lifecycle_digest')!=lifecycle['lifecycle_digest'] or row.get('transition_digest')!=execution_lifecycle_result_digest(row):
        raise JoyflowError('execution lifecycle result does not bind the approved task lifecycle')
    status=codex_return['execution_status']
    if row.get('transition_status')!=('RESULT_VALIDATED' if status=='COMPLETED' else 'BLOCKED_BEFORE_VALIDATED_RESULT'):
        raise JoyflowError('execution lifecycle transition status differs from the Codex Return')
    result=row.get('execution_result_object'); validation=row.get('final_validation_object')
    if status=='BLOCKED':
        if result is not None or validation is not None:
            raise JoyflowError('blocked execution cannot claim a validated result object')
        return
    if lifecycle['route_type']=='REPOSITORY_CHANGE':
        pr=codex_return.get('pr_evidence')
        if not pr or not isinstance(result,dict) or not isinstance(validation,dict):
            raise JoyflowError('completed repository execution requires lifecycle result and validation objects')
        approved=lifecycle['approved_input_object']
        expected_result={'result_type':'REPOSITORY_HEAD','repository_id':pr['repository_id'],'base_commit':pr['base_commit'],'head_commit':pr['head_sha'],'pr_url':pr['pr_url']}
        if result!=expected_result or pr['base_commit']!=approved['base_commit'] or pr['repository_id']!=approved['repository_id']:
            raise JoyflowError('repository lifecycle result differs from the approved base or PR evidence')
        refs=sorted({r['evidence_ref'] for r in codex_return['machine_results']})
        expected_validation={'target_type':'REPOSITORY_HEAD','repository_id':pr['repository_id'],'target_commit':pr['head_sha'],'validation_environment':'TEMPORARY_DETACHED_WORKTREE','machine_result_evidence_refs':refs,'diff_evidence_ref':pr['diff_evidence_ref']}
        if validation!=expected_validation:
            raise JoyflowError('repository final validation object differs from the exact result head')
    elif lifecycle['route_type']=='EXISTING_PR_REPLAY':
        replay=codex_return.get('repository_replay_evidence')
        if not replay or not isinstance(result,dict) or not isinstance(validation,dict):
            raise JoyflowError('completed existing PR replay requires replay evidence and lifecycle objects')
        approved=lifecycle['approved_input_object']
        expected_result={'result_type':'VALIDATED_EXISTING_PR_HEAD','repository_id':replay['repository_id'],'pr_number':replay['pr_number'],'base_commit':replay['base_commit'],'head_commit':replay['frozen_head_sha']}
        if result!=expected_result or replay['base_commit']!=approved['base_commit'] or replay['frozen_head_sha']!=approved['head_commit'] or replay['repository_id']!=approved['repository_id'] or replay['pr_number']!=approved['pr_number']:
            raise JoyflowError('existing PR replay lifecycle result differs from the approved frozen PR')
        refs=sorted({r['evidence_ref'] for r in codex_return['machine_results']})
        expected_validation={'target_type':'REPOSITORY_HEAD','repository_id':replay['repository_id'],'target_commit':replay['frozen_head_sha'],'validation_environment':'TEMPORARY_DETACHED_WORKTREE','machine_result_evidence_refs':refs,'diff_evidence_ref':replay['diff_evidence_ref']}
        if validation!=expected_validation:
            raise JoyflowError('existing PR replay final validation object differs from the frozen head')
    else:
        artifact=codex_return.get('artifact_evidence')
        if not artifact or not isinstance(result,dict) or not isinstance(validation,dict):
            raise JoyflowError('completed Artifact execution requires lifecycle result and validation objects')
        outputs=_canonical_artifact_outputs(artifact['outputs'])
        output_set_digest=_artifact_output_set_digest(artifact['outputs'])
        if artifact['output_set_digest']!=output_set_digest:
            raise JoyflowError('Artifact evidence output-set digest mismatch')
        refs=sorted({ref for row in artifact['outputs'] for ref in row['validation_evidence_refs']})
        coverage=sorted([{'artifact_id':row['artifact_id'],'validation_evidence_refs':sorted(row['validation_evidence_refs'])} for row in artifact['outputs']],key=lambda r:r['artifact_id'])
        expected_result={'result_type':'ARTIFACT_OUTPUT_SET','outputs':outputs,'output_set_digest':output_set_digest}
        expected_validation={'target_type':'ARTIFACT_OUTPUT_SET','target_digest':output_set_digest,'validation_environment':'EXACT_OUTPUT_FILES','machine_result_evidence_refs':sorted({r['evidence_ref'] for r in codex_return['machine_results']}),'artifact_validation_evidence_refs':refs,'output_validation_coverage':coverage,'uncovered_output_ids':[]}
        if result!=expected_result or validation!=expected_validation:
            raise JoyflowError('Artifact lifecycle result or final validation object differs from the exact output set')

def validate_task_object_anchor(capsule: dict[str, Any]) -> None:
    anchor=capsule['task_anchor']; scope=anchor['change_scope']; repo=anchor.get('repository_anchor'); artifact=anchor.get('artifact_anchor')
    if scope=='REPOSITORY_CHANGE':
        if not isinstance(repo,dict) or not repo.get('repository_id') or not repo.get('baseline_commit') or artifact is not None:
            raise JoyflowError('repository task requires exact repository anchor and no artifact anchor')
        if anchor.get('repository_operation')=='CURRENT_ROUND_REPOSITORY_CHANGE' and set(repo)!={'repository_id','baseline_commit'}:
            raise JoyflowError('current-round repository change anchor shape mismatch')
        if anchor.get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY':
            expected={'repository_id','baseline_commit','pr_number','pr_url','base_branch','working_branch','frozen_head_sha','review_coverage_paths'}
            if set(repo)!=expected:
                raise JoyflowError('existing PR replay anchor shape mismatch')
    elif scope=='ARTIFACT_CHANGE':
        if repo is not None or not isinstance(artifact,dict):
            raise JoyflowError('artifact task requires exact artifact anchor and no repository anchor')
        if set(artifact)!={'source_mode','artifact_id','artifact_sha256','source_material_refs','source_materials'}:
            raise JoyflowError('artifact anchor shape mismatch')
        mode=artifact['source_mode']; refs=artifact['source_material_refs']; materials=artifact['source_materials']
        if mode=='EXISTING_ARTIFACT':
            if not artifact.get('artifact_id') or not re.fullmatch(r'[0-9a-f]{64}',artifact.get('artifact_sha256','')) or materials:
                raise JoyflowError('existing artifact task requires exact artifact id/SHA and no source-material set')
        elif mode=='NEW_ARTIFACT':
            if artifact.get('artifact_id') is not None or artifact.get('artifact_sha256') is not None or not refs or not materials:
                raise JoyflowError('new artifact task requires exact source materials and no pre-existing artifact identity')
            canonical=_canonical_source_materials(materials)
            if canonical!=materials or [r['source_ref'] for r in canonical]!=refs:
                raise JoyflowError('new artifact source materials must be canonical and exactly match source material refs')
            for row in canonical:
                if not re.fullmatch(r'[0-9a-f]{64}',row['material_digest']):
                    raise JoyflowError('new artifact source material digest must be SHA-256')
        else:
            raise JoyflowError('unknown artifact source mode')
        require_refs(refs,evidence_map(capsule),'artifact source material')
    else:
        if anchor.get('repository_operation')!='NOT_APPLICABLE':
            raise JoyflowError('non-repository task repository operation must be NOT_APPLICABLE')
        if artifact is not None:
            raise JoyflowError('non-artifact task cannot carry artifact anchor')
        if capsule['route_profile']=='READ_ONLY_DISCOVERY' and (not isinstance(repo,dict) or not repo.get('repository_id') or not repo.get('baseline_commit')):
            raise JoyflowError('read-only repository discovery requires exact repository anchor')



def _task_bound_preflight_subject_payload(capsule: dict[str, Any], dimension: str) -> tuple[str,list[str],dict[str,Any]]:
    anchor=capsule['task_anchor']
    decision=capsule.get('active_fibers',{}).get('decision_boundary',{}).get('payload',{})
    validation=capsule.get('active_fibers',{}).get('validation',{}).get('payload',{})
    routes=decision.get('technical_route_space',{}).get('candidate_routes',[])
    boundary=decision.get('boundary_obligations',[])
    if dimension=='OBJECT_IDENTITY':
        repo=anchor.get('repository_anchor')
        artifact=anchor.get('artifact_anchor')
        payload={'repository_operation':anchor.get('repository_operation'),'repository_anchor':repo,'artifact_anchor':artifact}
        refs=[]
        if isinstance(repo,dict):
            if anchor.get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY':
                refs.append(f"EXISTING_FROZEN_PR:{repo.get('repository_id')}#{repo.get('pr_number')}@{repo.get('baseline_commit')}..{repo.get('frozen_head_sha')}")
            else:
                refs.append(f"REPOSITORY:{repo.get('repository_id')}@{repo.get('baseline_commit')}")
        if isinstance(artifact,dict):
            mode=artifact.get('source_mode')
            if mode=='EXISTING_ARTIFACT':
                refs.append(f"ARTIFACT:{artifact.get('artifact_id')}@{artifact.get('artifact_sha256')}")
            elif mode=='NEW_ARTIFACT':
                refs.extend(f"SOURCE_MATERIAL:{ref}" for ref in artifact.get('source_material_refs',[]))
        return 'EXECUTION_OBJECT',refs,payload
    if dimension=='ROUTE_ASSUMPTION_VALIDITY':
        payload={'candidate_routes':routes,'technical_decisions':decision.get('technical_decisions',[])}
        return 'BRAIN_ROUTE_SPACE',[f"ROUTE:{r['route_id']}" for r in routes],payload
    if dimension=='PATH_SUFFICIENCY':
        allows=[{'obligation_id':r['obligation_id'],'statement':r['statement']} for r in boundary if r.get('kind')=='ALLOW_PATH']
        final=(capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{}) or {}).get('final_path_decision')
        refs=[f"ALLOW:{r['obligation_id']}" for r in allows]
        if final: refs.append(f"FINAL_PATH_DECISION:{final.get('decision_digest')}")
        if not refs: refs.append(f"NO_REPOSITORY_PATH_BOUNDARY:{anchor.get('change_scope')}")
        review_coverage=sorted((anchor.get('repository_anchor') or {}).get('review_coverage_paths',[])) if anchor.get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else []
        if review_coverage: refs.append(f"REVIEW_COVERAGE:{digest(review_coverage)}")
        return 'APPROVED_PATH_BOUNDARY',refs,{'repository_operation':anchor.get('repository_operation'),'allow_paths':allows,'review_coverage_paths':review_coverage,'final_path_decision':final,'change_scope':anchor.get('change_scope')}
    if dimension=='ACCEPTANCE_FEASIBILITY':
        obligations=validation.get('obligation_registry',[]); checks=validation.get('checks',[]); humans=validation.get('human_validation',[])
        refs=[f"VALIDATION:{r['obligation_id']}" for r in obligations]+[f"CHECK:{r['check_id']}" for r in checks]+[f"HUMAN:{r['validation_id']}" for r in humans]
        return 'ACCEPTANCE_CONTRACT',refs,{'obligations':obligations,'checks':checks,'human_validation':humans}
    if dimension=='PRODUCT_SEMANTIC_PRESERVATION':
        rows=[]
        for item in semantic_items(capsule):
            if active_material(item):
                rows.append({'item_id':item['item_id'],'meaning_digest':item['meaning_digest'],'effects':[{'effect_id':e['effect_id'],'effect_type':e['effect_type'],'value':e['value'],'effect_digest':e['effect_digest']} for e in item.get('effects',[])]})
        rows=sorted(rows,key=lambda r:r['item_id'])
        return 'MATERIAL_SEMANTICS',[f"SEMANTIC:{r['item_id']}" for r in rows],{'material_semantics':rows}
    if dimension=='NON_GOAL_PRESERVATION':
        must_not=[{'obligation_id':r['obligation_id'],'statement':r['statement']} for r in boundary if r.get('kind')=='MUST_NOT_DO']
        refs=[f"NON_GOAL:{i+1}" for i,_ in enumerate(anchor.get('non_goals',[]))]+[f"MUST_NOT:{r['obligation_id']}" for r in must_not]
        return 'NON_GOAL_BOUNDARY',refs,{'non_goals':anchor.get('non_goals',[]),'must_not':must_not}
    if dimension=='TEST_CONTRADICTION':
        checks=validation.get('checks',[]); cases=validation.get('acceptance_cases',[])
        refs=[f"CHECK:{r['check_id']}" for r in checks]+[f"CASE:{r['case_id']}" for r in cases]
        return 'TEST_AND_CASE_PLAN',refs,{'checks':checks,'acceptance_cases':cases}
    if dimension=='MIGRATION_COMPATIBILITY_IMPACT':
        route_impact=[{'route_id':r['route_id'],'known_costs':r.get('known_costs',[]),'known_risks':r.get('known_risks',[])} for r in routes]
        refs=[f"ROUTE:{r['route_id']}" for r in routes]+[f"CHANGE_SCOPE:{anchor.get('change_scope')}"]
        return 'MIGRATION_COMPATIBILITY_BOUNDARY',refs,{'change_scope':anchor.get('change_scope'),'route_impact':route_impact}
    raise JoyflowError(f'unknown technical preflight dimension: {dimension}')


def expected_preflight_subject_binding(capsule: dict[str, Any], dimension: str) -> dict[str,Any]:
    subject_type,refs,payload=_task_bound_preflight_subject_payload(capsule,dimension)
    return {'subject_type':subject_type,'subject_refs':refs,'subject_digest':digest(payload)}

def validate_technical_route_space(capsule: dict[str, Any]) -> None:
    profile=load_model()['route_profiles'][capsule['route_profile']]
    if not profile['executable']:
        return
    decision=capsule['active_fibers']['decision_boundary']['payload']
    space=decision.get('technical_route_space')
    if not isinstance(space,dict):
        raise JoyflowError('executable decision boundary requires Brain technical route space')
    required={'planning_mode','source_structural_route_binding','owner','candidate_set_exhaustive','codex_alternative_route_allowed','required_dimensions','obligations','candidate_routes','route_change_boundaries'}
    if set(space)!=required or space['owner']!='WEB_BRAIN' or space['candidate_set_exhaustive'] is not False or space['codex_alternative_route_allowed'] is not True:
        raise JoyflowError('technical route space authority or openness mismatch')
    frame=(capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{}) or {}).get('structural_decision_frame')
    disposition=(capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{}) or {}).get('brain_architecture_disposition')
    if frame is None:
        if space['planning_mode']!='BRAIN_BOUNDED_FAST_PATH' or space['source_structural_route_binding'] is not None:
            raise JoyflowError('ordinary technical route space cannot claim Codex-first structural route lineage')
    else:
        if space['planning_mode']!='CODEX_STRUCTURAL_ROUTE_BRAIN_ACCEPTED' or not disposition or disposition.get('disposition')!='ACCEPT':
            raise JoyflowError('structural technical route space requires accepted Codex-first structural route lineage')
        expected_binding={'source_structural_return_digest':disposition['source_structural_return_digest'],'structural_question_id':frame['question_id'],'source_route_id':disposition['source_route_id'],'brain_disposition_digest':disposition['disposition_digest']}
        if space['source_structural_route_binding']!=expected_binding:
            raise JoyflowError('technical route space is not bound to the accepted Codex structural route')
        if not any(r.get('route_id')==disposition['source_route_id'] for r in space['candidate_routes']):
            raise JoyflowError('Brain final technical route does not preserve the accepted Codex structural route identity')
    model=load_model(); dimensions=model['technical_preflight_dimensions']; templates=model['technical_preflight_question_templates']
    if set(space['required_dimensions'])!=set(dimensions):
        raise JoyflowError('technical route space must include every required preflight dimension')
    obligations=space['obligations']; ids=[r.get('obligation_id') for r in obligations]; dims=[r.get('dimension') for r in obligations]
    if None in ids or len(ids)!=len(set(ids)) or set(dims)!=set(dimensions):
        raise JoyflowError('technical preflight obligations must uniquely cover every required dimension')
    registry=evidence_map(capsule)
    for row in obligations:
        required_row={'obligation_id','dimension','question','blocking','source_refs','subject_binding'}
        if set(row)!=required_row or row['dimension'] not in dimensions or row['question']!=templates[row['dimension']] or row['blocking'] is not True:
            raise JoyflowError('technical preflight obligation must use the canonical dimension question')
        expected=expected_preflight_subject_binding(capsule,row['dimension'])
        if row['subject_binding']!=expected:
            raise JoyflowError('technical preflight obligation is not bound to the current task subject')
        if row['source_refs']:
            require_refs(row['source_refs'],registry,f"technical obligation {row['obligation_id']}")
    routes=space['candidate_routes']; route_ids=[r.get('route_id') for r in routes]
    if not 1<=len(routes)<=3 or None in route_ids or len(route_ids)!=len(set(route_ids)):
        raise JoyflowError('Brain candidate routes must contain one to three unique routes')
    for route in routes:
        if set(route)!={'route_id','summary','expected_mechanisms','expected_paths','advantages','known_costs','known_risks','important_tradeoff_owner'} or not route['summary'] or not route['expected_mechanisms'] or not route['advantages']:
            raise JoyflowError('candidate route shape mismatch')
        if route['important_tradeoff_owner'] not in {'CODEX_WITHIN_BOUNDARY','WEB_BRAIN','USER'}:
            raise JoyflowError('candidate route tradeoff owner invalid')
        for path in route['expected_paths']:
            if not _valid_repo_path(path):
                raise JoyflowError('candidate route expected path is not repository-relative')
    bounds=space['route_change_boundaries']
    if set(bounds)!={'may_execute_without_reclosure','must_return_for_reclosure'} or not bounds['may_execute_without_reclosure'] or not bounds['must_return_for_reclosure']:
        raise JoyflowError('technical route change boundaries are incomplete')


def _bundle_source_registry_rows(bundle: dict[str,Any]) -> list[dict[str,Any]]:
    rows=[copy.deepcopy(row) for row in bundle.get('evidence_rows',[])]
    for row in bundle.get('derivation_rows',[]):
        rows.append({'evidence_id':row['derivation_id'],'authority':row['authority'],'kind':row['kind'],'ref':row['source_evidence_refs'][0],'claim':row['claim'],'claim_digest':row['claim_digest'],'produced_by':row['produced_by'],'subject_type':row['subject_type'],'subject_id':row['subject_id'],'raw_output_ref':None})
    rows=sorted(rows,key=lambda r:r['evidence_id'])
    if len({r['evidence_id'] for r in rows})!=len(rows):
        raise JoyflowError('Evidence Bundle source row IDs must be unique across facts and derivations')
    return rows


def source_evidence_row_digest_map(bundle: dict[str,Any]) -> dict[str,str]:
    return {row['evidence_id']:digest(row) for row in _bundle_source_registry_rows(bundle)}


def _source_derived_review_snapshot_payload(review: dict[str,Any]) -> dict[str,Any]:
    machine=[]
    for result in review.get('validation_results',[]):
        machine.append({'obligation_id':result.get('obligation_id'),'machine_results':copy.deepcopy(result.get('machine_results',[]))})
    machine=sorted(machine,key=lambda r:r['obligation_id'] or '')
    return {'source_projection_digest':review.get('source_projection_digest'),'source_codex_return_digest':review.get('source_codex_return_digest'),'source_evidence_bundle_digest':review.get('source_evidence_bundle_digest'),'source_task_object_lifecycle_digest':review.get('source_task_object_lifecycle_digest'),'source_execution_lifecycle_result_digest':review.get('source_execution_lifecycle_result_digest'),'source_execution_status':review.get('source_execution_status'),'review_target':copy.deepcopy(review.get('review_target')),'source_machine_results':machine,'source_evidence_row_digests':copy.deepcopy(review.get('source_evidence_row_digests',{})),'unresolved_followups':copy.deepcopy(review.get('unresolved_followups',[]))}


def source_derived_review_snapshot_digest(review: dict[str,Any]) -> str:
    return digest(_source_derived_review_snapshot_payload(review))

def validate_review_input_binding_structure(capsule: dict[str, Any], projection: dict[str, Any] | None = None,
                                  codex_return: dict[str, Any] | None = None,
                                  evidence_bundle: dict[str, Any] | None = None) -> None:
    fiber = capsule.get('active_fibers', {}).get('execution_review')
    if not fiber:
        return
    review = fiber['payload']
    if review.get('source_snapshot_digest')!=source_derived_review_snapshot_digest(review):
        raise JoyflowError('Brain review source-derived snapshot digest mismatch')
    project_id = capsule['task_anchor']['project_id']
    task_id = capsule['task_anchor']['task_id']
    round_id = capsule['task_progress']['cycle']
    expected = {'project_id': project_id, 'task_id': task_id, 'round_id': round_id}
    actual = {k: review.get(k) for k in expected}
    if actual != expected:
        raise JoyflowError('execution review is bound to another project/task/round')
    approval = capsule.get('approval_record', {})
    if approval.get('status') != 'APPROVED_FINAL':
        raise JoyflowError('execution review requires an active user mutation authorization')
    if projection is not None and approval.get('binding') != approval_binding(projection):
        raise JoyflowError('execution review Projection is outside the user-approved mutation execution envelope')
    packet_subject = _round_packet_subject(project_id, task_id, round_id, review['source_projection_digest'])
    registry = evidence_map(capsule)
    sealed_rows=review.get('source_evidence_row_digests')
    if not isinstance(sealed_rows,dict) or not sealed_rows or any(not isinstance(k,str) or not re.fullmatch(r'[0-9a-f]{64}',v or '') for k,v in sealed_rows.items()):
        raise JoyflowError('Brain review source Evidence snapshot is missing or malformed')
    for evidence_id,row_digest in sealed_rows.items():
        if evidence_id not in registry or digest(registry[evidence_id])!=row_digest:
            raise JoyflowError('Brain review rewrote or omitted one sealed source Evidence row')
    ret_ev = _evidence_for_subject(registry, review.get('source_codex_return_evidence_ref'),
        authority='EXECUTION_EVIDENCE', kinds={'CODEX_RETURN'}, subject_type='ROUND_PACKET',
        subject_id=packet_subject, producers={'CODEX','TOOL'}, context='source Codex return')
    bundle_ev = _evidence_for_subject(registry, review.get('source_evidence_bundle_ref'),
        authority='EXECUTION_EVIDENCE', kinds={'EVIDENCE_BUNDLE'}, subject_type='ROUND_PACKET',
        subject_id=packet_subject, producers={'CODEX','TOOL'}, context='source evidence bundle')
    if ret_ev.get('ref') != review.get('source_codex_return_digest') or bundle_ev.get('ref') != review.get('source_evidence_bundle_digest'):
        raise JoyflowError('review source evidence references do not bind the declared digests')
    supplied = [projection is not None, codex_return is not None, evidence_bundle is not None]
    if any(supplied) and not all(supplied):
        raise JoyflowError('review sealing requires Projection, Codex Return and Evidence Bundle together')
    if all(supplied):
        validate_codex_execution_return_structure(codex_return, projection, evidence_bundle)
        if projection['project_id'] != project_id or projection['task_id'] != task_id or projection['round_id'] != round_id:
            raise JoyflowError('review Projection belongs to another active round')
        if review.get('source_execution_status') != codex_return['execution_status']:
            raise JoyflowError('review source execution status differs from exact Codex Return')
        if (projection['projection_digest'] != review['source_projection_digest'] or
            codex_return['return_digest'] != review['source_codex_return_digest'] or
            evidence_bundle['evidence_bundle_digest'] != review['source_evidence_bundle_digest']):
            raise JoyflowError('review input digest binding mismatch')
        expected_source_rows=source_evidence_row_digest_map(evidence_bundle)
        if review.get('source_evidence_row_digests')!=expected_source_rows:
            raise JoyflowError('Brain review source Evidence snapshot differs from the exact Evidence Bundle')
        expected_registry_rows={r['evidence_id']:r for r in _bundle_source_registry_rows(evidence_bundle)}
        if any(registry.get(evidence_id)!=row for evidence_id,row in expected_registry_rows.items()):
            raise JoyflowError('Brain review source Evidence content differs from the exact Evidence Bundle')
        validate_task_object_lifecycle(projection)
        validate_execution_lifecycle_result_structure(codex_return['execution_lifecycle_result'],projection,codex_return)
        if review.get('source_task_object_lifecycle_digest')!=projection['task_object_lifecycle']['lifecycle_digest'] or review.get('source_execution_lifecycle_result_digest')!=codex_return['execution_lifecycle_result']['transition_digest']:
            raise JoyflowError('Brain review does not bind the exact task lifecycle transition')
        source_structural=codex_return['structural_execution_result']
        sr=review.get('structural_review') or {}
        if source_structural['status']=='NOT_APPLICABLE':
            if sr.get('status')!='NOT_REQUIRED' or sr.get('actual_consequence_ids')!=[]:
                raise JoyflowError('Brain structural review invented consequences absent from the Codex Return')
        else:
            expected_ids=[r['consequence_id'] for r in source_structural['actual_consequences']]
            if sr.get('approved_closure_digest')!=source_structural['approved_structural_closure_digest'] or sorted(sr.get('actual_consequence_ids',[]))!=sorted(expected_ids):
                raise JoyflowError('Brain structural review does not preserve the exact Codex structural consequence set')
            if source_structural['status']=='DEVIATION_DETECTED' and sr.get('status')!='RECLOSURE_REQUIRED':
                raise JoyflowError('Codex structural deviation must remain re-closure-required in Brain review')
        if codex_return['execution_status']=='BLOCKED':
            expected_target={'target_type':'BLOCKED_EXECUTION_RETURN','source_codex_return_digest':codex_return['return_digest'],'technical_preflight_status':codex_return['technical_preflight']['status'],'objection_finding_id':codex_return['technical_preflight']['objection']['finding_id'],'blocker_evidence_refs':copy.deepcopy(codex_return['blocker_evidence_refs']),'mutation_summary':copy.deepcopy(codex_return['mutation_summary']),'unresolved_items':copy.deepcopy(codex_return['unresolved_items'])}
        elif _repository_review_evidence(codex_return) is not None:
            repository_evidence=_repository_review_evidence(codex_return)
            expected_target={'target_type':'REPOSITORY_PR_HEAD','repository_id':repository_evidence['repository_id'],'pr_url':repository_evidence['pr_url'],'head_sha':repository_evidence['head_sha'],'actual_changed_paths':copy.deepcopy(repository_evidence['review_coverage_paths']),'changed_paths_evidence_ref':repository_evidence['diff_evidence_ref']}
        else:
            artifact=codex_return['artifact_evidence']
            lifecycle_result=codex_return['execution_lifecycle_result']['execution_result_object']
            validation=codex_return['execution_lifecycle_result']['final_validation_object']
            expected_target={'target_type':'ARTIFACT_OUTPUT_SET','output_set_digest':lifecycle_result['output_set_digest'],'outputs':copy.deepcopy(lifecycle_result['outputs']),'artifact_validation_evidence_refs':copy.deepcopy(validation['artifact_validation_evidence_refs']),'output_validation_coverage':copy.deepcopy(validation['output_validation_coverage'])}
        if review.get('review_target') != expected_target:
            raise JoyflowError('Brain review target does not deterministically match the exact Codex Return')
        returned_by_obligation: dict[str, list[dict[str, Any]]] = {}
        for machine_row in codex_return['machine_results']:
            returned_by_obligation.setdefault(machine_row['obligation_id'], []).append(machine_row)
        reviewed_results={r['obligation_id']:r for r in review.get('validation_results',[])}
        for obligation_id, review_row in reviewed_results.items():
            actual=sorted(returned_by_obligation.get(obligation_id,[]),key=lambda r:(r['check_id'],r['evidence_ref']))
            claimed=sorted(review_row.get('machine_results',[]),key=lambda r:(r['check_id'],r['evidence_ref']))
            if claimed != actual:
                raise JoyflowError('Brain review machine results differ from the exact Codex Return')
        if codex_return['execution_status']=='BLOCKED':
            if review.get('unresolved_followups') != codex_return['unresolved_items']:
                raise JoyflowError('blocked review followups must preserve exact Codex unresolved items')


def validate_review_input_binding(capsule: dict[str,Any], projection: dict[str,Any] | None=None, codex_return: dict[str,Any] | None=None, evidence_bundle: dict[str,Any] | None=None, *, source_repository: str | pathlib.Path | None=None, source_artifact: str | pathlib.Path | None=None, artifact_outputs: list[str | pathlib.Path] | None=None, artifact_output_root: str | pathlib.Path | None=None, replay_tests: bool=True, path_discovery_return: dict[str,Any] | None=None, path_discovery_projection: dict[str,Any] | None=None, source_materials: dict[str,str | pathlib.Path] | None=None) -> None:
    validate_review_input_binding_structure(capsule,projection,codex_return,evidence_bundle)
    if projection is not None and codex_return is not None and evidence_bundle is not None:
        validate_codex_execution_return(codex_return,projection,evidence_bundle,repository=source_repository,artifact=source_artifact,artifact_outputs=artifact_outputs,artifact_output_root=artifact_output_root,replay_tests=replay_tests,path_discovery_return=path_discovery_return,path_discovery_projection=path_discovery_projection,source_materials=source_materials)

def validate_execution_review(capsule: dict[str, Any]) -> None:
    fiber = capsule.get('active_fibers', {}).get('execution_review')
    if not fiber:
        raise JoyflowError('execution review fiber missing')
    validate_review_input_binding_structure(capsule)
    review = fiber['payload']
    source_blocked = review.get('source_execution_status') == 'BLOCKED'
    structural_review=review.get('structural_review')
    if not isinstance(structural_review,dict):
        raise JoyflowError('Brain execution review requires an explicit structural review disposition')
    validation = capsule['active_fibers']['validation']['payload']
    bindings = {r['obligation_id']: r for r in validation.get('obligation_registry', [])}
    results = review.get('validation_results', [])
    result_ids = [r.get('obligation_id') for r in results]
    if len(result_ids) != len(set(result_ids)) or set(result_ids) != set(bindings):
        raise JoyflowError('execution review must return exact validation obligation set')
    registry = evidence_map(capsule)
    check_map = {r['check_id']: r for r in validation.get('checks', [])}
    human_map = {r['validation_id']: r for r in validation.get('human_validation', [])}
    acceptance = review.get('user_acceptance')
    for result in results:
        oid = result['obligation_id']
        binding = bindings[oid]
        machine_rows = result.get('machine_results', [])
        human_rows = result.get('human_results', [])
        machine = {r['check_id']: r for r in machine_rows}
        humans = {r['validation_id']: r for r in human_rows}
        if len(machine) != len(machine_rows) or len(humans) != len(human_rows):
            raise JoyflowError('duplicate validation result identifiers')
        expected_machine=set(binding.get('check_ids', []))
        if source_blocked:
            if not set(machine).issubset(expected_machine):
                raise JoyflowError('blocked execution review contains an unplanned machine result')
            if humans:
                raise JoyflowError('blocked execution review cannot claim human validation results')
            for cid,row in machine.items():
                if row.get('actual_argv') != check_map[cid]['argv'] or row.get('actual_cwd_scope')!='SOURCE_ROOT' or row.get('actual_command') != check_map[cid]['command']:
                    raise JoyflowError(f'blocked machine result argv/cwd mismatch: {oid}:{cid}')
                rs,code=row.get('result'),row.get('exit_code')
                if rs=='PASS' and code!=0: raise JoyflowError('PASS machine result requires exit_code 0')
                if rs=='FAIL' and (code is None or code==0): raise JoyflowError('FAIL machine result requires nonzero exit_code')
                if rs=='NOT_RUN' and code is not None: raise JoyflowError('NOT_RUN machine result requires null exit_code')
                _evidence_for_subject(registry,row.get('evidence_ref'),authority='EXECUTION_EVIDENCE',kinds={'TEST_RESULT','PR_CHECK','RUNTIME_OUTPUT'},subject_type='VALIDATION_CHECK',subject_id=f'{oid}:{cid}',producers={'CODEX','TOOL'},context=f'blocked machine validation {cid}')
            if result.get('verdict')!='BLOCKED':
                raise JoyflowError('blocked execution validation obligation must remain BLOCKED')
        else:
            if set(machine) != expected_machine:
                raise JoyflowError('execution machine result coverage mismatch')
            for cid, row in machine.items():
                if row.get('actual_argv') != check_map[cid]['argv'] or row.get('actual_cwd_scope')!='SOURCE_ROOT' or row.get('actual_command') != check_map[cid]['command'] or row.get('result') != 'PASS' or row.get('exit_code') != 0:
                    raise JoyflowError(f'machine validation did not pass exact approved argv/cwd: {oid}:{cid}')
                _evidence_for_subject(registry, row.get('evidence_ref'), authority='EXECUTION_EVIDENCE',
                    kinds={'TEST_RESULT','PR_CHECK','RUNTIME_OUTPUT'}, subject_type='VALIDATION_CHECK',
                    subject_id=f'{oid}:{cid}', producers={'CODEX','TOOL'}, context=f'machine validation {cid}')
            expected_humans = set(binding.get('human_validation_ids', []))
            if acceptance == 'PASS':
                if set(humans) != expected_humans:
                    raise JoyflowError('human validation result coverage mismatch')
                for hid, row in humans.items():
                    if row.get('verdict') != 'PASS':
                        raise JoyflowError(f'human validation did not pass: {oid}:{hid}')
                    _evidence_for_subject(registry, row.get('evidence_ref'), authority='USER_DECISION',
                        kinds={'USER_ACCEPTANCE'}, subject_type='VALIDATION_CHECK', subject_id=f'{oid}:{hid}',
                        producers={'USER','WEB_BRAIN'}, context=f'human validation {hid}')
            elif humans:
                raise JoyflowError('human validation results may only be recorded with user acceptance PASS')
            expected_verdict = 'PASS' if not expected_humans or acceptance == 'PASS' else 'PENDING_USER_ACCEPTANCE'
            if result.get('verdict') != expected_verdict:
                raise JoyflowError('validation obligation verdict does not match machine/human status')

    target = review.get('review_target') or {}
    if source_blocked:
        if target.get('target_type')!='BLOCKED_EXECUTION_RETURN':
            raise JoyflowError('blocked Codex Return requires blocked-return review target')
        required=('source_codex_return_digest','technical_preflight_status','objection_finding_id','blocker_evidence_refs','mutation_summary','unresolved_items')
        if any(k not in target for k in required) or target.get('source_codex_return_digest')!=review.get('source_codex_return_digest'):
            raise JoyflowError('blocked execution review target is incomplete or bound to another Return')
        if not target.get('blocker_evidence_refs') or not target.get('unresolved_items'):
            raise JoyflowError('blocked execution review target requires blocker evidence and unresolved items')
        for ref in target['blocker_evidence_refs']:
            ev=registry.get(ref)
            if not ev or ev.get('authority')!='EXECUTION_EVIDENCE' or ev.get('kind')!='TECHNICAL_OBJECTION_DERIVATION' or ev.get('subject_type')!='TECHNICAL_PREFLIGHT_FINDING' or ev.get('subject_id')!=target['objection_finding_id'] or ev.get('produced_by')!='CODEX':
                raise JoyflowError('blocked review target evidence does not match its technical finding')
        target_subject_type,target_subject_id='CODEX_RETURN',target['source_codex_return_digest']
        if acceptance!='PENDING_USER_ACCEPTANCE':
            raise JoyflowError('blocked execution review cannot claim user acceptance outcome')
    else:
        requires_pr = _requires_pr(capsule)
        if requires_pr:
            if target.get('target_type') != 'REPOSITORY_PR_HEAD':
                raise JoyflowError('repository change requires PR-head review target')
            required = ('repository_id','pr_url','head_sha','actual_changed_paths','changed_paths_evidence_ref')
            if any(target.get(k) is None or target.get(k) == '' for k in required):
                raise JoyflowError('repository PR review target is incomplete')
            binding = capsule['active_fibers']['decision_boundary']['payload'].get('repository_binding') or {}
            if target['repository_id'] != binding.get('repository_id'):
                raise JoyflowError('PR review repository binding mismatch')
            diff_ev=_evidence_for_subject(registry, target['changed_paths_evidence_ref'], authority='EXECUTION_EVIDENCE',kinds={'REPOSITORY_DIFF'}, subject_type='PR_HEAD', subject_id=target['head_sha'],producers={'TOOL'}, context='changed paths')
            try:
                diff_claim=json.loads(diff_ev['claim'])
            except Exception as exc:
                raise JoyflowError('review changed-path evidence claim is not canonical JSON') from exc
            observation=diff_claim.get('observation',{})
            observed_object=diff_claim.get('observed_object',{})
            if diff_claim.get('capture_kind')!='REPOSITORY_DIFF' or observation.get('head_ref')!=target['head_sha'] or sorted(observation.get('changed_paths',[]))!=sorted(target['actual_changed_paths']) or observed_object.get('object_id')!=target['repository_id']:
                raise JoyflowError('review changed-path evidence does not bind the current PR target')
            if capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY':
                expected_coverage=sorted(capsule['task_anchor']['repository_anchor']['review_coverage_paths'])
                if sorted(target.get('actual_changed_paths',[]))!=expected_coverage or _allow_paths(capsule):
                    raise JoyflowError('existing PR replay review coverage differs from the exact frozen diff or mutation boundary is non-empty')
            else:
                allowed = _allow_paths(capsule)
                for path in target.get('actual_changed_paths', []):
                    if not _path_within_allowed(path, allowed):
                        raise JoyflowError(f'changed path outside allowed paths: {path}')
            target_subject_type, target_subject_id = 'PR_HEAD', target['head_sha']
        else:
            if target.get('target_type') != 'ARTIFACT_OUTPUT_SET':
                raise JoyflowError('artifact change requires exact Artifact output-set review target')
            outputs=target.get('outputs')
            if not isinstance(outputs,list) or not outputs or target.get('output_set_digest')!=_artifact_output_set_digest(outputs) or outputs!=_canonical_artifact_outputs(outputs):
                raise JoyflowError('artifact output-set review target identity is incomplete')
            identities=[(row.get('artifact_id'),row.get('artifact_digest')) for row in outputs]
            if len(identities)!=len(set(identities)) or any(not aid or not re.fullmatch(r'[0-9a-f]{64}',sha or '') for aid,sha in identities):
                raise JoyflowError('artifact output-set contains invalid or duplicate output identities')
            refs=target.get('artifact_validation_evidence_refs',[]); coverage=target.get('output_validation_coverage',[])
            if not refs or sorted(r.get('artifact_id') for r in coverage)!=sorted(aid for aid,_ in identities):
                raise JoyflowError('artifact output-set review requires exact per-output validation coverage')
            union=set(); digest_covered=set()
            identity_map={aid:sha for aid,sha in identities}
            for row in coverage:
                aid=row.get('artifact_id'); row_refs=row.get('validation_evidence_refs',[])
                if aid not in identity_map or not row_refs: raise JoyflowError('artifact output validation coverage is malformed')
                has_digest=False; has_test=False
                for ref in row_refs:
                    ev=registry.get(ref)
                    if not ev or ev.get('authority')!='EXECUTION_EVIDENCE' or ev.get('produced_by')!='TOOL': raise JoyflowError('artifact output-set validation reference is not a direct tool fact')
                    try: claim=json.loads(ev.get('claim',''))
                    except Exception as exc: raise JoyflowError('artifact output validation claim is not canonical JSON') from exc
                    obj=claim.get('observed_object',{})
                    if obj.get('object_id')!=aid or obj.get('ref_or_sha256')!=identity_map[aid]: raise JoyflowError('artifact output validation reference is bound to another output')
                    if ev.get('kind')=='ARTIFACT_SHA256_OBSERVATION' and ev.get('subject_type')=='ARTIFACT' and ev.get('subject_id')==identity_map[aid]: has_digest=True; digest_covered.add(aid)
                    elif ev.get('kind')=='TEST_RESULT' and ev.get('subject_type')=='VALIDATION_CHECK': has_test=True
                    else: raise JoyflowError('artifact output validation reference has an unsupported kind or subject')
                    union.add(ref)
                if not has_digest or not has_test: raise JoyflowError('each artifact output needs digest and test validation evidence')
            if union!=set(refs) or digest_covered!=set(identity_map):
                raise JoyflowError('artifact output-set validation evidence does not cover the exact output set')
            target_subject_type,target_subject_id='ARTIFACT_OUTPUT_SET',target['output_set_digest']
    structural_binding=(capsule.get('active_fibers',{}).get('decision_boundary',{}).get('payload',{}).get('technical_route_space',{}) or {}).get('source_structural_route_binding')
    if structural_binding is None:
        expected_structural={'status':'NOT_REQUIRED','approved_closure_digest':None,'actual_consequence_ids':[],'dispositions':[],'long_term_projection_disposition':'NO_REFOLD_REQUIRED'}
        if structural_review!=expected_structural:
            raise JoyflowError('ordinary Brain review cannot claim structural closure or refold results')
    else:
        required_sr={'status','approved_closure_digest','actual_consequence_ids','dispositions','long_term_projection_disposition'}
        if set(structural_review)!=required_sr or structural_review['approved_closure_digest']!=structural_binding['brain_disposition_digest']:
            raise JoyflowError('Brain structural review is not bound to the approved structural closure')
        if structural_review['status'] not in {'PRESERVED','RECLOSURE_REQUIRED'} or structural_review['long_term_projection_disposition'] not in {'NO_REFOLD_REQUIRED','REFOLD_REQUIRED'}:
            raise JoyflowError('Brain structural review status/refold disposition invalid')
        ids=structural_review['actual_consequence_ids']; disp=structural_review['dispositions']
        if len(ids)!=len(set(ids)) or len(disp)!=len(ids) or {r.get('consequence_id') for r in disp}!=set(ids):
            raise JoyflowError('Brain structural review must disposition every actual structural consequence exactly once')
        if any(set(r)!={'consequence_id','result','review_basis'} or r['result'] not in {'PRESERVED','AUTHORIZED_CHANGE','RECLOSURE_REQUIRED'} or not r['review_basis'] for r in disp):
            raise JoyflowError('Brain structural consequence disposition invalid')
        if any(r['result']=='RECLOSURE_REQUIRED' for r in disp) and review.get('brain_review_verdict')=='PASS':
            raise JoyflowError('Brain PASS cannot hide a structural consequence requiring re-closure')
    brain = review.get('brain_review_verdict')
    if source_blocked and brain == 'PASS':
        raise JoyflowError('Brain may not promote a blocked Codex Return to PASS')
    brain_refs = review.get('brain_review_evidence_refs', [])
    if brain == 'PENDING_BRAIN_REVIEW':
        if brain_refs:
            raise JoyflowError('pending Brain review cannot carry Brain review evidence')
    elif brain in {'PASS','BLOCK'}:
        if not brain_refs:
            raise JoyflowError('completed Brain review requires evidence refs')
        kinds = {'TECHNICAL_INFERENCE'} if source_blocked or target_subject_type=='ARTIFACT' else {'PR_REVIEW','TECHNICAL_INFERENCE'}
        for ref in brain_refs:
            _evidence_for_subject(registry, ref, authority='BRAIN_DERIVATION', kinds=kinds,
                subject_type=target_subject_type, subject_id=target_subject_id,
                producers={'WEB_BRAIN'}, context='Brain review')
    else:
        raise JoyflowError('invalid Brain review verdict')
    user_refs = review.get('user_acceptance_evidence_refs', [])
    na_reason = review.get('acceptance_not_applicable_reason')
    if acceptance == 'PENDING_USER_ACCEPTANCE':
        if user_refs or na_reason:
            raise JoyflowError('pending user acceptance cannot carry outcome evidence')
    elif acceptance in {'PASS','BLOCK'}:
        if not user_refs or na_reason:
            raise JoyflowError('user acceptance outcome requires evidence refs and no N/A reason')
        for ref in user_refs:
            _evidence_for_subject(registry, ref, authority='USER_DECISION', kinds={'USER_ACCEPTANCE'},
                subject_type=target_subject_type, subject_id=target_subject_id,
                producers={'USER','WEB_BRAIN'}, context='user acceptance')
    elif acceptance == 'NOT_APPLICABLE':
        if user_refs or not na_reason:
            raise JoyflowError('N/A user acceptance requires a reason and no acceptance evidence')
    else:
        raise JoyflowError('invalid user acceptance status')
    delta=review.get('rework_delta')
    if not isinstance(delta,list):
        raise JoyflowError('execution review requires explicit rework_delta list')
    required_failure=set()
    if source_blocked: required_failure.add('CODEX_BLOCK')
    if brain=='BLOCK': required_failure.add('BRAIN_REVIEW_BLOCK')
    if acceptance=='BLOCK': required_failure.add('USER_ACCEPTANCE_BLOCK')
    observed_failure=set()
    for row in delta:
        if set(row)!={'failure_source','affected_subject','remaining_gap','evidence_refs','next_allowed_action','reopen_scope'} or row.get('failure_source') not in {'CODEX_BLOCK','BRAIN_REVIEW_BLOCK','USER_ACCEPTANCE_BLOCK'} or not all(isinstance(row.get(k),str) and row[k].strip() for k in ('affected_subject','remaining_gap','next_allowed_action','reopen_scope')):
            raise JoyflowError('rework delta row invalid')
        refs=row.get('evidence_refs') or []
        if not refs:
            raise JoyflowError('rework delta requires evidence refs')
        observed_failure.add(row['failure_source'])
        if row['failure_source']=='CODEX_BLOCK':
            require_compatible_evidence(refs,registry,{'EXECUTION_EVIDENCE':None},'Codex-block rework delta')
        elif row['failure_source']=='BRAIN_REVIEW_BLOCK':
            for ref in refs:
                _evidence_for_subject(registry,ref,authority='BRAIN_DERIVATION',kinds={'PR_REVIEW','TECHNICAL_INFERENCE'},subject_type=target_subject_type,subject_id=target_subject_id,producers={'WEB_BRAIN'},context='Brain-review rework delta')
        else:
            for ref in refs:
                _evidence_for_subject(registry,ref,authority='USER_DECISION',kinds={'USER_ACCEPTANCE'},subject_type=target_subject_type,subject_id=target_subject_id,producers={'USER','WEB_BRAIN'},context='user-acceptance rework delta')
    if not required_failure.issubset(observed_failure):
        raise JoyflowError('failed execution/review/acceptance requires an explicit evidence-bound rework delta')
    if not required_failure and delta:
        raise JoyflowError('successful current round cannot carry a failure rework delta')
    if review.get('merge_status') != 'NOT_AUTHORIZED':
        raise JoyflowError('execution review cannot authorize merge')
    validate_scenario_cumulative_review(load_model(), capsule)

def validate_scenario_cumulative_review(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    fiber=capsule.get('active_fibers',{}).get('execution_review')
    if not fiber:
        return
    review=fiber['payload']
    registry=evidence_map(capsule)
    scenario=review.get('scenario_goal_review')
    cumulative=review.get('cumulative_review')
    if not isinstance(scenario,dict) or not isinstance(cumulative,dict):
        raise JoyflowError('Brain review lacks scenario-bounded and cumulative review dimensions')
    if set(scenario)!={'material_operating_assumptions','product_goal_result','machine_validation_status','human_acceptance_required','critical_high_loss_risks','known_limits'}:
        raise JoyflowError('scenario-bounded goal review shape invalid')
    expected_assumptions=capsule['task_anchor']['planning_context'].get('material_operating_assumptions',[])
    if scenario['material_operating_assumptions']!=expected_assumptions:
        raise JoyflowError('Brain review scenario assumptions drift from approved current task anchor')
    if scenario['product_goal_result'] not in {'PENDING_BRAIN_REVIEW','PASS','BLOCK'} or scenario['machine_validation_status'] not in {'PASS','BLOCKED','INCOMPLETE'}:
        raise JoyflowError('scenario goal review verdict invalid')
    blocked_risk=False
    for risk in scenario['critical_high_loss_risks']:
        if set(risk)!={'risk_id','risk','status','evidence_refs','affected_global_invariant_ids'} or not risk.get('risk_id') or not risk.get('risk') or risk.get('status') not in {'CONTROLLED_FOR_CURRENT_SCENARIO','RESIDUAL_ACCEPTED_BY_USER','BLOCKED'}:
            raise JoyflowError('critical high-loss risk review invalid')
        active_invariants={item['item_id'] for item in semantic_items(capsule) if active_material(item) and item.get('material_class')=='GLOBAL_INVARIANT'}
        affected=set(risk.get('affected_global_invariant_ids') or [])
        if not affected.issubset(active_invariants):
            raise JoyflowError('risk review references unknown or inactive GLOBAL_INVARIANT')
        if risk['status']=='RESIDUAL_ACCEPTED_BY_USER' and affected:
            raise JoyflowError('user residual-risk acceptance cannot waive an active GLOBAL_INVARIANT; change/supersede the product invariant and re-close instead')
        refs=risk.get('evidence_refs') or []
        if not refs:
            raise JoyflowError('critical high-loss risk conclusion requires evidence refs')
        if risk['status']=='CONTROLLED_FOR_CURRENT_SCENARIO':
            require_relevant_evidence(refs,registry,{'EXECUTION_EVIDENCE':{'TEST_RESULT','PR_CHECK','RUNTIME_OUTPUT'}},subject_type='RISK',subject_id=risk['risk_id'],context=f"controlled risk {risk['risk_id']}")
        elif risk['status']=='RESIDUAL_ACCEPTED_BY_USER':
            matched=False
            for ref in refs:
                try:
                    _evidence_for_subject(registry,ref,authority='USER_DECISION',kinds={'PRODUCT_DECISION'},subject_type='RISK',subject_id=risk['risk_id'],producers={'USER','WEB_BRAIN'},context=f"user-accepted residual risk {risk['risk_id']}")
                    matched=True
                except JoyflowError:
                    pass
            if not matched:
                raise JoyflowError('user-accepted residual risk lacks current user decision evidence bound to the exact risk')
        else:
            blocked_risk=True
            require_refs(refs,registry,f"blocked risk {risk['risk_id']}")
    if any(not isinstance(x,str) or not x.strip() for x in scenario['known_limits']):
        raise JoyflowError('known validation limits must be explicit text')
    if set(cumulative)!={'relevant_prior_behaviors','impact_comparison','exit_condition_results','residuals','verdict'}:
        raise JoyflowError('cumulative review shape invalid')
    planned={r['behavior_id']:r for r in capsule['task_anchor']['planning_context'].get('relevant_prior_behaviors',[])}
    actual_ids=[r.get('behavior_id') for r in cumulative['relevant_prior_behaviors']]
    if sorted(planned)!=sorted(actual_ids) or len(actual_ids)!=len(set(actual_ids)):
        raise JoyflowError('cumulative review must cover exactly current-task relevant prior behaviors')
    review_evidence_allowed={'EXECUTION_EVIDENCE':{'TEST_RESULT','PR_CHECK','RUNTIME_OUTPUT','REPOSITORY_DIFF','CODEX_RETURN','EVIDENCE_BUNDLE','TECHNICAL_OBJECTION_DERIVATION'}}
    expected_status={'PRESERVE_REQUIRED':'PRESERVED','CHANGE_AUTHORIZED':'CHANGED_WITH_RECLOSURE','SUPERSEDE_AUTHORIZED':'SUPERSEDED_WITH_RECLOSURE'}
    for row in cumulative['relevant_prior_behaviors']:
        if set(row)!={'behavior_id','status','evidence_refs','review_basis'} or row.get('status') not in {'PRESERVED','CHANGED_WITH_RECLOSURE','SUPERSEDED_WITH_RECLOSURE','BROKEN'} or not row.get('review_basis'):
            raise JoyflowError('prior behavior review row invalid')
        refs=row.get('evidence_refs') or []
        if not refs:
            raise JoyflowError('prior behavior review conclusion requires evidence refs')
        require_relevant_evidence(refs,registry,{**review_evidence_allowed,'BRAIN_DERIVATION':{'PR_REVIEW','TECHNICAL_INFERENCE'}},subject_type='PRIOR_BEHAVIOR',subject_id=row['behavior_id'],context=f"prior behavior review {row['behavior_id']}")
        disposition=planned[row['behavior_id']]['expected_disposition']
        if row['status']!=expected_status[disposition] and row['status']!='BROKEN':
            raise JoyflowError('prior behavior review status conflicts with approved expected disposition')
    impact=cumulative['impact_comparison']
    if set(impact)!={'expected_paths','observed_paths','unexpected_paths','status'} or impact.get('status') not in {'WITHIN_EXPECTED','EXPANDED_REQUIRES_RECLOSURE'}:
        raise JoyflowError('impact comparison invalid')
    if review.get('review_target',{}).get('target_type')=='REPOSITORY_PR_HEAD':
        context=_build_current_source_context(capsule)
        expected=sorted(context['review_coverage_paths'] if capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else context['selected_paths'])
        observed=sorted(review['review_target'].get('actual_changed_paths',[]))
        unexpected=sorted([path for path in observed if (path not in expected if capsule['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else not _path_within_allowed(path,expected))])
    else:
        expected=[]; observed=[]; unexpected=[]
    expected_status_value='EXPANDED_REQUIRES_RECLOSURE' if unexpected else 'WITHIN_EXPECTED'
    if sorted(impact['expected_paths'])!=expected or sorted(impact['observed_paths'])!=observed or sorted(impact['unexpected_paths'])!=unexpected or impact['status']!=expected_status_value:
        raise JoyflowError('impact comparison is not mechanically derived from current approved context and exact review target')
    exits=capsule['task_anchor']['planning_context'].get('exit_conditions',[])
    exit_rows=cumulative['exit_condition_results']
    if [r.get('condition') for r in exit_rows]!=exits or len(exit_rows)!=len(exits):
        raise JoyflowError('cumulative review must consume each current change-unit exit condition exactly once')
    for row in exit_rows:
        if set(row)!={'condition','status','evidence_refs','review_basis'} or row.get('status') not in {'PENDING','SATISFIED','BLOCKED'} or not row.get('review_basis'):
            raise JoyflowError('exit condition result invalid')
        if row['status'] in {'SATISFIED','BLOCKED'}:
            require_relevant_evidence(row.get('evidence_refs') or [],registry,{'BRAIN_DERIVATION':{'PR_REVIEW','TECHNICAL_INFERENCE'},'USER_DECISION':{'USER_ACCEPTANCE','PRODUCT_DECISION'},'EXECUTION_EVIDENCE':{'TEST_RESULT','PR_CHECK','RUNTIME_OUTPUT'}},subject_type='EXIT_CONDITION',subject_id=support_subject_id(row['condition']),context=f"exit condition {row['condition']}")
        elif row.get('evidence_refs'):
            raise JoyflowError('pending exit condition cannot claim final evidence')
    for row in cumulative['residuals']:
        if set(row)!={'issue','material_risk','reopen_trigger'} or not all(isinstance(row.get(k),str) and row[k].strip() for k in row):
            raise JoyflowError('cumulative residual must state issue, material risk and reopen trigger')
    if cumulative['verdict'] not in {'PENDING_BRAIN_REVIEW','PASS','BLOCK'}:
        raise JoyflowError('cumulative review verdict invalid')
    brain=review.get('brain_review_verdict')
    if brain=='PASS':
        if scenario['product_goal_result']!='PASS' or scenario['machine_validation_status']!='PASS' or cumulative['verdict']!='PASS':
            raise JoyflowError('Brain PASS requires scenario goal and cumulative review PASS')
        if blocked_risk:
            raise JoyflowError('Brain PASS cannot coexist with a blocked high-loss risk')
        for row in cumulative['relevant_prior_behaviors']:
            if row['status']=='BROKEN':
                raise JoyflowError('Brain PASS cannot hide a broken relevant prior behavior')
        if impact['status']!='WITHIN_EXPECTED':
            raise JoyflowError('Brain PASS cannot hide expanded observed impact')
        if any(r['status']!='SATISFIED' for r in exit_rows):
            raise JoyflowError('Brain PASS requires every current change-unit exit condition satisfied')
    if impact['status']=='EXPANDED_REQUIRES_RECLOSURE' and brain=='PASS':
        raise JoyflowError('expanded observed impact requires Brain re-closure')

def path_readiness_gate(capsule: dict[str, Any]) -> str:
    fiber=capsule.get('active_fibers',{}).get('repository_evidence')
    if not fiber:
        return 'NOT_REQUIRED'
    try:
        validate_path_discovery_state(load_model(), capsule)
    except JoyflowError:
        return 'BLOCK'
    state=fiber['payload']['path_discovery']
    if capsule['route_profile']=='READ_ONLY_DISCOVERY':
        return 'NEEDS_LOCAL_DISCOVERY'
    if capsule['task_anchor']['change_scope']=='REPOSITORY_CHANGE':
        return 'PASS' if state['final_allowed_paths_status']=='CONFIRMED' else 'BLOCK'
    return 'PASS'

def _valid_merge_candidate_freeze_digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None

def validate_repository_acceptance_freeze_binding(capsule: dict[str, Any]) -> None:
    """Keep repository acceptance/merge-decision lifecycle behind the existing exact freeze boundary.

    The standalone Capsule can mechanically prove the presence of the bound freeze digest.
    Operational sealing additionally consumes the exact Merge Candidate Freeze object via
    validate_merge_candidate_freeze_seal_input().
    """
    if not _requires_pr(capsule):
        return
    review = capsule.get('active_fibers', {}).get('execution_review', {}).get('payload')
    if not isinstance(review, dict):
        return
    stage = capsule['task_progress']['stage']
    acceptance = review.get('user_acceptance')
    freeze_bound = _valid_merge_candidate_freeze_digest(review.get('merge_candidate_freeze_digest'))
    if stage in {'USER_ACCEPTANCE', 'MERGE_DECISION'} and not freeze_bound:
        raise JoyflowError(f'{stage} repository Capsule requires the current Merge Candidate Freeze digest')
    if acceptance in {'PASS', 'BLOCK', 'NOT_APPLICABLE'} and not freeze_bound:
        raise JoyflowError('repository user acceptance outcome requires the current Merge Candidate Freeze digest')
    if stage == 'MERGE_DECISION' and acceptance not in {'PASS', 'NOT_APPLICABLE'}:
        raise JoyflowError('MERGE_DECISION requires a completed post-freeze user acceptance disposition')

def validate_merge_candidate_freeze_seal_input(capsule: dict[str, Any], previous: dict[str, Any] | None, merge_candidate_freeze: dict[str, Any] | None) -> None:
    """Bind operational USER_ACCEPTANCE/MERGE_DECISION sealing to the exact existing freeze object."""
    if not _requires_pr(capsule):
        if merge_candidate_freeze is not None:
            raise JoyflowError('Merge Candidate Freeze input is only valid for repository PR tasks')
        return
    review = capsule.get('active_fibers', {}).get('execution_review', {}).get('payload')
    if not isinstance(review, dict):
        return
    stage = capsule['task_progress']['stage']
    acceptance = review.get('user_acceptance')
    requires_exact = stage in {'USER_ACCEPTANCE', 'MERGE_DECISION'} or acceptance in {'PASS', 'BLOCK', 'NOT_APPLICABLE'}
    if not requires_exact:
        if merge_candidate_freeze is not None:
            raise JoyflowError('Merge Candidate Freeze must not be injected before the post-review freeze boundary')
        return
    if merge_candidate_freeze is None:
        raise JoyflowError('operational repository acceptance sealing requires the exact Merge Candidate Freeze object')
    validate_schema(merge_candidate_freeze, MERGE_FREEZE_SCHEMA)
    if merge_candidate_freeze.get('freeze_digest') != digest(strip_digest(merge_candidate_freeze, 'freeze_digest')):
        raise JoyflowError('Merge Candidate Freeze digest mismatch during Capsule sealing')
    if review.get('merge_candidate_freeze_digest') != merge_candidate_freeze['freeze_digest']:
        raise JoyflowError('Capsule is not bound to the exact supplied Merge Candidate Freeze')
    target = review.get('review_target') or {}
    expected = {
        'project_id': capsule['task_anchor']['project_id'],
        'task_id': capsule['task_anchor']['task_id'],
        'round_id': capsule['task_progress']['cycle'],
        'repository_id': target.get('repository_id'),
        'head_sha': target.get('head_sha'),
    }
    if any(merge_candidate_freeze.get(k) != v for k, v in expected.items()):
        raise JoyflowError('Merge Candidate Freeze belongs to another task round or PR Head')
    if stage == 'USER_ACCEPTANCE' and previous is not None:
        if previous['task_progress']['stage'] != 'BRAIN_REVIEW':
            raise JoyflowError('USER_ACCEPTANCE must consume the immediately preceding Brain Review PASS Capsule')
        previous_review = previous.get('active_fibers', {}).get('execution_review', {}).get('payload', {})
        if previous_review.get('brain_review_verdict') != 'PASS':
            raise JoyflowError('Merge Candidate Freeze boundary requires immediately preceding Brain Review PASS')
        if merge_candidate_freeze.get('brain_review_capsule_digest') != previous.get('capsule_digest'):
            raise JoyflowError('Merge Candidate Freeze is not bound to the exact preceding Brain Review PASS Capsule')

def compute_gate_snapshot(capsule: dict[str, Any]) -> dict[str, Any]:
    model = load_model()
    profile = model['route_profiles'][capsule['route_profile']]
    active = capsule.get('active_fibers', {})
    semantic_pass = 'semantic' in active and (not capsule.get('unresolved_blockers')) and all((not (active_material(i) and i['status'] == 'UNRESOLVED') for i in semantic_items(capsule)))
    repo_required = bool(_required_fact_slots(model, capsule))
    repo_pass = not repo_required or 'repository_evidence' in active
    if repo_pass and 'repository_evidence' in active:
        try:
            validate_repository_readiness(model, capsule, require_complete=True)
        except JoyflowError:
            repo_pass = False
    boundary_pass = not profile['executable'] or 'decision_boundary' in active
    validation_pass = 'validation' in active and bool(active['validation']['payload'].get('obligation_registry')) if profile['executable'] else ('validation' in active or profile['validation_depth'] == 'NONE')
    authority_pass = not profile['executable'] or _valid_execution_approval_record(capsule)
    path_gate = path_readiness_gate(capsule)
    path_ready_for_projection = (path_gate == 'NEEDS_LOCAL_DISCOVERY') if capsule['route_profile'] == 'READ_ONLY_DISCOVERY' else (path_gate in {'PASS','NOT_REQUIRED'})
    projection_stage_ready = capsule['task_progress']['stage'] in (model['approval_requirements']['read_only_projection_ready_stages'] if capsule['route_profile']=='READ_ONLY_DISCOVERY' else model['projection_ready_stages'])
    projection_pass = profile['executable'] and projection_stage_ready and semantic_pass and repo_pass and boundary_pass and validation_pass and authority_pass and path_ready_for_projection and (not capsule.get('unresolved_blockers'))
    review_active = profile['executable'] and capsule['task_progress']['stage'] in model['execution_review_required_stages']
    codex_return_gate = 'NOT_ACTIVE'
    brain_review_gate = 'NOT_ACTIVE'
    user_acceptance_gate = 'NOT_ACTIVE'
    pr_review_gate = 'NOT_ACTIVE'
    artifact_review_gate = 'NOT_ACTIVE'
    merge_gate = 'NOT_ACTIVE'
    review = active.get('execution_review', {}).get('payload', {})
    if review_active:
        try:
            validate_execution_review(capsule)
            codex_return_gate = 'PASS'
            brain = review.get('brain_review_verdict')
            brain_review_gate = 'PASS' if brain == 'PASS' else ('BLOCK' if brain == 'BLOCK' else 'NEEDS_BRAIN_REVIEW')
            acceptance = review.get('user_acceptance')
            if _requires_pr(capsule):
                freeze_bound = _valid_merge_candidate_freeze_digest(review.get('merge_candidate_freeze_digest'))
                if not freeze_bound:
                    user_acceptance_gate = 'BLOCK' if acceptance in {'PASS','BLOCK','NOT_APPLICABLE'} else 'NOT_ACTIVE'
                else:
                    user_acceptance_gate = 'PASS' if acceptance in {'PASS','NOT_APPLICABLE'} else ('BLOCK' if acceptance == 'BLOCK' else 'NEEDS_USER_ACCEPTANCE')
                pr_review_gate = 'PASS' if brain_review_gate == 'PASS' else 'BLOCK'
                if pr_review_gate == 'PASS' and freeze_bound and user_acceptance_gate == 'PASS' and not review.get('unresolved_followups'):
                    merge_gate = 'MERGE_READY'
                elif pr_review_gate == 'PASS' and freeze_bound:
                    merge_gate = 'NEEDS_USER_ACCEPTANCE'
                else:
                    merge_gate = 'NOT_ACTIVE'
            else:
                user_acceptance_gate = 'PASS' if acceptance in {'PASS','NOT_APPLICABLE'} else ('BLOCK' if acceptance == 'BLOCK' else 'NEEDS_USER_ACCEPTANCE')
                artifact_review_gate = 'PASS' if brain_review_gate == 'PASS' else 'BLOCK'
        except JoyflowError:
            codex_return_gate = 'BLOCK'
            brain_review_gate = 'BLOCK'
            user_acceptance_gate = 'BLOCK'
            if _requires_pr(capsule): pr_review_gate = 'BLOCK'
            else: artifact_review_gate = 'BLOCK'
    snapshot = {
        'semantic_gate':'PASS' if semantic_pass else 'BLOCK',
        'repository_evidence_gate':'PASS' if repo_pass else 'BLOCK',
        'path_readiness_gate':path_gate,
        'boundary_gate':'PASS' if boundary_pass else 'BLOCK',
        'validation_gate':'PASS' if validation_pass else 'BLOCK',
        'authority_gate':'PASS' if authority_pass else (('NEEDS_BRAIN_READ_ONLY_AUTHORIZATION' if profile['execution_mode']=='READ_ONLY' else 'NEEDS_USER_APPROVAL') if profile['executable'] else 'NOT_REQUIRED'),
        'projection_gate':'PASS' if projection_pass else 'BLOCK',
        'execution_review_gate':codex_return_gate,
        'codex_return_gate':codex_return_gate,
        'brain_review_gate':brain_review_gate,
        'user_acceptance_gate':user_acceptance_gate,
        'pr_review_gate':pr_review_gate,
        'artifact_review_gate':artifact_review_gate,
        'merge_gate':merge_gate,
        'derived_from_capsule_digest':capsule.get('capsule_digest')
    }
    snapshot['gate_snapshot_digest']=digest(strip_digest(snapshot,'gate_snapshot_digest'))
    return snapshot

def validate_derived_gates(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    if capsule.get('derived_gates') != compute_gate_snapshot(capsule):
        raise JoyflowError('derived gate snapshot mismatch')

def validate_stage_gate_requirements(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    stage = capsule['task_progress']['stage']
    profile = model['route_profiles'][capsule['route_profile']]
    gates = capsule['derived_gates']
    if profile['executable'] and stage == 'BRAIN_REVIEW' and gates['codex_return_gate'] != 'PASS':
        raise JoyflowError('BRAIN_REVIEW requires a valid current-round Codex Return and Evidence Bundle')
    if profile['executable'] and stage == 'USER_ACCEPTANCE':
        for name in ('codex_return_gate','brain_review_gate'):
            if gates[name] != 'PASS': raise JoyflowError(f'USER_ACCEPTANCE blocked by {name}')
        if _requires_pr(capsule) and not _valid_merge_candidate_freeze_digest(capsule['active_fibers']['execution_review']['payload'].get('merge_candidate_freeze_digest')):
            raise JoyflowError('USER_ACCEPTANCE requires the current Merge Candidate Freeze binding')
    if stage == 'MERGE_DECISION':
        if not _requires_pr(capsule):
            raise JoyflowError('MERGE_DECISION is only valid for repository PR tasks')
        for name in ('codex_return_gate','brain_review_gate','user_acceptance_gate','pr_review_gate'):
            if gates[name] != 'PASS': raise JoyflowError(f'MERGE_DECISION blocked by {name}')
        review = capsule['active_fibers']['execution_review']['payload']
        if not _valid_merge_candidate_freeze_digest(review.get('merge_candidate_freeze_digest')):
            raise JoyflowError('MERGE_DECISION requires the current Merge Candidate Freeze binding')
        if review.get('unresolved_followups'):
            raise JoyflowError('unresolved followups block MERGE_DECISION')
    if stage == 'CLOSED':
        if profile['executable']:
            if _requires_pr(capsule):
                raise JoyflowError('repository tasks close through observed merge result, not by closing the temporary capsule')
            for name in ('codex_return_gate','brain_review_gate','user_acceptance_gate','artifact_review_gate'):
                if gates[name] != 'PASS': raise JoyflowError(f'CLOSED artifact task blocked by {name}')
            if capsule['active_fibers']['execution_review']['payload'].get('unresolved_followups'):
                raise JoyflowError('unresolved followups block artifact closure')
        else:
            for name in ('semantic_gate','repository_evidence_gate','validation_gate'):
                if gates[name] != 'PASS': raise JoyflowError(f'CLOSED non-executable task blocked by {name}')

def expected_approval_scope(capsule: dict[str, Any]) -> str:
    profile=load_model()['route_profiles'][capsule['route_profile']]
    return load_model()['approval_requirements']['scope_by_execution_mode'][profile['execution_mode']]

def _authorization_expectation(capsule: dict[str, Any]) -> tuple[str,str,str]:
    model=load_model(); profile=model['route_profiles'][capsule['route_profile']]; mode=profile['execution_mode']; req=model['approval_requirements']
    return req['status_by_execution_mode'][mode], req['basis_by_execution_mode'][mode], req['scope_by_execution_mode'][mode]

def _approval_record_shape(capsule: dict[str, Any], projection: dict[str, Any] | None = None) -> bool:
    record=capsule.get('approval_record'); model=load_model()
    if not isinstance(record,dict) or record.get('owner')!=model['approval_requirements']['record_owner']:
        return False
    expected_status,expected_basis,expected_scope=_authorization_expectation(capsule)
    if record.get('scope')!=expected_scope or record.get('status')!=expected_status or record.get('basis')!=expected_basis or not record.get('decision_ref'):
        return False
    if projection is None:
        return isinstance(record.get('binding'),dict)
    return record.get('binding')==approval_binding(projection)

def _valid_execution_approval_record(capsule: dict[str, Any], projection: dict[str, Any] | None=None) -> bool:
    return _approval_record_shape(capsule, projection)

def _default_evidence_transport_plan() -> dict[str,Any]:
    return {'mode':'INLINE','transport_role':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY','github_surface':None,'trigger_conditions':[],'retention_policy':'EPHEMERAL_BY_DEFAULT','retention_reason':None,'cleanup':{'trigger':'TASK_TERMINAL','action':'DELETE_EXACT_TEMPORARY_REF','preauthorized':False,'background_service_forbidden':True},'fallback_mode':'MANUAL_FALLBACK','product_pr_promotion_forbidden':True,'product_main_or_development_branch_forbidden':True}

def validate_evidence_transport_plan(projection: dict[str,Any]) -> None:
    plan=projection.get('delivery',{}).get('evidence_transport'); cleanup=(plan or {}).get('cleanup') or {}; surface=(plan or {}).get('github_surface')
    if not isinstance(plan,dict) or plan.get('transport_role')!='CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY': raise JoyflowError('delivery must carry one exact current-round Evidence Bundle transport plan')
    if plan.get('product_pr_promotion_forbidden') is not True or plan.get('product_main_or_development_branch_forbidden') is not True: raise JoyflowError('Evidence transport may not enter product PR/merge promotion or product main/development history')
    if cleanup.get('background_service_forbidden') is not True: raise JoyflowError('Evidence cleanup may not require a persistent background service')
    if plan.get('mode')=='GITHUB_EXACT_OBJECT_IF_NEEDED':
        if projection.get('execution_mode')!='MUTATING': raise JoyflowError('read-only Brain authorization cannot authorize GitHub Evidence write mutation')
        if not isinstance(surface,dict): raise JoyflowError('GitHub Evidence transport requires an exact approved temporary surface')
        ref=surface.get('temporary_ref') or ''
        prefix=load_model().get('evidence_transport_policy',{}).get('temporary_ref_namespace','refs/heads/joyflow-evidence/')
        if not ref.startswith(prefix) or '..' in pathlib.PurePosixPath(ref).parts or '//' in ref:
            raise JoyflowError('Evidence transport ref must stay inside the dedicated positive Joyflow Evidence namespace')
        if surface.get('side_effect_status') not in {'NONE','EXPLICITLY_INCLUDED_IN_APPROVED_EXECUTION_OBJECT'} or not surface.get('side_effect_basis'): raise JoyflowError('Evidence transport side effects are not closed inside the approved execution object')
        if plan.get('retention_policy')=='EPHEMERAL_BY_DEFAULT':
            if cleanup.get('trigger')!='TASK_TERMINAL' or cleanup.get('action')!='DELETE_EXACT_TEMPORARY_REF' or cleanup.get('preauthorized') is not True or plan.get('retention_reason') is not None: raise JoyflowError('ephemeral GitHub Evidence transport requires exact preauthorized terminal cleanup')
        else:
            if not plan.get('retention_reason') or cleanup.get('trigger')!='NOT_APPLICABLE_RETAINED' or cleanup.get('action')!='NO_DELETE_RETAINED': raise JoyflowError('retained Evidence requires an explicit material non-reproducibility reason')
    else:
        if surface is not None: raise JoyflowError('non-GitHub Evidence transport cannot carry a GitHub write surface')
        if cleanup.get('preauthorized') is not False: raise JoyflowError('non-GitHub Evidence transport cannot claim preauthorized remote cleanup')

def validate_current_review_transport_plan(projection: dict[str,Any]) -> None:
    plan=projection.get('delivery',{}).get('current_review_transport')
    if plan is None:
        return
    cleanup=(plan or {}).get('cleanup') or {}; surface=(plan or {}).get('github_surface')
    if not isinstance(plan,dict) or plan.get('transport_role')!='CURRENT_PR_REVIEW_INPUT_TRANSPORT':
        raise JoyflowError('current review transport must use its distinct transport role')
    if projection.get('execution_mode')!='MUTATING' or projection.get('delivery',{}).get('requires_pr') is not True:
        raise JoyflowError('current review transport is available only to user-approved repository PR execution')
    if plan.get('product_pr_promotion_forbidden') is not True or plan.get('product_main_or_development_branch_forbidden') is not True:
        raise JoyflowError('current review transport may not enter product PR or main/development history')
    if cleanup.get('background_service_forbidden') is not True:
        raise JoyflowError('current review transport cleanup may not require a background service')
    if plan.get('mode')=='GITHUB_EXACT_OBJECT_IF_NEEDED':
        if not isinstance(surface,dict): raise JoyflowError('GitHub current review transport requires an approved temporary surface')
        ref=surface.get('temporary_ref') or ''
        prefix=load_model().get('current_review_transport_policy',{}).get('temporary_ref_namespace','refs/heads/joyflow-evidence/')
        if not ref.startswith(prefix) or '..' in pathlib.PurePosixPath(ref).parts or '//' in ref:
            raise JoyflowError('current review transport ref must stay inside the dedicated temporary namespace')
        if surface.get('side_effect_status') not in {'NONE','EXPLICITLY_INCLUDED_IN_APPROVED_EXECUTION_OBJECT'} or not surface.get('side_effect_basis'):
            raise JoyflowError('current review transport side effects are outside the approved execution object')
        if plan.get('retention_policy')=='EPHEMERAL_BY_DEFAULT':
            if cleanup.get('trigger')!='TASK_TERMINAL' or cleanup.get('action')!='DELETE_EXACT_TEMPORARY_REF' or cleanup.get('preauthorized') is not True or plan.get('retention_reason') is not None:
                raise JoyflowError('ephemeral current review transport requires exact preauthorized terminal cleanup')
        elif not plan.get('retention_reason') or cleanup.get('trigger')!='NOT_APPLICABLE_RETAINED' or cleanup.get('action')!='NO_DELETE_RETAINED':
            raise JoyflowError('retained current review transport requires an explicit non-reproducibility reason')
    else:
        if surface is not None: raise JoyflowError('non-GitHub current review transport cannot carry a GitHub surface')
        if cleanup.get('preauthorized') is not False: raise JoyflowError('non-GitHub current review transport cannot claim remote cleanup approval')

def evidence_bundle_transport_bytes(evidence_bundle: dict[str,Any]) -> bytes:
    validate_schema(evidence_bundle,EVIDENCE_BUNDLE_SCHEMA)
    if evidence_bundle.get('evidence_bundle_digest')!=digest(strip_digest(evidence_bundle,'evidence_bundle_digest')):
        raise JoyflowError('Evidence Bundle digest mismatch before transport')
    return canonical_bytes(evidence_bundle)

def validate_evidence_transport_receipt_structure(receipt: dict[str,Any], projection: dict[str,Any], evidence_bundle: dict[str,Any]) -> None:
    validate_schema(receipt,EVIDENCE_TRANSPORT_RECEIPT_SCHEMA)
    if receipt['receipt_digest']!=digest(strip_digest(receipt,'receipt_digest')): raise JoyflowError('Evidence transport receipt digest mismatch')
    expected={'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'evidence_bundle_digest':evidence_bundle['evidence_bundle_digest']}
    if any(receipt.get(k)!=v for k,v in expected.items()): raise JoyflowError('Evidence transport receipt is bound to another current-round Evidence Bundle')
    data=evidence_bundle_transport_bytes(evidence_bundle)
    if receipt.get('object_encoding')!='CANONICAL_JSON_UTF8' or receipt.get('object_bytes')!=len(data) or receipt.get('object_sha256')!=hashlib.sha256(data).hexdigest():
        raise JoyflowError('Evidence transport object identity is not the exact canonical current-round Evidence Bundle bytes')
    plan=projection.get('delivery',{}).get('evidence_transport') or {}; surface=plan.get('github_surface') or {}
    if plan.get('mode')!='GITHUB_EXACT_OBJECT_IF_NEEDED': raise JoyflowError('GitHub Evidence receipt cannot bind a non-GitHub transport plan')
    if receipt.get('repository_id')!=surface.get('repository_id') or receipt.get('temporary_ref')!=surface.get('temporary_ref'):
        raise JoyflowError('Evidence transport receipt escaped the approved transport-only repository/ref surface')
    prefix=(surface.get('path_prefix') or '').rstrip('/')
    path=receipt.get('exact_path') or ''
    if not prefix or not (path==prefix or path.startswith(prefix+'/')):
        raise JoyflowError('Evidence transport receipt escaped the approved transport path prefix')
    if receipt.get('retention_policy')!=plan.get('retention_policy') or receipt.get('cleanup_trigger')!=(plan.get('cleanup') or {}).get('trigger'):
        raise JoyflowError('Evidence transport receipt changed the approved retention/cleanup lifecycle')

def verify_evidence_transport_receipt_against_object(receipt: dict[str,Any], transport_object: str | pathlib.Path, evidence_bundle: dict[str,Any]) -> None:
    data=pathlib.Path(transport_object).read_bytes()
    expected=evidence_bundle_transport_bytes(evidence_bundle)
    if data!=expected:
        raise JoyflowError('GitHub exact-object bytes are not the exact canonical Evidence Bundle bytes')
    if len(data)!=receipt['object_bytes'] or hashlib.sha256(data).hexdigest()!=receipt['object_sha256']:
        raise JoyflowError('GitHub exact-object transport bytes do not match the receipt')

def _task_terminal_evidence_from_merge_pointer(completion_pointer: dict[str,Any]) -> dict[str,Any]:
    validate_schema(completion_pointer,COMPLETION_POINTER_SCHEMA)
    if completion_pointer.get('pointer_digest')!=digest(strip_digest(completion_pointer,'pointer_digest')):
        raise JoyflowError('task completion pointer digest mismatch')
    return {'status':'MERGED','evidence_ref':completion_pointer.get('repository_evidence_ref') or 'repository:merge-observed','evidence_digest':completion_pointer['pointer_digest']}

def build_evidence_transport_cleanup_continuation(
    projection: dict[str,Any], approval_record: dict[str,Any], receipt: dict[str,Any], evidence_bundle: dict[str,Any],
    completion_pointer: dict[str,Any] | None=None, merge_candidate_freeze: dict[str,Any] | None=None,
    user_acceptance_capsule: dict[str,Any] | None=None, user_authorization: dict[str,Any] | None=None, *, terminal_evidence: dict[str,Any] | None=None,
) -> dict[str,Any]:
    validate_evidence_transport_plan(projection)
    plan=projection['delivery']['evidence_transport']; cleanup=plan['cleanup']
    if plan.get('mode')!='GITHUB_EXACT_OBJECT_IF_NEEDED' or plan.get('retention_policy')!='EPHEMERAL_BY_DEFAULT' or cleanup.get('preauthorized') is not True or cleanup.get('action')!='DELETE_EXACT_TEMPORARY_REF':
        raise JoyflowError('Evidence transport cleanup continuation requires an exact preauthorized ephemeral GitHub transport plan')
    if projection.get('execution_mode')!='MUTATING': raise JoyflowError('Evidence transport cleanup continuation requires the original user-approved mutating execution object')
    if not isinstance(approval_record,dict) or approval_record.get('status')!='APPROVED_FINAL' or approval_record.get('basis')!='CURRENT_EXPLICIT_USER_DECISION':
        raise JoyflowError('Evidence transport cleanup continuation requires the original explicit user execution approval')
    if approval_record.get('binding')!=approval_binding(projection): raise JoyflowError('Evidence cleanup original approval is outside this mutation execution envelope')
    validate_evidence_transport_receipt_structure(receipt,projection,evidence_bundle)
    if terminal_evidence is None:
        if completion_pointer is None or merge_candidate_freeze is None or user_acceptance_capsule is None or user_authorization is None:
            raise JoyflowError('Evidence cleanup requires exact task-terminal evidence')
        validate_completion_pointer(completion_pointer,merge_candidate_freeze,user_acceptance_capsule,user_authorization)
        if any(completion_pointer.get(k)!=projection.get(k) for k in ('project_id','task_id','round_id')):
            raise JoyflowError('Evidence cleanup terminal condition belongs to another task round')
        terminal_evidence=_task_terminal_evidence_from_merge_pointer(completion_pointer)
    allowed=set(load_model().get('evidence_transport_policy',{}).get('cleanup_supported_terminal_statuses',[]))
    if not isinstance(terminal_evidence,dict) or terminal_evidence.get('status') not in allowed or not terminal_evidence.get('evidence_ref') or not re.fullmatch(r'[0-9a-f]{64}',terminal_evidence.get('evidence_digest') or ''):
        raise JoyflowError('Evidence cleanup terminal evidence is missing or not an allowed terminal status')
    surface=plan['github_surface']
    row={'artifact_type':'EVIDENCE_TRANSPORT_CLEANUP_CONTINUATION','owner':'WEB_BRAIN','authority_basis':'ORIGINAL_USER_APPROVED_EXECUTION_AND_CURRENT_TASK_TERMINAL_EVIDENCE',
         'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],
         'source_projection_digest':projection['projection_digest'],'source_user_approval_decision_ref':approval_record['decision_ref'],'source_transport_receipt_digest':receipt['receipt_digest'],
         'transport_repository_id':surface['repository_id'],'temporary_ref':surface['temporary_ref'],'expected_ref_commit':receipt['exact_commit_sha'],
         'terminal_basis':'TASK_TERMINAL_EVIDENCE','task_terminal_status':terminal_evidence['status'],'terminal_evidence_ref':terminal_evidence['evidence_ref'],'terminal_evidence_digest':terminal_evidence['evidence_digest'],
         'cleanup_action':'DELETE_EXACT_TEMPORARY_REF','background_service_used':False,'user_mediated_handoff_required':True,'continuation_digest':None}
    row['continuation_digest']=digest(strip_digest(row,'continuation_digest')); validate_schema(row,EVIDENCE_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA); return row

def validate_evidence_transport_cleanup_target(continuation: dict[str,Any], current_ref_commit: str) -> None:
    validate_schema(continuation,EVIDENCE_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA)
    if continuation['continuation_digest']!=digest(strip_digest(continuation,'continuation_digest')): raise JoyflowError('Evidence transport cleanup continuation digest mismatch')
    if current_ref_commit!=continuation['expected_ref_commit']:
        raise JoyflowError('temporary Evidence ref moved after transport; preauthorized cleanup may not delete a repurposed ref')

def build_current_review_transport_cleanup_continuation(
    projection: dict[str,Any], approval_record: dict[str,Any], locator: dict[str,Any], *, terminal_evidence: dict[str,Any],
) -> dict[str,Any]:
    validate_current_review_transport_plan(projection)
    plan=projection.get('delivery',{}).get('current_review_transport') or {}; cleanup=plan.get('cleanup') or {}
    if plan.get('mode')!='GITHUB_EXACT_OBJECT_IF_NEEDED' or plan.get('retention_policy')!='EPHEMERAL_BY_DEFAULT' or cleanup.get('preauthorized') is not True:
        raise JoyflowError('current review cleanup requires an exact preauthorized ephemeral transport plan')
    if not isinstance(approval_record,dict) or approval_record.get('status')!='APPROVED_FINAL' or approval_record.get('basis')!='CURRENT_EXPLICIT_USER_DECISION' or approval_record.get('binding')!=approval_binding(projection):
        raise JoyflowError('current review cleanup requires the original explicit user execution approval')
    validate_schema(locator,CURRENT_PR_REVIEW_INPUT_TRANSPORT_SCHEMA)
    if locator.get('locator_digest')!=digest(strip_digest(locator,'locator_digest')):
        raise JoyflowError('current review transport locator digest mismatch')
    surface=plan.get('github_surface') or {}
    if locator.get('repository_id')!=surface.get('repository_id') or locator.get('temporary_ref')!=surface.get('temporary_ref'):
        raise JoyflowError('current review cleanup locator escaped the approved transport surface')
    allowed=set(load_model().get('current_review_transport_policy',{}).get('cleanup_supported_terminal_statuses',[]))
    if not isinstance(terminal_evidence,dict) or terminal_evidence.get('status') not in allowed or not terminal_evidence.get('evidence_ref') or not re.fullmatch(r'[0-9a-f]{64}',terminal_evidence.get('evidence_digest') or ''):
        raise JoyflowError('current review cleanup terminal evidence is missing or invalid')
    row={'artifact_type':'CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION','owner':'WEB_BRAIN','authority_basis':'ORIGINAL_USER_APPROVED_EXECUTION_AND_CURRENT_TASK_TERMINAL_EVIDENCE',
         'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],
         'source_projection_digest':projection['projection_digest'],'source_user_approval_decision_ref':approval_record['decision_ref'],'source_locator_digest':locator['locator_digest'],
         'transport_repository_id':locator['repository_id'],'temporary_ref':locator['temporary_ref'],'expected_ref_commit':locator['exact_transport_commit'],
         'terminal_basis':'TASK_TERMINAL_EVIDENCE','task_terminal_status':terminal_evidence['status'],'terminal_evidence_ref':terminal_evidence['evidence_ref'],'terminal_evidence_digest':terminal_evidence['evidence_digest'],
         'cleanup_action':'DELETE_EXACT_TEMPORARY_REF','background_service_used':False,'user_mediated_handoff_required':True,'continuation_digest':None}
    row['continuation_digest']=digest(strip_digest(row,'continuation_digest'))
    validate_schema(row,CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA)
    return row

def validate_current_review_transport_cleanup_target(continuation: dict[str,Any], current_ref_commit: str) -> None:
    validate_schema(continuation,CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA)
    if continuation['continuation_digest']!=digest(strip_digest(continuation,'continuation_digest')):
        raise JoyflowError('current review transport cleanup continuation digest mismatch')
    if current_ref_commit!=continuation['expected_ref_commit']:
        raise JoyflowError('temporary current review ref moved after transport; cleanup must not delete it')

def validate_approval(capsule: dict[str, Any], projection: dict[str, Any]) -> None:
    if not _approval_record_shape(capsule,projection):
        if projection.get('execution_mode')=='READ_ONLY':
            raise JoyflowError('exact Web-Brain bounded read-only discovery authorization is missing or bound to another object')
        raise JoyflowError('Brain-recorded current explicit user execution approval is missing or bound to another object')

def validate_role_ownership(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    record = capsule.get('approval_record', {})
    if record.get('owner') != 'WEB_BRAIN':
        raise JoyflowError('only WEB_BRAIN may record approval lifecycle state')
    review = capsule.get('active_fibers', {}).get('execution_review', {}).get('payload')
    if not review:
        return
    if review.get('brain_review_verdict') not in {'PENDING_BRAIN_REVIEW', 'PASS', 'BLOCK'}:
        raise JoyflowError('invalid Brain review state')
    if review.get('user_acceptance') not in {'PENDING_USER_ACCEPTANCE', 'PASS', 'BLOCK', 'NOT_APPLICABLE'}:
        raise JoyflowError('invalid user acceptance state')
    if review.get('merge_status', 'NOT_AUTHORIZED') != 'NOT_AUTHORIZED':
        raise JoyflowError('Task Capsule and Codex return may not elevate merge authorization')

def validate_authority_fiber(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    profile=model['route_profiles'][capsule['route_profile']]
    fiber=capsule.get('active_fibers',{}).get('authority')
    if not profile['executable']:
        return
    if not fiber:
        raise JoyflowError('executable task requires authority fiber')
    payload=fiber['payload']
    if profile['execution_mode']=='READ_ONLY':
        if payload.get('approval_required') is not False or payload.get('brain_read_only_authorization_required') is not True:
            raise JoyflowError('bounded read-only discovery requires Web Brain authorization and must not require separate user approval')
    elif payload.get('approval_required') is not True:
        raise JoyflowError('mutation/material execution requires explicit user approval')
    if not payload.get('return_contract'):
        raise JoyflowError('authority fiber requires a return contract')

def validate_route_profile(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    profile_name = capsule.get('route_profile')
    if profile_name not in model['route_profiles']:
        raise JoyflowError(f'unknown route profile: {profile_name}')
    profile = model['route_profiles'][profile_name]
    if capsule['task_anchor']['change_scope'] not in profile['allowed_change_scopes']:
        raise JoyflowError('route profile does not allow task change_scope')
    if capsule['task_progress']['stage'] not in profile['allowed_stages']:
        raise JoyflowError('stage is not legal for route profile')

def validate_sealed_progress(model: dict[str, Any], capsule: dict[str, Any]) -> None:
    """Validate a sealed capsule without requiring the parent payload.

    Exact parent/child comparison belongs to validate_transition() and is run only
    while sealing a new revision. A previously sealed capsule must remain usable as
    a self-contained handoff source.
    """
    progress = capsule['task_progress']
    profile = model['route_profiles'][capsule['route_profile']]
    trigger = progress.get('cycle_trigger', 'NONE')
    event = progress.get('transition_event')
    if progress['cycle'] < 1:
        raise JoyflowError('cycle must start at 1')
    if trigger != 'NONE' and trigger not in model['cycle_triggers']:
        raise JoyflowError('unknown cycle trigger')
    parent = progress.get('parent_capsule_digest')
    previous_stage = progress.get('previous_stage')
    if parent is None:
        if progress['cycle'] != 1 or previous_stage is not None:
            raise JoyflowError('initial sealed capsule lineage is invalid')
        if progress['stage'] != profile['initial_stage']:
            raise JoyflowError(f"initial stage must be {profile['initial_stage']} for route {capsule['route_profile']}")
        if not event or event.get('event_type') != 'CREATE_TASK' or event.get('from_stage') is not None or (event.get('to_stage') != progress['stage']):
            raise JoyflowError('initial sealed capsule requires exact CREATE_TASK event')
    else:
        if previous_stage is None:
            raise JoyflowError('non-initial capsule requires previous_stage')
        if not event or event.get('event_type') == 'CREATE_TASK':
            raise JoyflowError('non-initial capsule requires non-CREATE_TASK transition event')
        if event.get('event_type') not in model['transition_event_types']:
            raise JoyflowError('unknown transition event type')
        if event.get('from_stage') != previous_stage or event.get('to_stage') != progress['stage']:
            raise JoyflowError('sealed transition event stage binding mismatch')
        if trigger != 'NONE' and event.get('event_type') != model['cycle_trigger_event_map'][trigger]:
            raise JoyflowError('cycle trigger and sealed transition event mismatch')
    if not event.get('reason'):
        raise JoyflowError('transition event requires reason')
    require_refs(event.get('evidence_refs', []), evidence_map(capsule), 'transition event')

def validate_transition(model: dict[str, Any], capsule: dict[str, Any], previous: dict[str, Any] | None) -> None:
    """Validate the exact transition while a new capsule revision is sealed."""
    validate_progress(model, capsule, previous)
    validate_lineage(model, capsule, previous)
    if previous is not None:
        current_review=capsule.get('active_fibers',{}).get('execution_review',{}).get('payload')
        previous_review=previous.get('active_fibers',{}).get('execution_review',{}).get('payload')
        if current_review and previous_review:
            immutable=('project_id','task_id','round_id','source_execution_status','source_projection_digest','source_codex_return_digest','source_evidence_bundle_digest','source_codex_return_evidence_ref','source_evidence_bundle_ref','review_target','source_evidence_row_digests','source_snapshot_digest')
            if any(current_review.get(k)!=previous_review.get(k) for k in immutable):
                raise JoyflowError('Brain review revision cannot rewrite its exact Codex source object or review target')

def validate_capsule(capsule: dict[str, Any], *, previous: dict[str, Any] | None=None, require_projection_ready: bool=False, require_approval: bool=False) -> None:
    validate_schema(capsule, CAPSULE_SCHEMA)
    validate_pr_goal_scenario_grounding(load_model(), capsule)
    validate_current_source_task_grounding(load_model(), capsule)
    model = load_model()
    validate_registry_implementation(model)
    if capsule['model_id'] != model['model_id'] or capsule['model_version'] != model['model_version']:
        raise JoyflowError('capsule model identity mismatch')
    validate_route_profile(model, capsule)
    validate_single_active_round_binding(model, capsule)
    validate_task_object_anchor(capsule)
    validate_sealed_progress(model, capsule)
    validate_active_fibers(model, capsule)
    validate_digest_chain(model, capsule)
    validate_materiality(model, capsule)
    validate_semantic_classification_review(capsule)
    validate_exclusions(model, capsule)
    validate_risk_route(model, capsule)
    validate_effect_transport(model, capsule)
    validate_technical_route_space(capsule)
    validate_path_discovery_state(model, capsule)
    validate_repository_readiness(model, capsule, require_complete=require_projection_ready)
    validate_mechanical_walkthrough(model, capsule)
    validate_validation_closure(model, capsule)
    validate_repair_extension(model, capsule)
    validate_authority_fiber(model, capsule)
    validate_role_ownership(model, capsule)
    validate_review_input_binding(capsule)
    validate_repository_acceptance_freeze_binding(capsule)
    if capsule['capsule_digest'] != digest(capsule_payload(capsule)):
        raise JoyflowError('capsule digest mismatch')
    validate_derived_gates(model, capsule)
    validate_stage_gate_requirements(model, capsule)
    if previous is not None:
        validate_transition(model, capsule, previous)
    if require_projection_ready:
        profile = model['route_profiles'][capsule['route_profile']]
        if not profile['executable']:
            raise JoyflowError('non-executable route cannot create Codex handoff')
        ready_stages=model['approval_requirements']['read_only_projection_ready_stages'] if capsule['route_profile']=='READ_ONLY_DISCOVERY' else model['projection_ready_stages']
        if capsule['task_progress']['stage'] not in ready_stages:
            raise JoyflowError('task stage is not projection-ready')
        for name in profile['required_fibers']:
            if capsule['active_fibers'][name]['status'] not in {'VALIDATED', 'FROZEN'}:
                raise JoyflowError(f'required fiber is not validated: {name}')
        if capsule.get('unresolved_blockers'):
            raise JoyflowError('unresolved blockers prevent projection')
        if require_approval and capsule['derived_gates']['projection_gate'] != 'PASS':
            raise JoyflowError('derived projection gate is not PASS')
        if not require_approval:
            for gate in ('semantic_gate', 'repository_evidence_gate', 'boundary_gate', 'validation_gate'):
                if capsule['derived_gates'][gate] != 'PASS':
                    raise JoyflowError(f'draft projection blocked by {gate}')
            pg=capsule['derived_gates']['path_readiness_gate']
            if capsule['route_profile']=='READ_ONLY_DISCOVERY':
                if pg!='NEEDS_LOCAL_DISCOVERY': raise JoyflowError('read-only discovery projection requires pending local discovery')
            elif pg not in {'PASS','NOT_REQUIRED'}:
                raise JoyflowError('draft projection blocked by path_readiness_gate')

def capsule_payload(capsule: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(capsule)
    value.pop('capsule_digest', None)
    value.pop('approval_record', None)
    value.pop('derived_gates', None)
    return value

def validate_review_seal_input_structure(capsule: dict[str, Any], previous: dict[str, Any] | None, projection: dict[str, Any] | None, codex_return: dict[str, Any] | None, evidence_bundle: dict[str, Any] | None) -> None:
    current=capsule.get('active_fibers',{}).get('execution_review',{}).get('payload')
    prior=(previous or {}).get('active_fibers',{}).get('execution_review',{}).get('payload')
    supplied=[projection is not None,codex_return is not None,evidence_bundle is not None]
    if any(supplied) and not all(supplied):
        raise JoyflowError('review sealing requires exact Projection, Codex Return and Evidence Bundle together')
    if current is None:
        return
    source_fields=('source_projection_digest','source_codex_return_digest','source_evidence_bundle_digest','source_task_object_lifecycle_digest','source_execution_lifecycle_result_digest','source_execution_status','review_target','source_evidence_row_digests','source_snapshot_digest')
    new_or_changed=prior is None or any(current.get(k)!=prior.get(k) for k in source_fields)
    if new_or_changed and not all(supplied):
        raise JoyflowError('new or changed Brain review source must be sealed with exact Projection, Codex Return and Evidence Bundle')
    if all(supplied):
        validate_review_input_binding_structure(capsule,projection,codex_return,evidence_bundle)


def validate_local_discovery_seal_input_structure(capsule: dict[str, Any], previous: dict[str, Any] | None, projection: dict[str, Any] | None, path_return: dict[str, Any] | None) -> None:
    state=capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{})
    completed=state.get('local_discovery_status')=='COMPLETED'
    previous_state=(previous or {}).get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{})
    binding=state.get('local_discovery_binding')
    newly_bound=completed and (previous_state.get('local_discovery_binding')!=binding or previous_state.get('local_discovery_status')!='COMPLETED')
    decision_changed=completed and previous_state.get('final_path_decision')!=state.get('final_path_decision')
    supplied=[projection is not None,path_return is not None]
    if any(supplied) and not all(supplied):
        raise JoyflowError('local discovery sealing requires the exact Projection and Path Discovery Return together')
    if (newly_bound or decision_changed) and not all(supplied):
        raise JoyflowError('new or changed local path decision must be sealed with the exact Projection and Path Discovery Return')
    if all(supplied):
        validate_path_discovery_return_structure(path_return,projection)
        if path_return['unresolved_questions']:
            raise JoyflowError('unresolved local discovery questions prevent final path confirmation')
        structural=path_return['structural_discovery']
        frame=state.get('structural_decision_frame'); disposition=state.get('brain_architecture_disposition')
        if frame is not None:
            if structural['task_structural_projection']['status']!='CLOSED' or structural['unresolved_structural_questions']:
                raise JoyflowError('unresolved structural discovery prevents final path confirmation')
            if not disposition or disposition.get('disposition')!='ACCEPT' or disposition.get('source_structural_return_digest')!=path_return['return_digest'] or disposition.get('source_route_id')!=structural['recommended_route_id']:
                raise JoyflowError('final structural path confirmation requires exact Brain acceptance of the supplied Codex route')
        expected={'project_id':capsule['task_anchor']['project_id'],'task_id':capsule['task_anchor']['task_id'],'round_id':capsule['task_progress']['cycle']}
        if any(projection.get(k)!=v for k,v in expected.items()):
            raise JoyflowError('local discovery source Projection belongs to another task round')
        if not binding or binding.get('source_projection_digest')!=projection['projection_digest'] or binding.get('path_discovery_return_digest')!=path_return['return_digest']:
            raise JoyflowError('local discovery state is not bound to the exact supplied Return')
        validate_final_path_decision(state['final_path_decision'],capsule,expected_path_return_digest=path_return['return_digest'],path_return=path_return)

def validate_review_seal_input(capsule: dict[str,Any], previous: dict[str,Any] | None, projection: dict[str,Any] | None, codex_return: dict[str,Any] | None, evidence_bundle: dict[str,Any] | None, *, source_repository: str | pathlib.Path | None=None, source_artifact: str | pathlib.Path | None=None, artifact_outputs: list[str | pathlib.Path] | None=None, artifact_output_root: str | pathlib.Path | None=None, replay_tests: bool=True, path_discovery_return: dict[str,Any] | None=None, path_discovery_projection: dict[str,Any] | None=None, source_materials: dict[str,str | pathlib.Path] | None=None) -> None:
    validate_review_seal_input_structure(capsule,previous,projection,codex_return,evidence_bundle)
    if projection is not None and codex_return is not None and evidence_bundle is not None:
        validate_review_input_binding(capsule,projection,codex_return,evidence_bundle,source_repository=source_repository,source_artifact=source_artifact,artifact_outputs=artifact_outputs,artifact_output_root=artifact_output_root,replay_tests=replay_tests,path_discovery_return=path_discovery_return,path_discovery_projection=path_discovery_projection,source_materials=source_materials)

def validate_local_discovery_seal_input(capsule: dict[str,Any], previous: dict[str,Any] | None, projection: dict[str,Any] | None, path_return: dict[str,Any] | None, *, source_repository: str | pathlib.Path | None=None) -> None:
    validate_local_discovery_seal_input_structure(capsule,previous,projection,path_return)
    if projection is not None and path_return is not None:
        if source_repository is None:
            raise JoyflowError('local discovery sealing requires current repository source replay')
        validate_path_discovery_return(path_return,projection,repository=source_repository)

def prepare_capsule(unsealed: dict[str, Any], previous: dict[str, Any] | None=None, *, review_projection: dict[str, Any] | None=None, codex_return: dict[str, Any] | None=None, evidence_bundle: dict[str, Any] | None=None, path_discovery_projection: dict[str, Any] | None=None, path_discovery_return: dict[str, Any] | None=None, merge_candidate_freeze: dict[str, Any] | None=None, source_repository: str | pathlib.Path | None=None, source_artifact: str | pathlib.Path | None=None, artifact_outputs: list[str | pathlib.Path] | None=None, artifact_output_root: str | pathlib.Path | None=None, replay_tests: bool=True, source_materials: dict[str,str | pathlib.Path] | None=None) -> dict[str, Any]:
    capsule = copy.deepcopy(unsealed)
    model = load_model()
    capsule['model_id'] = model['model_id']
    capsule['model_version'] = model['model_version']
    capsule.pop('gates', None)
    capsule.setdefault('approval_record', ({'status':'NEEDS_BRAIN_READ_ONLY_AUTHORIZATION','owner':'WEB_BRAIN','scope':'READ_ONLY_DISCOVERY_ONLY','basis':'NOT_YET_AUTHORIZED','decision_ref':None,'binding':None} if load_model()['route_profiles'][capsule['route_profile']]['execution_mode']=='READ_ONLY' else {'status':'NEEDS_USER_APPROVAL','owner':'WEB_BRAIN','scope':expected_approval_scope(capsule),'basis':'NOT_YET_APPROVED','decision_ref':None,'binding':None}))
    capsule['task_anchor']['anchor_digest'] = digest(strip_digest(capsule['task_anchor'], 'anchor_digest'))
    for row in capsule.get('evidence_registry', []):
        row['claim_digest'] = digest(row['claim'])
    for item in semantic_items(capsule):
        item['meaning_digest'] = digest(item['meaning'])
        for effect in item.get('effects', []):
            effect['effect_digest'] = digest(strip_digest(effect, 'effect_digest'))
    for name, fiber in capsule['active_fibers'].items():
        fiber['fiber_type'] = name
        fiber['fiber_digest'] = digest(strip_digest(fiber, 'fiber_digest'))
    capsule['capsule_digest'] = digest(capsule_payload(capsule))
    capsule['derived_gates'] = compute_gate_snapshot(capsule)
    validate_transition(model, capsule, previous)
    validate_review_seal_input(capsule, previous, review_projection, codex_return, evidence_bundle, source_repository=source_repository, source_artifact=source_artifact, artifact_outputs=artifact_outputs, artifact_output_root=artifact_output_root, replay_tests=replay_tests, path_discovery_return=path_discovery_return, path_discovery_projection=path_discovery_projection, source_materials=source_materials)
    validate_local_discovery_seal_input(capsule, previous, path_discovery_projection, path_discovery_return, source_repository=source_repository)
    validate_merge_candidate_freeze_seal_input(capsule, previous, merge_candidate_freeze)
    validate_capsule(capsule)
    return capsule

_BRAIN_MANIFEST_FORBIDDEN_FIELDS = {
    'capsule_digest', 'fiber_digest', 'approval_digest', 'approval_record',
    'codex_return', 'user_merge_authorization', 'merge_authorization',
}

def _validate_brain_manifest_boundary(value: Any, path: str='<root>') -> None:
    if isinstance(value,dict):
        for key,item in value.items():
            current=f'{path}.{key}'
            if key in _BRAIN_MANIFEST_FORBIDDEN_FIELDS:
                raise JoyflowError(f'Brain semantic manifest contains forbidden mechanical/authority field: {current}')
            _validate_brain_manifest_boundary(item,current)
    elif isinstance(value,list):
        for index,item in enumerate(value):
            _validate_brain_manifest_boundary(item,f'{path}[{index}]')

def _manifest_fibers(manifest: dict[str,Any]) -> dict[str,Any]:
    result={}
    for name,spec in manifest['active_fibers'].items():
        payload=copy.deepcopy(spec['payload']); status=spec['status']
        result[name]={'fiber_type':name,'status':status,'revision':1,'previous_digest':None,'payload':payload,'fiber_digest':None}
    return result

def _normalize_brain_manifest_derivations(capsule: dict[str,Any]) -> None:
    for item in semantic_items(capsule):
        item['meaning_digest']=digest(item['meaning'])
        for effect in item.get('effects',[]):
            effect['effect_digest']=digest(strip_digest(effect,'effect_digest'))
    decision=capsule.get('active_fibers',{}).get('decision_boundary',{}).get('payload')
    if decision is not None:
        decision['boundary_obligations']=expected_boundary_obligations(capsule)
    validation=capsule.get('active_fibers',{}).get('validation',{}).get('payload')
    if validation is not None:
        validation['acceptance_cases']=expected_validation_cases(capsule)
        validation['obligation_registry']=expected_validation_obligations(capsule)
        validation['mechanical_walkthrough']=expected_mechanical_walkthrough(capsule)
    final=(capsule.get('active_fibers',{}).get('repository_evidence',{}).get('payload',{}).get('path_discovery',{}).get('final_path_decision'))
    if isinstance(final,dict) and final.get('decision_digest') is None:
        final['decision_digest']=digest(strip_digest(final,'decision_digest'))
    space=(decision or {}).get('technical_route_space')
    if isinstance(space,dict):
        for obligation in space.get('obligations',[]):
            dimension=obligation.get('dimension')
            if dimension:
                obligation['subject_binding']=expected_preflight_subject_binding(capsule,dimension)

def _bind_manifest_fiber_lineage(capsule: dict[str,Any], previous: dict[str,Any] | None) -> None:
    old_fibers=(previous or {}).get('active_fibers',{})
    for name,fiber in capsule['active_fibers'].items():
        old=old_fibers.get(name)
        if old is None:
            fiber['revision']=1; fiber['previous_digest']=None
        elif old['payload']==fiber['payload'] and old['status']==fiber['status']:
            fiber['revision']=old['revision']; fiber['previous_digest']=old.get('previous_digest')
        else:
            fiber['revision']=old['revision']+1; fiber['previous_digest']=old['fiber_digest']

def build_capsule_from_brain_manifest(manifest: dict[str,Any], previous: dict[str,Any] | None=None) -> dict[str,Any]:
    """Mechanically assemble and seal a Capsule from explicit Web-Brain semantics.

    The manifest is temporary construction input, not a Capsule, approval record,
    evidence object, or durable truth source. All semantic payloads remain exact;
    only schema wrappers, lineage bindings, model identity, and digests are added.
    """
    validate_schema(manifest,BRAIN_CAPSULE_MANIFEST_SCHEMA)
    _validate_brain_manifest_boundary(manifest)
    model=load_model(); profile=model['route_profiles'].get(manifest['route_profile'])
    if not profile or profile.get('execution_mode')!='MUTATING':
        raise JoyflowError('NEEDS_USER_APPROVAL Brain manifest requires an existing mutating route profile')
    if manifest.get('approval_state')!='NEEDS_USER_APPROVAL':
        raise JoyflowError('Brain manifest may compile only a pre-user-approval Capsule')
    progress=copy.deepcopy(manifest['task_progress']); event=progress['transition_event']
    previous_stage=(previous or {}).get('task_progress',{}).get('stage')
    progress['previous_stage']=previous_stage
    progress['parent_capsule_digest']=(previous or {}).get('capsule_digest')
    event['from_stage']=previous_stage
    event['to_stage']=progress['stage']
    evidence=copy.deepcopy(manifest['evidence_registry'])
    for row in evidence:
        row['claim_digest']=None
    anchor=copy.deepcopy(manifest['task_anchor']); anchor['anchor_digest']=None
    capsule={
      'artifact_type':'FIBERED_TASK_CAPSULE','model_id':model['model_id'],'model_version':model['model_version'],
      'capsule_id':manifest['capsule_id'],'task_anchor':anchor,'task_progress':progress,
      'route_profile':manifest['route_profile'],'task_classification':copy.deepcopy(manifest['task_classification']),
      'active_fibers':_manifest_fibers(manifest),'evidence_registry':evidence,
      'refs':copy.deepcopy(manifest['refs']),'derived_gates':{},
      'unresolved_blockers':copy.deepcopy(manifest['unresolved_blockers']),
      'approval_record':{'status':'NEEDS_USER_APPROVAL','owner':'WEB_BRAIN','scope':'EXECUTION_ONLY','basis':'NOT_YET_APPROVED','decision_ref':None,'binding':None},
      'stop_conditions':copy.deepcopy(manifest['stop_conditions']),'capsule_digest':None,
    }
    _normalize_brain_manifest_derivations(capsule)
    _bind_manifest_fiber_lineage(capsule,previous)
    return prepare_capsule(capsule,previous)

def prepare_repository_review_capsule(unsealed: dict[str,Any], previous: dict[str,Any] | None, *, review_projection: dict[str,Any], codex_return: dict[str,Any], evidence_bundle: dict[str,Any], source_repository: str | pathlib.Path, path_discovery_return: dict[str,Any] | None=None, path_discovery_projection: dict[str,Any] | None=None) -> dict[str,Any]:
    if review_projection.get('task_object_lifecycle',{}).get('route_type') not in {'REPOSITORY_CHANGE','EXISTING_PR_REPLAY'}:
        raise JoyflowError('repository review entry requires a repository lifecycle Projection')
    if _repository_review_evidence(codex_return) is None or codex_return.get('artifact_evidence') is not None:
        raise JoyflowError('repository review entry requires exactly one repository evidence variant')
    return prepare_capsule(unsealed,previous,review_projection=review_projection,codex_return=codex_return,evidence_bundle=evidence_bundle,path_discovery_return=path_discovery_return,path_discovery_projection=path_discovery_projection,source_repository=source_repository,replay_tests=True)

def prepare_artifact_review_capsule(unsealed: dict[str,Any], previous: dict[str,Any] | None, *, review_projection: dict[str,Any], codex_return: dict[str,Any], evidence_bundle: dict[str,Any], source_artifact: str | pathlib.Path | None=None, source_materials: dict[str,str | pathlib.Path] | None=None, artifact_outputs: list[str | pathlib.Path], artifact_output_root: str | pathlib.Path) -> dict[str,Any]:
    route=review_projection.get('task_object_lifecycle',{}).get('route_type')
    if route not in {'ARTIFACT_REPAIR','NEW_ARTIFACT'}:
        raise JoyflowError('Artifact review entry requires an Artifact lifecycle Projection')
    if codex_return.get('artifact_evidence') is None or codex_return.get('pr_evidence') is not None:
        raise JoyflowError('Artifact review entry requires Artifact evidence only')
    if not artifact_outputs:
        raise JoyflowError('Artifact review entry requires the exact complete output Artifact set')
    if route=='ARTIFACT_REPAIR' and (source_artifact is None or source_materials):
        raise JoyflowError('Artifact repair review requires exactly one source Artifact')
    if route=='NEW_ARTIFACT' and (source_artifact is not None or not source_materials):
        raise JoyflowError('new Artifact review requires the exact source-material set')
    return prepare_capsule(unsealed,previous,review_projection=review_projection,codex_return=codex_return,evidence_bundle=evidence_bundle,source_artifact=source_artifact,source_materials=source_materials,artifact_outputs=artifact_outputs,artifact_output_root=artifact_output_root,replay_tests=True)

def prepare_capsule_structural_fixture(unsealed: dict[str,Any], previous: dict[str,Any] | None=None, **kwargs: Any) -> dict[str,Any]:
    """TEST/EXAMPLE ONLY: build structurally valid static fixtures without source replay.

    Operational sealing must use prepare_capsule with current repository/artifact context.
    """
    capsule=copy.deepcopy(unsealed)
    model=load_model()
    capsule['model_id']=model['model_id']; capsule['model_version']=model['model_version']; capsule.pop('gates',None)
    capsule.setdefault('approval_record', ({'status':'NEEDS_BRAIN_READ_ONLY_AUTHORIZATION','owner':'WEB_BRAIN','scope':'READ_ONLY_DISCOVERY_ONLY','basis':'NOT_YET_AUTHORIZED','decision_ref':None,'binding':None} if load_model()['route_profiles'][capsule['route_profile']]['execution_mode']=='READ_ONLY' else {'status':'NEEDS_USER_APPROVAL','owner':'WEB_BRAIN','scope':expected_approval_scope(capsule),'basis':'NOT_YET_APPROVED','decision_ref':None,'binding':None}))
    capsule['task_anchor']['anchor_digest']=digest(strip_digest(capsule['task_anchor'],'anchor_digest'))
    for row in capsule.get('evidence_registry',[]): row['claim_digest']=digest(row['claim'])
    for item in semantic_items(capsule):
        item['meaning_digest']=digest(item['meaning'])
        for effect in item.get('effects',[]): effect['effect_digest']=digest(strip_digest(effect,'effect_digest'))
    for name,fiber in capsule['active_fibers'].items(): fiber['fiber_type']=name; fiber['fiber_digest']=digest(strip_digest(fiber,'fiber_digest'))
    capsule['capsule_digest']=digest(capsule_payload(capsule)); capsule['derived_gates']=compute_gate_snapshot(capsule)
    validate_transition(model,capsule,previous)
    validate_review_seal_input_structure(capsule,previous,kwargs.get("review_projection"),kwargs.get("codex_return"),kwargs.get("evidence_bundle"))
    validate_local_discovery_seal_input_structure(capsule,previous,kwargs.get("path_discovery_projection"),kwargs.get("path_discovery_return"))
    validate_capsule(capsule)
    return capsule

def traceability_map(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    obligations = {r['effect_id']: r['obligation_id'] for r in expected_boundary_obligations(capsule)}
    cases = {r['effect_id']: r['case_id'] for r in expected_validation_cases(capsule)}
    controls = capsule.get('active_fibers', {}).get('decision_boundary', {}).get('payload', {}).get('risk_controls', [])
    control_by_marker: dict[str, list[str]] = {}
    for row in controls:
        control_by_marker.setdefault(row['marker'], []).append(row['control_id'])
    rows = []
    for item in semantic_items(capsule):
        if not active_material(item):
            continue
        effects = item.get('effects', [])
        rows.append({'item_id': item['item_id'], 'meaning_digest': item['meaning_digest'], 'effect_ids': [e['effect_id'] for e in effects], 'boundary_obligation_ids': [obligations[e['effect_id']] for e in effects if e['effect_id'] in obligations], 'validation_case_ids': [cases[e['effect_id']] for e in effects if e['effect_id'] in cases], 'risk_control_ids': sorted({cid for marker in item['risk_markers'] for cid in control_by_marker.get(marker, [])}), 'prompt_included': True})
    return sorted(rows, key=lambda r: r['item_id'])

def projection_payload(projection: dict[str, Any]) -> dict[str, Any]:
    return strip_digest(projection, 'projection_digest')

def build_projection(capsule: dict[str, Any], *, require_approval: bool=False) -> dict[str, Any]:
    validate_capsule(capsule, require_projection_ready=True, require_approval=require_approval)
    model = load_model(); profile = model['route_profiles'][capsule['route_profile']]; fibers = capsule['active_fibers']
    decision = fibers['decision_boundary']['payload']; validation = fibers['validation']['payload']; repository_evidence = fibers.get('repository_evidence', {}).get('payload', {})
    material=[]
    for item in semantic_items(capsule):
        if active_material(item):
            material.append({k:copy.deepcopy(item[k]) for k in ('item_id','item_type','meaning','meaning_digest','status','material_class','risk_markers','domain_lanes','effects','provenance_refs')})
    projection={'artifact_type':'CODEX_HANDOFF_PROJECTION','projection_version':8,'build_identity':build_identity(),'project_id':capsule['task_anchor']['project_id'],'task_id':capsule['task_anchor']['task_id'],'round_id':capsule['task_progress']['cycle'],'capsule_id':capsule['capsule_id'],'capsule_digest':capsule['capsule_digest'],'task_anchor':copy.deepcopy(capsule['task_anchor']),'task_progress':copy.deepcopy(capsule['task_progress']),'route_profile':capsule['route_profile'],'execution_mode':profile['execution_mode'],'flow_depth':profile['flow_depth'],'validation_depth':profile['validation_depth'],'task_classification':copy.deepcopy(capsule['task_classification']),'material_semantics':material,'repository_evidence':copy.deepcopy(repository_evidence),'current_source_context':_build_current_source_context(capsule),'decision_boundary':copy.deepcopy(decision),'validation':copy.deepcopy(validation),'traceability':traceability_map(capsule),'derived_gates':{'semantic_gate':capsule['derived_gates']['semantic_gate'],'repository_evidence_gate':capsule['derived_gates']['repository_evidence_gate'],'path_readiness_gate':capsule['derived_gates']['path_readiness_gate'],'boundary_gate':capsule['derived_gates']['boundary_gate'],'validation_gate':capsule['derived_gates']['validation_gate'],'derived_from_capsule_digest':capsule['capsule_digest']},'codex_technical_authority':copy.deepcopy(model['codex_technical_authority']),'technical_route_space':copy.deepcopy(decision['technical_route_space']),'execution_object':_execution_object_from_capsule(capsule),'task_object_lifecycle':task_object_lifecycle_from_capsule(capsule),'delivery':{'execution_mode':profile['execution_mode'],'mutation_allowed':profile['execution_mode']=='MUTATING','return_artifact_type':'PATH_DISCOVERY_RETURN' if capsule['route_profile']=='READ_ONLY_DISCOVERY' else 'CODEX_EXECUTION_RETURN','requires_pr':bool(profile['requires_pr'] is True or (profile['requires_pr']=='conditional' and capsule['task_anchor']['change_scope']=='REPOSITORY_CHANGE')),'candidate_is_not_canonical':True,'merge_requires_separate_user_decision':True,'automatic_promotion_forbidden':True,'return_contract':copy.deepcopy(fibers['authority']['payload']['return_contract']),'evidence_transport':copy.deepcopy(fibers['authority']['payload'].get('evidence_transport',_default_evidence_transport_plan()))},'stop_conditions':copy.deepcopy(capsule['stop_conditions']),'projection_digest':None}
    current_review_plan=fibers['authority']['payload'].get('current_review_transport')
    if current_review_plan is not None:
        projection['delivery']['current_review_transport']=copy.deepcopy(current_review_plan)
    projection['projection_digest']=digest(projection_payload(projection)); validate_schema(projection,PROJECTION_SCHEMA); validate_evidence_transport_plan(projection); validate_current_review_transport_plan(projection); validate_task_object_lifecycle(projection); return projection

def execution_view(projection: dict[str, Any]) -> dict[str, Any]:
    # Full exact execution semantics remain available to the Runtime from the sealed
    # projection. This full view is not duplicated into the model-visible prompt.
    return {'identity':{'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_id':projection['capsule_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest'],'route_profile':projection['route_profile'],'execution_mode':projection['execution_mode'],'flow_depth':projection['flow_depth'],'validation_depth':projection['validation_depth'],'build_identity_digest':projection['build_identity']['build_identity_digest'],'source_set_digest':projection['build_identity']['source_set']['source_set_digest']},'objective':{'goal':projection['task_anchor']['goal'],'desired_result':projection['task_anchor']['desired_result'],'non_goals':projection['task_anchor']['non_goals']},'classification':copy.deepcopy(projection['task_classification']),'material_semantics':copy.deepcopy(projection['material_semantics']),'repository_evidence':copy.deepcopy(projection['repository_evidence']),'current_source_context':copy.deepcopy(projection['current_source_context']),'decision_boundary':copy.deepcopy(projection['decision_boundary']),'validation':copy.deepcopy(projection['validation']),'traceability':copy.deepcopy(projection['traceability']),'codex_technical_authority':copy.deepcopy(projection['codex_technical_authority']),'technical_route_space':copy.deepcopy(projection['technical_route_space']),'execution_object':copy.deepcopy(projection['execution_object']),'task_object_lifecycle':copy.deepcopy(projection['task_object_lifecycle']),'delivery':copy.deepcopy(projection['delivery']),'stop_conditions':copy.deepcopy(projection['stop_conditions'])}

def compact_execution_view(projection: dict[str, Any]) -> dict[str, Any]:
    planning=projection['task_anchor'].get('planning_context',{})
    decision=projection['decision_boundary']
    validation=projection['validation']
    return {
      'identity':{
        'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],
        'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest'],
        'route_profile':projection['route_profile'],'execution_mode':projection['execution_mode'],
        'build_identity_digest':projection['build_identity']['build_identity_digest']},
      'objective':{
        'parent_goal':planning.get('parent_goal'),'goal':projection['task_anchor']['goal'],
        'desired_result':projection['task_anchor']['desired_result'],'non_goals':projection['task_anchor']['non_goals'],
        'material_operating_assumptions':copy.deepcopy(planning.get('material_operating_assumptions',[])),
        'relevant_prior_behaviors':copy.deepcopy(planning.get('relevant_prior_behaviors',[])),
        'exit_conditions':copy.deepcopy(planning.get('exit_conditions',[]))},
      'material_semantics':copy.deepcopy(projection['material_semantics']),
      'current_source_context':copy.deepcopy(projection['current_source_context']),
      'execution_boundary':{
        'boundary_obligations':copy.deepcopy(decision.get('boundary_obligations',[])),
        'repository_binding':copy.deepcopy(decision.get('repository_binding')),
        'risk_controls':copy.deepcopy(decision.get('risk_controls',[])),
        'technical_decisions':copy.deepcopy(decision.get('technical_decisions',[])),
        'repair_extension':copy.deepcopy(decision.get('repair_extension'))},
      'technical_route_space':copy.deepcopy(projection['technical_route_space']),
      'validation':{
        'obligation_registry':copy.deepcopy(validation.get('obligation_registry',[])),
        'checks':copy.deepcopy(validation.get('checks',[])),
        'human_validation':copy.deepcopy(validation.get('human_validation',[])),
        'adversarial_review':copy.deepcopy(validation.get('adversarial_review',[]))},
      'execution_object':copy.deepcopy(projection['execution_object']),
      'delivery':{
        'mutation_allowed':projection['delivery']['mutation_allowed'],
        'requires_pr':projection['delivery']['requires_pr'],
        'return_artifact_type':projection['delivery']['return_artifact_type'],
        'return_contract':copy.deepcopy(projection['delivery']['return_contract']),'evidence_transport':copy.deepcopy(projection['delivery']['evidence_transport']),
        **({'current_review_transport':copy.deepcopy(projection['delivery']['current_review_transport'])} if 'current_review_transport' in projection['delivery'] else {})},
      'stop_conditions':copy.deepcopy(projection['stop_conditions'])}

def execution_authorization_envelope(projection: dict[str, Any]) -> dict[str, Any]:
    planning=projection['task_anchor'].get('planning_context',{})
    tolerances=[copy.deepcopy(r) for r in planning.get('material_operating_assumptions',[]) if r.get('condition_type')=='PRODUCT_TOLERANCE']
    semantics=[]
    for item in projection.get('material_semantics',[]):
        if item.get('status')=='USER_CONFIRMED' or item.get('material_class')=='GLOBAL_INVARIANT':
            semantics.append(copy.deepcopy(item))
    decision=projection.get('decision_boundary',{})
    minimum_validation=[]
    validation=projection.get('validation',{})
    case_map={row.get('case_id'): row for row in validation.get('acceptance_cases',[]) if row.get('case_id')}
    for row in validation.get('obligation_registry',[]):
        case=case_map.get(row.get('case_id'),{})
        minimum_validation.append({
          'obligation_id':row.get('obligation_id'),
          'assertion':case.get('assertion'),
          'assertion_digest':row.get('assertion_digest'),
          'required':row.get('required',True),
          'mode':row.get('mode'),
          'check_ids':copy.deepcopy(row.get('check_ids',[])),
          'human_validation_ids':copy.deepcopy(row.get('human_validation_ids',[])),
        })
    envelope={
      'artifact_type':'JOYFLOW_EXECUTION_AUTHORIZATION_ENVELOPE',
      'version':1,
      'project_id':projection['project_id'],'task_id':projection['task_id'],
      'task_version':projection['task_anchor'].get('task_version'),
      'execution_mode':projection['execution_mode'],
      'goal':projection['task_anchor']['goal'],'desired_result':projection['task_anchor']['desired_result'],
      'non_goals':copy.deepcopy(projection['task_anchor']['non_goals']),
      'active_product_semantics':semantics,
      'user_confirmed_product_tolerances':tolerances,
      'change_scope':projection['task_anchor'].get('change_scope'),
      'execution_object':copy.deepcopy(projection.get('execution_object')),
      'boundary_obligations':copy.deepcopy(decision.get('boundary_obligations',[])),
      'repository_binding':copy.deepcopy(decision.get('repository_binding')),
      'minimum_validation_obligations':minimum_validation,
      'stop_conditions':copy.deepcopy(projection.get('stop_conditions',[])),
    }
    if projection.get('delivery',{}).get('current_review_transport') is not None:
        envelope['current_review_transport']=copy.deepcopy(projection['delivery']['current_review_transport'])
    if projection['execution_mode']=='READ_ONLY':
        envelope['read_only_discovery_context']={
          'current_source_context':copy.deepcopy(projection.get('current_source_context')),
          'repository_evidence':copy.deepcopy(projection.get('repository_evidence')),
        }
    return envelope

def render_approval_view(projection: dict[str, Any]) -> str:
    read_only=projection['execution_mode']=='READ_ONLY'
    zero_product_mutation_material_execution=(
      projection['execution_mode']=='MUTATING'
      and projection.get('task_anchor',{}).get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY'
      and projection.get('current_source_context',{}).get('current_product_mutation_paths')==[]
      and projection.get('task_object_lifecycle',{}).get('approved_execution_boundary',{}).get('allowed_paths')==[])
    env=execution_authorization_envelope(projection)
    title=('# JOYFLOW BRAIN READ-ONLY DISCOVERY AUTHORIZATION VIEW' if read_only else
           '# JOYFLOW USER MATERIAL EXECUTION APPROVAL VIEW' if zero_product_mutation_material_execution else
           '# JOYFLOW USER MUTATION APPROVAL VIEW')
    lines=[title,'',f"- Project / task: `{projection['project_id']}` / `{projection['task_id']}`",f"- Execution mode: `{projection['execution_mode']}`",f"- Authorization envelope: `{digest(env)}`",'', '## Goal', env['desired_result'],'','## Scope / non-goals']
    lines.extend([f'- Non-goal: {x}' for x in env['non_goals']] or ['- No explicit non-goals'])
    lines += ['', '## Must preserve / must not happen']
    obligations=env['boundary_obligations']
    lines.extend([f"- {r['kind']}: {r['statement']}" for r in obligations if r.get('kind') in {'MUST_DO','MUST_NOT_DO','MUST_PRESERVE','ALLOW_PATH','FORBID_PATH'}] or ['- No additional boundary obligations'])
    if env['user_confirmed_product_tolerances']:
        lines += ['', '## User-confirmed consequence boundaries']
        lines.extend([f"- {r['assumption']} → {r['material_effect']}" for r in env['user_confirmed_product_tolerances']])
    lines += ['', '## Minimum validation']
    lines.extend([f"- {r['obligation_id']}: {r['assertion']}" for r in env['minimum_validation_obligations']] or ['- No executable validation obligation'])
    lines += ['', '## Stop / re-closure conditions']
    lines.extend([f'- {x}' for x in env['stop_conditions']])
    if read_only:
        lines += ['', '- This is Web-Brain authorization for bounded pure read-only Technical Discovery only.', '- Logical authorization does not automatically invoke Local Codex; the handoff remains user-mediated or uses another explicitly available transport.', '- No file/data mutation, Commit, Push, PR mutation, or material side effect is authorized.']
    elif zero_product_mutation_material_execution:
        lines += ['', '- This user decision authorizes only the material execution explicitly contained in the exact envelope above.', '- No product/source file modification, implementation change, local source debugging edit, refactor, product commit, product push, or PR source mutation is authorized because current product mutation paths are empty.', '- Historical review coverage paths remain review-only and may not be converted into product mutation paths.', '- Validation may be executed only as listed in the exact envelope.']
        if projection.get('delivery',{}).get('current_review_transport') is not None:
            lines += ['- Conditional current-review transport may be used only when its exact Projection-bound trigger and surface requirements are satisfied; this view does not represent that transport as already created.']
        lines += ['- If product/source mutation becomes necessary, stop and return for Brain re-closure and a new explicit user authorization.', '- Merge remains a separate exact-PR-head user decision.']
    else:
        lines += ['', '- This user decision authorizes mutation only inside the envelope above.', '- Local Codex may adapt implementation details, debug, refactor locally, and retry tests inside this envelope without renewed approval.', '- A material change to product semantics, active invariants, accepted consequences, mutation scope, minimum validation, or stop conditions requires re-closure and a new user authorization.', '- Merge remains a separate exact-PR-head user decision.']
    lines.append('')
    return '\n'.join(lines)

def approval_binding(projection: dict[str, Any]) -> dict[str, str]:
    view=render_approval_view(projection)
    return {
      'execution_authorization_envelope_digest':digest(execution_authorization_envelope(projection)),
      'approval_view_digest':hashlib.sha256(view.encode('utf-8')).hexdigest(),
      'build_identity_digest':projection['build_identity']['build_identity_digest'],
    }

def parse_prompt(prompt: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    matches = ENVELOPE_RE.findall(prompt)
    if len(matches) != 1:
        raise JoyflowError('prompt must contain exactly one compressed machine envelope')
    envelope = compressed_envelope_decode(matches[0])
    if envelope.get('artifact_type') != 'JOYFLOW_SELF_CONTAINED_DUAL_LAYER_HANDOFF':
        raise JoyflowError('wrong handoff envelope type')
    projection = envelope.get('projection')
    approval_record = envelope.get('approval_record')
    validate_schema(projection, PROJECTION_SCHEMA)
    if projection['projection_digest'] != digest(projection_payload(projection)):
        raise JoyflowError('projection digest mismatch')
    if projection['build_identity'] != build_identity():
        raise JoyflowError('prompt was built by a different ruleset/model/compiler build')
    expected_status=load_model()['approval_requirements']['status_by_execution_mode'][projection.get('execution_mode')]; expected_basis=load_model()['approval_requirements']['basis_by_execution_mode'][projection.get('execution_mode')]; expected_scope=load_model()['approval_requirements']['scope_by_execution_mode'][projection.get('execution_mode')]
    if not isinstance(approval_record,dict) or approval_record.get('owner')!='WEB_BRAIN' or approval_record.get('status')!=expected_status or approval_record.get('basis')!=expected_basis or approval_record.get('scope')!=expected_scope or not approval_record.get('decision_ref') or approval_record.get('binding')!=approval_binding(projection):
        raise JoyflowError('prompt lacks exact route-appropriate execution authorization binding')
    compact_matches=COMPACT_VIEW_RE.findall(prompt)
    if len(compact_matches)!=1:
        raise JoyflowError('prompt must contain exactly one model-visible compact execution view')
    try:
        parsed=json.loads(compact_matches[0])
    except Exception as exc:
        raise JoyflowError('invalid compact execution view JSON') from exc
    expected=compact_execution_view(projection)
    if parsed!=expected:
        raise JoyflowError('prompt compact execution view differs from sealed projection')
    return (projection, approval_record, parsed)

def render_prompt(projection: dict[str, Any], approval_record: dict[str, Any]) -> str:
    if projection['build_identity'] != build_identity():
        raise JoyflowError('projection build identity differs from current runtime')
    expected_status=load_model()['approval_requirements']['status_by_execution_mode'][projection.get('execution_mode')]; expected_basis=load_model()['approval_requirements']['basis_by_execution_mode'][projection.get('execution_mode')]; expected_scope=load_model()['approval_requirements']['scope_by_execution_mode'][projection.get('execution_mode')]
    if not isinstance(approval_record,dict) or approval_record.get('owner')!='WEB_BRAIN' or approval_record.get('status')!=expected_status or approval_record.get('basis')!=expected_basis or approval_record.get('scope')!=expected_scope or not approval_record.get('decision_ref') or approval_record.get('binding')!=approval_binding(projection):
        raise JoyflowError('authorization record lacks exact route-appropriate binding')
    view=compact_execution_view(projection)
    envelope={'artifact_type':'JOYFLOW_SELF_CONTAINED_DUAL_LAYER_HANDOFF','projection':projection,'approval_record':approval_record}
    path_discovery=projection.get('repository_evidence',{}).get('path_discovery',{})
    final_path_decision=path_discovery.get('final_path_decision')
    if projection['execution_mode']=='READ_ONLY':
        path_instruction='No final allowed paths are authorized in this discovery handoff. Return bounded current-source facts only; the Web Brain alone decides the later final mutation boundary. If the task frames material architecture uncertainty, perform goal-conditioned structural discovery before any later path freeze: derive typed semantic relations only from direct repository path/source observations, cover every requested architecture-question closure dimension exactly once, preserve counterevidence/unresolved questions/material omissions in the task structural projection, and do not recommend a final route while structural closure remains unresolved.'
        delivery_instruction='Perform only bounded local read-only discovery. Do not modify files, create commits or PRs, or decide final allowed paths. Return PATH_DISCOVERY_RETURN. Use structural_discovery.mode=GOAL_CONDITIONED only when the current task actually asks a material architecture question; otherwise use NOT_APPLICABLE.'
    elif final_path_decision:
        path_instruction=f"Execute only the WEB_BRAIN-owned FINAL_PATH_DECISION {final_path_decision['decision_digest']} sealed in the machine envelope and summarized by the compact current-source context. Do not widen or replace its allowed paths."
        delivery_instruction='Create or update only the bounded candidate PR. Do not merge.' if projection['delivery']['requires_pr'] else 'Produce only the bounded artifact result; no PR is required.'
        if projection['delivery']['evidence_transport']['mode']=='GITHUB_EXACT_OBJECT_IF_NEEDED':
            delivery_instruction += ' If a frozen transport trigger occurs, write only the current-round Evidence Bundle to the approved temporary transport-only GitHub surface, return the exact-object receipt, and keep it outside the product PR/history.'
        if (projection['delivery'].get('current_review_transport') or {}).get('mode')=='GITHUB_EXACT_OBJECT_IF_NEEDED':
            delivery_instruction += ' After the final source Head exists, place only the four exact current-review inputs on the separately approved temporary transport surface; keep the locator outside that transport commit and keep all inputs outside product history.'
    else:
        path_instruction='This handoff has no sealed final path decision and therefore cannot authorize repository mutation.'
        delivery_instruction='Stop and return the missing path-boundary blocker.'
    lines=[
      'JOYFLOW CODEX EXECUTION PROMPT','',
      'The installed Joyflow Runtime owns fixed schemas, mechanical validators, evidence capture and exact sealed-object verification. The model-visible JSON below contains only the current dynamic task semantics needed for this execution.','',
      f'<JOYFLOW_MACHINE_ENVELOPE encoding="zlib+base64url">{compressed_envelope_encode(envelope)}</JOYFLOW_MACHINE_ENVELOPE>','',
      '<JOYFLOW_COMPACT_EXECUTION_VIEW encoding="json">',visible_json(view),'</JOYFLOW_COMPACT_EXECUTION_VIEW>','',
      'Treat the compact JSON as the current task instruction view; the compressed envelope is the exact machine-verifiable binding and must not be reinterpreted or edited.','',
      ('Codex may inspect only within the Brain-authorized read-only discovery boundary and must return evidence without mutation.' if projection['execution_mode']=='READ_ONLY' else 'Codex may choose an equivalent implementation route only within the approved product semantics, current-source context, execution boundary and stop conditions. It may not change product meaning, user decisions, approval state, acceptance state or merge state.'),
      ('Replay current-source binding against the exact Brain-authorized repository anchor before discovery; any mutation is forbidden.' if projection['execution_mode']=='READ_ONLY' else 'Before repository mutation, replay current-source binding against the exact approved repository. If current source, path sufficiency, impact coverage, validation feasibility or material semantics conflict with the sealed task, stop and return the blocker instead of expanding scope.'),
      path_instruction,delivery_instruction,
      'The candidate result is not repository canonical state. Do not merge. Brain review, user acceptance when applicable, separate user merge approval, and current repository evidence remain outside this execution return.','']
    return '\n'.join(lines)

def compile_handoff(capsule: dict[str, Any]) -> tuple[dict[str, Any], str]:
    projection = build_projection(capsule)
    validate_approval(capsule, projection)
    prompt = render_prompt(projection, capsule['approval_record'])
    verify_prompt(projection, capsule['approval_record'], prompt)
    return (projection, prompt)

def _execution_capture_payload(row: dict[str, Any]) -> dict[str, Any]:
    return strip_digest(row,'capture_sha256')


def _direct_capture_claim(capture: dict[str, Any]) -> str:
    return json.dumps({'capture_kind':capture['capture_kind'],'observed_object':capture['observed_object'],'observation':capture['observation'],'command':capture['command'],'exit_code':capture['exit_code']},ensure_ascii=False,sort_keys=True,separators=(',',':'))


_DIRECT_KIND_BY_CAPTURE={
    'REPOSITORY_HEAD':'REPOSITORY_HEAD_OBSERVATION',
    'REPOSITORY_COMMIT':'REPOSITORY_COMMIT_OBSERVATION',
    'REPOSITORY_STATE':'REPOSITORY_STATE_OBSERVATION',
    'ARTIFACT_SHA256':'ARTIFACT_SHA256_OBSERVATION',
    'SOURCE_MATERIAL_SET':'SOURCE_MATERIAL_SET_OBSERVATION',
    'REPOSITORY_FILE':'REPOSITORY_FILE_SNAPSHOT',
    'REPOSITORY_DIFF':'REPOSITORY_DIFF',
    'TEST_COMMAND':'TEST_RESULT',
}


def validate_codex_execution_evidence_bundle_structure(bundle: dict[str, Any], projection: dict[str, Any]) -> tuple[dict[str, dict[str, Any]],dict[str,dict[str,Any]],dict[str,dict[str,Any]]]:
    validate_schema(bundle,EVIDENCE_BUNDLE_SCHEMA)
    if bundle['evidence_bundle_digest']!=digest(strip_digest(bundle,'evidence_bundle_digest')):
        raise JoyflowError('Codex evidence bundle digest mismatch')
    expected={'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest']}
    if any(bundle.get(k)!=v for k,v in expected.items()):
        raise JoyflowError('Codex evidence bundle is bound to another project/task/round/Projection')
    captures={r['capture_id']:r for r in bundle['raw_captures']}
    if len(captures)!=len(bundle['raw_captures']):
        raise JoyflowError('execution capture IDs must be unique')
    for capture in captures.values():
        if capture['capture_sha256']!=digest(_execution_capture_payload(capture)):
            raise JoyflowError('execution raw capture digest mismatch')
        if not re.fullmatch(r'[0-9a-f]{64}', capture.get('stdout_sha256','')) or not re.fullmatch(r'[0-9a-f]{64}', capture.get('stderr_sha256','')):
            raise JoyflowError('execution raw stdout/stderr byte digest missing or malformed')
        kind=capture['capture_kind']; obs=capture['observation']; obj=capture['observed_object']
        if capture['tool']!='joyflow-typed-execution-evidence-runner':
            raise JoyflowError('execution capture must come from the typed repository-owned runner')
        if kind=='REPOSITORY_HEAD':
            if set(obs)!={'repository_id','remote_url','head_sha'} or obj.get('object_type')!='REPOSITORY' or obj.get('source_mode') not in {'REPOSITORY_REF','EXISTING_PR_HEAD'} or obj.get('object_id')!=obs['repository_id'] or obj.get('ref_or_sha256')!=obs['head_sha']:
                raise JoyflowError('repository-head capture does not derive its observed object')
        elif kind=='REPOSITORY_COMMIT':
            if set(obs)!={'repository_id','remote_url','commit_sha','role'} or obs['role'] not in {'APPROVED_INPUT','EXECUTION_RESULT'} or obj.get('object_type')!='REPOSITORY' or obj.get('source_mode') not in {'REPOSITORY_REF','EXISTING_PR_HEAD'} or obj.get('object_id')!=obs['repository_id'] or obj.get('ref_or_sha256')!=obs['commit_sha']:
                raise JoyflowError('repository-commit capture does not derive its observed object')
        elif kind=='REPOSITORY_STATE':
            required={'capture_phase','head_commit','index_diff_sha256','worktree_diff_sha256','tracked_source_set_sha256','untracked_manifest_sha256','declared_ignored_coverage_sha256','declared_ignored_paths','state_fingerprint_sha256'}
            components={k:obs[k] for k in ('head_commit','index_diff_sha256','worktree_diff_sha256','tracked_source_set_sha256','untracked_manifest_sha256','declared_ignored_coverage_sha256')} if set(obs)==required else {}
            if set(obs)!=required or obs['capture_phase'] not in {'BEFORE','AFTER'} or obs['declared_ignored_paths']!=sorted(set(obs['declared_ignored_paths'])) or obs['state_fingerprint_sha256']!=digest(components) or obj!={'object_type':'REPOSITORY','source_mode':'EXISTING_PR_HEAD','object_id':obj.get('object_id'),'ref_or_sha256':obs['head_commit']}:
                raise JoyflowError('repository-state capture does not derive an exact frozen-source state')
        elif kind=='ARTIFACT_SHA256':
            if set(obs)!={'artifact_id','artifact_path','artifact_sha256','bytes'} or obj.get('object_type')!='ARTIFACT' or obj.get('object_id')!=obs['artifact_id'] or obj.get('ref_or_sha256')!=obs['artifact_sha256'] or obj.get('source_mode') not in {'EXISTING_ARTIFACT','NEW_ARTIFACT'}:
                raise JoyflowError('artifact capture does not derive its observed object')
        elif kind=='SOURCE_MATERIAL_SET':
            if set(obs)!={'materials','source_material_set_digest'} or obj!={'object_type':'ARTIFACT','source_mode':'NEW_ARTIFACT','object_id':'SOURCE_MATERIAL_SET','ref_or_sha256':obs['source_material_set_digest']}:
                raise JoyflowError('source-material-set capture does not derive its observed object')
            if obs['materials']!=_canonical_source_materials(obs['materials']) or obs['source_material_set_digest']!=_source_material_set_digest(obs['materials']):
                raise JoyflowError('source-material-set capture is not canonical')
        elif kind=='REPOSITORY_FILE':
            if set(obs)!={'path','file_sha256','bytes'} or obj.get('object_type')!='REPOSITORY' or not _valid_repo_path(obs['path']):
                raise JoyflowError('repository-file capture is malformed')
        elif kind=='REPOSITORY_DIFF':
            if set(obs)!={'base_ref','head_ref','changed_paths','diff_sha256'} or obj.get('object_type')!='REPOSITORY' or any(not _valid_repo_path(p) for p in obs['changed_paths']):
                raise JoyflowError('repository-diff capture is malformed')
        elif kind=='TEST_COMMAND':
            if set(obs)!={'argv','cwd_scope','target_ref'} or obs.get('cwd_scope')!='SOURCE_ROOT' or not isinstance(obs['argv'],list) or not obs['argv'] or not isinstance(obs.get('target_ref'),str):
                raise JoyflowError('test-command capture is malformed')
        else:
            raise JoyflowError('unknown execution capture kind')
    direct=evidence_map({'evidence_registry':bundle['evidence_rows']})
    if len(direct)!=len(bundle['evidence_rows']):
        raise JoyflowError('execution evidence IDs must be unique')
    for ev in direct.values():
        if ev['claim_digest']!=digest(ev['claim']) or ev['produced_by']!='TOOL':
            raise JoyflowError('execution direct evidence must be tool-produced and claim-bound')
        capture=captures.get(ev['raw_output_ref'])
        if not capture or ev['raw_output_sha256']!=capture['capture_sha256'] or ev['ref']!=capture['capture_id']:
            raise JoyflowError('execution evidence does not bind a preserved raw capture')
        if capture['subject_type']!=ev['subject_type'] or capture['subject_id']!=ev['subject_id']:
            raise JoyflowError('raw capture subject differs from evidence subject')
        if ev['kind']!=_DIRECT_KIND_BY_CAPTURE[capture['capture_kind']] or ev['claim']!=_direct_capture_claim(capture):
            raise JoyflowError('direct evidence kind or claim does not match the typed capture fact')
    derivations={r['derivation_id']:r for r in bundle['derivation_rows']}
    if len(derivations)!=len(bundle['derivation_rows']):
        raise JoyflowError('execution derivation IDs must be unique')
    if set(direct)&set(derivations):
        raise JoyflowError('direct evidence and derivation IDs must be disjoint')
    for row in derivations.values():
        if row['authority']!='EXECUTION_EVIDENCE' or row['produced_by']!='CODEX' or row['claim_digest']!=digest(row['claim']):
            raise JoyflowError('Codex technical derivation authority or claim binding mismatch')
        if not row['source_evidence_refs'] or any(ref not in direct for ref in row['source_evidence_refs']):
            raise JoyflowError('Codex technical derivation must cite preserved direct tool facts')
    return direct,captures,derivations

def _technical_preflight_subject(projection: dict[str, Any]) -> str:
    return f"{projection['project_id']}:{projection['task_id']}:{projection['round_id']}:{projection['projection_digest']}"


def _execution_object_claim(expected: dict[str, Any], observed: dict[str, Any]) -> str:
    return json.dumps({'expected_execution_object':expected,'observed_execution_object':observed},ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _obligation_result_claim(result: dict[str, Any]) -> str:
    return json.dumps({'obligation_id':result['obligation_id'],'dimension':result['dimension'],'subject_digest':result['subject_digest'],'result':result['result'],'finding_summary':result['finding_summary']},ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _candidate_evaluation_claim(result: dict[str, Any]) -> str:
    return json.dumps({'route_id':result['route_id'],'feasibility':result['feasibility'],'rejection_reason':result['rejection_reason']},ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _selected_route_claim(result: dict[str, Any]) -> str:
    return json.dumps({'source':result['source'],'route_id':result['route_id'],'implementation_summary':result['implementation_summary']},ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _alternative_route_claim(result: dict[str, Any]) -> str:
    return json.dumps({
        'route_id': result['route_id'],
        'summary': result['summary'],
        'why_better_than_candidates': result['why_better_than_candidates'],
        'product_semantics_unchanged': result['product_semantics_unchanged'],
        'approved_paths_sufficient': result['approved_paths_sufficient'],
        'important_tradeoff_changed': result['important_tradeoff_changed'],
        'protocol_or_compatibility_changed': result['protocol_or_compatibility_changed'],
        'migration_required': result['migration_required'],
    },ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _technical_objection_claim(status: str, objection: dict[str, Any], expected: dict[str, Any], observed: dict[str, Any]) -> str:
    return json.dumps({'status':status,'finding_id':objection['finding_id'],'failed_obligation_ids':sorted(objection['failed_obligation_ids']),'technical_conflict':objection['technical_conflict'],'minimum_correct_route':objection['minimum_correct_route'],'additional_paths_required':sorted(objection['additional_paths_required']),'expected_execution_object':expected,'observed_execution_object':observed},ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _pr_diff_claim(pr: dict[str, Any]) -> str:
    return json.dumps({'repository_id':pr['repository_id'],'pr_url':pr['pr_url'],'base_commit':pr['base_commit'],'head_sha':pr['head_sha'],'touched_files':sorted(pr['touched_files'])},ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _repository_review_evidence(codex_return: dict[str,Any]) -> dict[str,Any] | None:
    pr=codex_return.get('pr_evidence'); replay=codex_return.get('repository_replay_evidence')
    if pr is not None and replay is not None:
        raise JoyflowError('repository evidence variants are mutually exclusive')
    if pr is not None:
        return {'evidence_variant':'CURRENT_ROUND_PR','repository_id':pr['repository_id'],'pr_number':None,'pr_url':pr['pr_url'],'base_branch':pr['base_branch'],'working_branch':pr['working_branch'],'base_commit':pr['base_commit'],'head_sha':pr['head_sha'],'review_coverage_paths':copy.deepcopy(pr['touched_files']),'diff_evidence_ref':pr['diff_evidence_ref']}
    if replay is not None:
        return {'evidence_variant':'EXISTING_FROZEN_PR_REPLAY','repository_id':replay['repository_id'],'pr_number':replay['pr_number'],'pr_url':replay['pr_url'],'base_branch':replay['base_branch'],'working_branch':replay['working_branch'],'base_commit':replay['base_commit'],'head_sha':replay['frozen_head_sha'],'review_coverage_paths':copy.deepcopy(replay['review_coverage_paths']),'diff_evidence_ref':replay['diff_evidence_ref']}
    return None


def _path_within_allowed(path: str, allowed_paths: list[str]) -> bool:
    return _valid_repo_path(path) and any((fnmatch.fnmatch(path,allowed) or path==allowed.rstrip('/**')) for allowed in allowed_paths)


def _derivation_for_subject(derivations: dict[str,dict[str,Any]], ref: str, *, kind: str, subject_type: str, subject_id: str, context: str) -> dict[str,Any]:
    row=derivations.get(ref)
    if not row or row.get('kind')!=kind or row.get('subject_type')!=subject_type or row.get('subject_id')!=subject_id:
        raise JoyflowError(f'{context} does not bind the required Codex derivation subject')
    return row


def _derivation_source_kinds(row: dict[str,Any], direct: dict[str,dict[str,Any]]) -> set[str]:
    return {direct[ref]['kind'] for ref in row['source_evidence_refs']}


def validate_codex_execution_return_structure(row: dict[str, Any], projection: dict[str, Any], evidence_bundle: dict[str, Any]) -> None:
    if projection.get('execution_mode')=='READ_ONLY':
        raise JoyflowError('read-only discovery must return PATH_DISCOVERY_RETURN, not CODEX_EXECUTION_RETURN')
    validate_schema(row,CODEX_RETURN_SCHEMA)
    validate_task_object_lifecycle(projection)
    if row['return_digest']!=digest(strip_digest(row,'return_digest')):
        raise JoyflowError('Codex execution return digest mismatch')
    direct,captures,derivations=validate_codex_execution_evidence_bundle_structure(evidence_bundle,projection)
    validate_evidence_transport_plan(projection)
    plan=projection['delivery']['evidence_transport']; receipt=row.get('evidence_transport_receipt')
    if plan['mode']=='GITHUB_EXACT_OBJECT_IF_NEEDED':
        if receipt is None: raise JoyflowError('GitHub exact-object Evidence transport requires a receipt')
        validate_evidence_transport_receipt_structure(receipt,projection,evidence_bundle)
    elif receipt is not None:
        raise JoyflowError('non-GitHub Evidence transport may not return a GitHub transport receipt')
    expected={'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest'],'evidence_bundle_digest':evidence_bundle['evidence_bundle_digest']}
    if any(row.get(k)!=v for k,v in expected.items()):
        raise JoyflowError('Codex execution return is bound to another active round or evidence bundle')
    if row['brain_review_status']!='PENDING_BRAIN_REVIEW' or row['user_acceptance_status']!='PENDING_USER_ACCEPTANCE' or row['merge_status']!='NOT_AUTHORIZED':
        raise JoyflowError('Codex may not fill Brain review, user acceptance, or merge authority')
    preflight=row['technical_preflight']; status=preflight['status']; completed=row['execution_status']=='COMPLETED'; space=projection['technical_route_space']
    structural_binding=space.get('source_structural_route_binding')
    structural_result=row['structural_execution_result']
    if structural_binding is None:
        if structural_result!={'status':'NOT_APPLICABLE','approved_structural_closure_digest':None,'actual_consequences':[],'deviation_reason':None}:
            raise JoyflowError('non-structural execution cannot claim structural execution results')
    else:
        if structural_result['approved_structural_closure_digest']!=structural_binding['brain_disposition_digest']:
            raise JoyflowError('structural execution result is bound to another approved structural closure')
        if structural_result['status']=='NOT_APPLICABLE':
            raise JoyflowError('structural execution cannot downgrade the approved structural closure to NOT_APPLICABLE')
        if structural_result['status']=='DEVIATION_DETECTED':
            if not structural_result['deviation_reason'] or row['execution_status']!='BLOCKED' or preflight['execution_decision']!='STOP_FOR_BRAIN_RECLOSURE':
                raise JoyflowError('material structural deviation must stop execution for Brain re-closure')
        elif structural_result['deviation_reason'] is not None:
            raise JoyflowError('preserved structural execution cannot carry a deviation reason')
    expected_obj=_return_object_shape(projection['execution_object']); observed_obj=preflight['observed_execution_object']
    if preflight['expected_execution_object']!=expected_obj:
        raise JoyflowError('technical preflight expected object differs from approved execution object')
    subject=_technical_preflight_subject(projection)
    obj_ev=_evidence_for_subject(direct,preflight['object_observation_evidence_ref'],authority='EXECUTION_EVIDENCE',kinds={'REPOSITORY_HEAD_OBSERVATION','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION'},subject_type='TECHNICAL_PREFLIGHT',subject_id=subject,producers={'TOOL'},context='technical preflight object observation')
    if captures[obj_ev['raw_output_ref']]['observed_object']!=observed_obj:
        raise JoyflowError('execution object raw capture does not match observed object')
    obligations={r['obligation_id']:r for r in space['obligations']}; results=preflight['obligation_results']; result_map={r['obligation_id']:r for r in results}
    if len(result_map)!=len(results) or set(result_map)!=set(obligations):
        raise JoyflowError('Codex must answer the exact Brain technical preflight obligation set')
    allowed_source_kinds={
      'OBJECT_IDENTITY':{'REPOSITORY_HEAD_OBSERVATION','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION'},
      'ROUTE_ASSUMPTION_VALIDITY':{'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION','TEST_RESULT'},
      'PATH_SUFFICIENCY':{'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION'},
      'ACCEPTANCE_FEASIBILITY':{'TEST_RESULT'},
      'PRODUCT_SEMANTIC_PRESERVATION':{'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION'},
      'NON_GOAL_PRESERVATION':{'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION'},
      'TEST_CONTRADICTION':{'TEST_RESULT'},
      'MIGRATION_COMPATIBILITY_IMPACT':{'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION','TEST_RESULT'},
    }
    structural_fact_kinds={'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION'}
    approved_test_argv={tuple(check['argv']) for check in projection['validation'].get('checks',[])}
    def validate_preflight_derivation_sources(drv: dict[str,Any], *, require_structural: bool=False, require_test: bool=False) -> None:
        kinds=_derivation_source_kinds(drv,direct)
        if require_structural and not (kinds&structural_fact_kinds):
            raise JoyflowError('technical derivation lacks a structural current-object fact')
        if require_test and 'TEST_RESULT' not in kinds:
            raise JoyflowError('technical derivation lacks an approved test result')
        for ref in drv['source_evidence_refs']:
            ev=direct[ref]; capture=captures[ev['raw_output_ref']]
            if capture['observed_object']!=observed_obj:
                raise JoyflowError('technical derivation cites a fact from another execution object')
            if ev['kind']=='TEST_RESULT' and (tuple(capture['observation'].get('argv',[])) not in approved_test_argv or capture['command']!=_canonical_argv(capture['observation'].get('argv',[]))):
                raise JoyflowError('technical derivation cites a test command outside the approved argv plan')
    for oid,result in result_map.items():
        obligation=obligations[oid]
        if result['dimension']!=obligation['dimension'] or result['subject_digest']!=obligation['subject_binding']['subject_digest']:
            raise JoyflowError('preflight obligation result does not bind the exact task subject')
        for ref in result['evidence_refs']:
            drv=_derivation_for_subject(derivations,ref,kind='PREFLIGHT_OBLIGATION_DERIVATION',subject_type='TECHNICAL_PREFLIGHT_OBLIGATION',subject_id=oid,context='technical preflight obligation')
            if drv['claim']!=_obligation_result_claim(result):
                raise JoyflowError('preflight obligation derivation does not bind declared result')
            source_kinds=_derivation_source_kinds(drv,direct)
            if result['result']=='NOT_APPLICABLE':
                if status!='REPOSITORY_STATE_MISMATCH' or result['dimension']=='OBJECT_IDENTITY' or set(drv['source_evidence_refs'])!={preflight['object_observation_evidence_ref']}:
                    raise JoyflowError('preflight obligation may be NOT_APPLICABLE only after exact execution-object mismatch')
                validate_preflight_derivation_sources(drv)
                continue
            if not (source_kinds&allowed_source_kinds[result['dimension']]):
                raise JoyflowError('preflight obligation derivation lacks a dimension-compatible direct tool fact')
            validate_preflight_derivation_sources(
                drv,
                require_structural=result['dimension'] in {'ROUTE_ASSUMPTION_VALIDITY','PATH_SUFFICIENCY','PRODUCT_SEMANTIC_PRESERVATION','NON_GOAL_PRESERVATION','MIGRATION_COMPATIBILITY_IMPACT'},
                require_test=result['dimension'] in {'ACCEPTANCE_FEASIBILITY','TEST_CONTRADICTION'},
            )
    routes={r['route_id']:r for r in space['candidate_routes']}; evaluations=preflight['candidate_evaluations']; eval_map={r['route_id']:r for r in evaluations}
    if len(eval_map)!=len(evaluations) or set(eval_map)!=set(routes):
        raise JoyflowError('Codex must evaluate every Brain candidate route exactly once')
    allowed_paths=[x['statement'] for x in projection['decision_boundary'].get('boundary_obligations',[]) if x['kind']=='ALLOW_PATH']
    for rid,result in eval_map.items():
        for ref in result['evidence_refs']:
            drv=_derivation_for_subject(derivations,ref,kind='ROUTE_CANDIDATE_DERIVATION',subject_type='TECHNICAL_ROUTE_CANDIDATE',subject_id=rid,context='candidate route evaluation')
            if drv['claim']!=_candidate_evaluation_claim(result):
                raise JoyflowError('candidate route derivation does not bind evaluation')
            if result['feasibility']=='NOT_EVALUATED':
                if status!='REPOSITORY_STATE_MISMATCH' or set(drv['source_evidence_refs'])!={preflight['object_observation_evidence_ref']}:
                    raise JoyflowError('candidate route may be NOT_EVALUATED only after exact execution-object mismatch')
                validate_preflight_derivation_sources(drv)
                continue
            if not (_derivation_source_kinds(drv,direct)&{'REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','REPOSITORY_COMMIT_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION','TEST_RESULT'}):
                raise JoyflowError('candidate route derivation lacks current-object direct facts')
            validate_preflight_derivation_sources(drv,require_structural=True)
        if result['feasibility']=='PASS' and result['rejection_reason'] is not None:
            raise JoyflowError('passing candidate route cannot have rejection reason')
        if result['feasibility']!='PASS' and not result['rejection_reason']:
            raise JoyflowError('non-passing candidate route requires rejection reason')
        if result['feasibility']=='PASS' and any(not _path_within_allowed(path,allowed_paths) for path in routes[rid]['expected_paths']):
            raise JoyflowError('passing candidate route requires a path outside the approved boundary')
    selected=preflight['selected_route']
    if status=='REPOSITORY_STATE_MISMATCH':
        if selected is not None or preflight['alternative_route'] is not None or any(result['feasibility']!='NOT_EVALUATED' or not result['rejection_reason'] for result in evaluations):
            raise JoyflowError('execution-object mismatch must stop before route evaluation or selection')
    elif selected is None:
        raise JoyflowError('non-mismatch preflight requires a selected technical route')
    if selected is not None:
        for ref in selected['evidence_refs']:
            drv=_derivation_for_subject(derivations,ref,kind='SELECTED_ROUTE_DERIVATION',subject_type='TECHNICAL_ROUTE_SELECTION',subject_id=selected['route_id'],context='selected technical route')
            if drv['claim']!=_selected_route_claim(selected):
                raise JoyflowError('selected route derivation does not bind selection')
            validate_preflight_derivation_sources(drv,require_structural=True)
    material=preflight['material_change_assessment']; material_change=any(material.values()); alternative=preflight['alternative_route']
    if selected is None:
        pass
    elif selected['source']=='BRAIN_CANDIDATE':
        if selected['route_id'] not in routes or eval_map[selected['route_id']]['feasibility']!='PASS' or alternative is not None:
            raise JoyflowError('selected Brain route must be a feasible evaluated candidate')
        if routes[selected['route_id']]['important_tradeoff_owner']!='CODEX_WITHIN_BOUNDARY':
            raise JoyflowError('Codex cannot select a candidate whose important tradeoff belongs to Brain or user')
        if any(not _path_within_allowed(path,allowed_paths) for path in routes[selected['route_id']]['expected_paths']):
            raise JoyflowError('selected Brain route requires a path outside approved allowed_paths')
    else:
        if alternative is None or selected['route_id']!=alternative['route_id']:
            raise JoyflowError('Codex alternative selection requires exact alternative route')
        if any([not alternative['product_semantics_unchanged'],not alternative['approved_paths_sufficient'],alternative['important_tradeoff_changed'],alternative['protocol_or_compatibility_changed'],alternative['migration_required'],material_change]):
            raise JoyflowError('material or boundary-changing Codex alternative requires Brain re-closure')
        for ref in alternative['evidence_refs']:
            drv=_derivation_for_subject(derivations,ref,kind='CODEX_ALTERNATIVE_DERIVATION',subject_type='TECHNICAL_ROUTE_ALTERNATIVE',subject_id=alternative['route_id'],context='Codex alternative route')
            if drv['claim']!=_alternative_route_claim(alternative):
                raise JoyflowError('Codex alternative derivation does not bind the complete alternative route claim')
            validate_preflight_derivation_sources(drv,require_structural=True)
    failed={oid for oid,r in result_map.items() if r['result']=='FAIL'}; dim_failed={obligations[oid]['dimension'] for oid in failed}
    if completed:
        if observed_obj!=expected_obj or any(r['result']!='PASS' for r in results) or preflight['execution_decision']!='EXECUTE':
            raise JoyflowError('completed execution requires matching object, all preflight obligations PASS, and EXECUTE decision')
        if status not in {'ROUTE_CONFIRMED','EQUIVALENT_IMPLEMENTATION_ADJUSTMENT'} or preflight['objection'] is not None:
            raise JoyflowError('completed execution requires confirmed/equivalent status without objection')
        if status=='EQUIVALENT_IMPLEMENTATION_ADJUSTMENT' and not preflight['implementation_decisions']:
            raise JoyflowError('equivalent adjustment requires implementation decisions')
        if row['blocker_evidence_refs'] or row['unresolved_items'] or material_change:
            raise JoyflowError('completed execution cannot carry blockers, unresolved items, or material changes')
    else:
        if preflight['execution_decision']!='STOP_FOR_BRAIN_RECLOSURE' or status not in {'BRAIN_ROUTE_CONFLICT','APPROVAL_SCOPE_INSUFFICIENT','REPOSITORY_STATE_MISMATCH'} or preflight['objection'] is None:
            raise JoyflowError('blocked execution requires stop-for-reclosure and explicit objection')
        if not row['blocker_evidence_refs'] or not row['unresolved_items'] or not failed:
            raise JoyflowError('blocked execution requires failed preflight obligation, blocker evidence and unresolved items')
        expected_dim={'BRAIN_ROUTE_CONFLICT':'ROUTE_ASSUMPTION_VALIDITY','APPROVAL_SCOPE_INSUFFICIENT':'PATH_SUFFICIENCY','REPOSITORY_STATE_MISMATCH':'OBJECT_IDENTITY'}[status]
        if expected_dim not in dim_failed:
            raise JoyflowError('blocked status does not match failed preflight dimension')
        objection=preflight['objection']
        if set(objection['failed_obligation_ids'])!=failed or set(objection['finding_derivation_refs'])!=set(row['blocker_evidence_refs']):
            raise JoyflowError('technical objection must bind all and only failed obligations and blocker derivations')
        for ref in objection['finding_derivation_refs']:
            drv=_derivation_for_subject(derivations,ref,kind='TECHNICAL_OBJECTION_DERIVATION',subject_type='TECHNICAL_PREFLIGHT_FINDING',subject_id=objection['finding_id'],context='technical objection')
            if drv['claim']!=_technical_objection_claim(status,objection,expected_obj,observed_obj):
                raise JoyflowError('technical objection derivation does not bind declared conflict')
        if status=='REPOSITORY_STATE_MISMATCH':
            if expected_obj==observed_obj: raise JoyflowError('object mismatch requires a different observed object')
        elif expected_obj!=observed_obj:
            raise JoyflowError('non-object-mismatch blocker must inspect approved object')
        requested=objection['additional_paths_required']
        if status=='APPROVAL_SCOPE_INSUFFICIENT' and not requested: raise JoyflowError('scope insufficiency must identify additional paths')
        if requested and status!='APPROVAL_SCOPE_INSUFFICIENT': raise JoyflowError('only scope insufficiency may request paths')
        for path in requested:
            if not _valid_repo_path(path) or _path_within_allowed(path,allowed_paths): raise JoyflowError('scope gap path is invalid or already approved')
    mutation=row['mutation_summary']
    if not mutation['mutation_performed'] and (mutation['cleanup_status']!='NOT_REQUIRED' or mutation['residual_changed_paths']): raise JoyflowError('no-mutation return cannot report cleanup or residual paths')
    if completed and mutation['residual_changed_paths']: raise JoyflowError('completed execution cannot carry residual changed paths')
    if not completed and mutation['mutation_performed']:
        if mutation['residual_changed_paths'] and mutation['cleanup_status']!='PENDING': raise JoyflowError('blocked residual changes require pending cleanup')
        if not mutation['residual_changed_paths'] and mutation['cleanup_status']!='COMPLETED': raise JoyflowError('blocked fully recovered mutation requires completed cleanup')
    if mutation['cleanup_status']=='COMPLETED' and mutation['residual_changed_paths']: raise JoyflowError('completed cleanup cannot leave residual paths')
    for residual in mutation['residual_changed_paths']:
        if not _path_within_allowed(residual,allowed_paths): raise JoyflowError('residual changed path outside approved boundary')
    obligations_v={o['obligation_id']:o for o in projection['validation'].get('obligation_registry',[])}; checks={c['check_id']:c for c in projection['validation'].get('checks',[])}
    required_pairs={(oid,cid) for oid,o in obligations_v.items() for cid in o.get('check_ids',[])}; rows=row['machine_results']; pairs=[(r['obligation_id'],r['check_id']) for r in rows]
    if len(pairs)!=len(set(pairs)) or len([r['evidence_ref'] for r in rows])!=len(set(r['evidence_ref'] for r in rows)): raise JoyflowError('duplicate machine validation path or evidence')
    if completed and set(pairs)!=required_pairs: raise JoyflowError('completed return must cover every required machine check')
    for result in rows:
        oid,cid=result['obligation_id'],result['check_id']
        if oid not in obligations_v or cid not in checks or cid not in obligations_v[oid].get('check_ids',[]): raise JoyflowError('unplanned machine validation path')
        if result['actual_argv']!=checks[cid]['argv'] or result['actual_cwd_scope']!='SOURCE_ROOT' or result['actual_command']!=checks[cid]['command'] or result['actual_command']!=_canonical_argv(result['actual_argv']): raise JoyflowError('machine execution object differs from approved argv plus cwd')
        rs,code=result['result'],result['exit_code']
        if (rs=='PASS' and code!=0) or (rs=='FAIL' and (code is None or code==0)) or (rs=='NOT_RUN' and code is not None): raise JoyflowError('machine result and exit code mismatch')
        if completed and rs!='PASS': raise JoyflowError('completed return requires all checks PASS')
        ev=_evidence_for_subject(direct,result['evidence_ref'],authority='EXECUTION_EVIDENCE',kinds={'TEST_RESULT'},subject_type='VALIDATION_CHECK',subject_id=f'{oid}:{cid}',producers={'TOOL'},context='machine validation result')
        capture=captures[ev['raw_output_ref']]
        if capture['capture_kind']!='TEST_COMMAND' or capture['observation'].get('argv')!=result['actual_argv'] or capture['command']!=_canonical_argv(result['actual_argv']) or capture['exit_code']!=result['exit_code']:
            raise JoyflowError('machine result differs from typed approved-argv test capture')
    requires_pr=projection['delivery']['requires_pr']
    operation=projection['task_anchor'].get('repository_operation')
    replay_evidence=row.get('repository_replay_evidence')
    if completed and requires_pr:
        if row['artifact_evidence'] is not None: raise JoyflowError('completed repository task cannot claim Artifact evidence')
        if operation=='CURRENT_ROUND_REPOSITORY_CHANGE' and (not row['pr_evidence'] or replay_evidence is not None): raise JoyflowError('completed current-round repository task requires PR evidence only')
        if operation=='EXISTING_FROZEN_PR_REPLAY' and (row['pr_evidence'] is not None or not replay_evidence): raise JoyflowError('completed existing PR replay requires replay evidence only')
    elif completed:
        if row['pr_evidence'] is not None or replay_evidence is not None or not row['artifact_evidence']: raise JoyflowError('completed artifact task requires artifact evidence only')
    elif sum(x is not None for x in (row['pr_evidence'],replay_evidence,row['artifact_evidence']))>1: raise JoyflowError('blocked execution cannot claim multiple result evidence variants')
    if not completed and requires_pr and row['artifact_evidence'] is not None: raise JoyflowError('blocked repository task cannot claim artifact')
    if not completed and not requires_pr and (row['pr_evidence'] is not None or replay_evidence is not None): raise JoyflowError('blocked artifact task cannot claim repository evidence')
    if row['pr_evidence'] is not None:
        pr=row['pr_evidence']; binding=projection['decision_boundary'].get('repository_binding') or {}
        approved_base=projection['task_object_lifecycle']['approved_input_object']['base_commit']
        if pr['repository_id']!=binding.get('repository_id') or pr['base_branch']!=binding.get('default_branch') or pr['working_branch']!=binding.get('working_branch') or pr['base_commit']!=approved_base: raise JoyflowError('PR binding mismatch')
        diff=_evidence_for_subject(direct,pr['diff_evidence_ref'],authority='EXECUTION_EVIDENCE',kinds={'REPOSITORY_DIFF'},subject_type='PR_HEAD',subject_id=pr['head_sha'],producers={'TOOL'},context='PR diff')
        cap=captures[diff['raw_output_ref']]
        if cap['capture_kind']!='REPOSITORY_DIFF' or cap['observation']['base_ref']!=pr['base_commit'] or cap['observation']['head_ref']!=pr['head_sha'] or sorted(cap['observation']['changed_paths'])!=sorted(pr['touched_files']): raise JoyflowError('PR diff capture does not bind touched paths')
        for path in pr['touched_files']:
            if not _path_within_allowed(path,allowed_paths): raise JoyflowError('Codex touched path outside approved boundary')
        if not mutation['mutation_performed']: raise JoyflowError('PR evidence requires mutation_performed true')
        if not completed and sorted(mutation['residual_changed_paths'])!=sorted(pr['touched_files']): raise JoyflowError('blocked PR residual paths must equal current PR touched files')
    if replay_evidence is not None:
        replay=replay_evidence; anchor=projection['task_anchor']['repository_anchor']; binding=projection['decision_boundary'].get('repository_binding') or {}
        expected={'repository_id':anchor['repository_id'],'pr_number':anchor['pr_number'],'pr_url':anchor['pr_url'],'base_branch':anchor['base_branch'],'working_branch':anchor['working_branch'],'base_commit':anchor['baseline_commit'],'frozen_head_sha':anchor['frozen_head_sha'],'review_coverage_paths':sorted(anchor['review_coverage_paths'])}
        if any(replay.get(k)!=(sorted(v) if k=='review_coverage_paths' else v) for k,v in expected.items()) or replay['evidence_role']!='EXISTING_FROZEN_PR_REVIEW_TARGET':
            raise JoyflowError('repository replay evidence differs from the exact frozen PR anchor')
        if replay['repository_id']!=binding.get('repository_id') or replay['base_branch']!=binding.get('default_branch') or replay['working_branch']!=binding.get('working_branch'):
            raise JoyflowError('repository replay evidence differs from the repository binding')
        diff=_evidence_for_subject(direct,replay['diff_evidence_ref'],authority='EXECUTION_EVIDENCE',kinds={'REPOSITORY_DIFF'},subject_type='PR_HEAD',subject_id=replay['frozen_head_sha'],producers={'TOOL'},context='existing PR replay diff')
        cap=captures[diff['raw_output_ref']]
        if cap['capture_kind']!='REPOSITORY_DIFF' or cap['observation']['base_ref']!=replay['base_commit'] or cap['observation']['head_ref']!=replay['frozen_head_sha'] or sorted(cap['observation']['changed_paths'])!=sorted(replay['review_coverage_paths']):
            raise JoyflowError('existing PR replay diff does not bind exact review coverage')
        state_rows=[]
        for ref,phase in ((replay['source_state_before_evidence_ref'],'BEFORE'),(replay['source_state_after_evidence_ref'],'AFTER')):
            ev=_evidence_for_subject(direct,ref,authority='EXECUTION_EVIDENCE',kinds={'REPOSITORY_STATE_OBSERVATION'},subject_type='REPOSITORY_REPLAY_SOURCE_STATE',subject_id=f"{replay['frozen_head_sha']}:{phase}",producers={'TOOL'},context=f'existing PR replay source state {phase.lower()}')
            state_cap=captures[ev['raw_output_ref']]
            if state_cap['capture_kind']!='REPOSITORY_STATE' or state_cap['observation']['capture_phase']!=phase or state_cap['observation']['head_commit']!=replay['frozen_head_sha']:
                raise JoyflowError('existing PR replay source-state evidence is malformed or moved')
            state_rows.append(state_cap)
        if state_rows[0]['capture_id']==state_rows[1]['capture_id'] or state_rows[0]['observation']['state_fingerprint_sha256']!=state_rows[1]['observation']['state_fingerprint_sha256']:
            raise JoyflowError('existing PR replay changed frozen source HEAD/index/worktree/tracked state')
        if mutation['mutation_performed'] or mutation['cleanup_status']!='NOT_REQUIRED' or mutation['residual_changed_paths']:
            raise JoyflowError('existing PR replay must report exactly zero current product mutation')
    elif completed and requires_pr and operation=='EXISTING_FROZEN_PR_REPLAY': raise JoyflowError('completed existing PR replay lacks replay evidence')
    if row['artifact_evidence'] is not None:
        artifact=row['artifact_evidence']; outputs=artifact['outputs']
        if _canonical_artifact_outputs(outputs)!=[_artifact_output_identity(r) for r in outputs]:
            raise JoyflowError('Artifact outputs must use canonical artifact-id ordering')
        if artifact['output_set_digest']!=_artifact_output_set_digest(outputs):
            raise JoyflowError('Artifact output-set digest mismatch')
        machine_refs={r['evidence_ref'] for r in row['machine_results']}
        for output in outputs:
            digest_ref=None; test_refs=[]
            for ref in output['validation_evidence_refs']:
                ev=direct.get(ref)
                if not ev or ev.get('authority')!='EXECUTION_EVIDENCE' or ev.get('produced_by')!='TOOL' or ev.get('kind') not in {'ARTIFACT_SHA256_OBSERVATION','TEST_RESULT'}:
                    raise JoyflowError('Artifact output evidence lacks a supported direct tool fact')
                cap=captures[ev['raw_output_ref']]
                if cap['observed_object']['object_id']!=output['artifact_id'] or cap['observed_object']['ref_or_sha256']!=output['artifact_digest']:
                    raise JoyflowError('Artifact output evidence is bound to another output')
                if ev['kind']=='ARTIFACT_SHA256_OBSERVATION':
                    if ev.get('subject_type')!='ARTIFACT' or ev.get('subject_id')!=output['artifact_digest']:
                        raise JoyflowError('Artifact digest fact subject differs from the output')
                    digest_ref=ref
                else:
                    if ev.get('subject_type')!='VALIDATION_CHECK':
                        raise JoyflowError('Artifact validation result must bind a planned validation check')
                    test_refs.append(ref)
            if digest_ref is None or not test_refs or not set(test_refs).issubset(machine_refs):
                raise JoyflowError('every Artifact output requires one digest fact and at least one approved output-targeted validation result')
        if not mutation['mutation_performed']: raise JoyflowError('completed artifact output requires mutation_performed true')
    validate_execution_lifecycle_result_structure(row['execution_lifecycle_result'],projection,row)

def _structural_projection_source_refs(row: dict[str, Any]) -> list[dict[str, str]]:
    refs=[]
    for item in row.get('structural_anchors',[]): refs.extend(item.get('source_refs',[]))
    for item in row.get('semantic_fibers',[]): refs.extend(item.get('source_refs',[]))
    refs.extend(row.get('counterevidence_refs',[]))
    unique={ (r['path'],r['source_sha256']):r for r in refs }
    return [unique[k] for k in sorted(unique)]

def validate_long_term_structural_projection(row: dict[str, Any], *, repository: str | pathlib.Path | None=None) -> dict[str, Any]:
    validate_schema(row,LONG_TERM_STRUCTURAL_PROJECTION_SCHEMA)
    if row['projection_digest']!=digest(strip_digest(row,'projection_digest')):
        raise JoyflowError('long-term structural projection digest mismatch')
    anchor_ids=[r['anchor_id'] for r in row['structural_anchors']]
    if len(anchor_ids)!=len(set(anchor_ids)):
        raise JoyflowError('long-term structural anchor IDs must be unique')
    anchor_set=set(anchor_ids)
    fiber_ids=[r['fiber_id'] for r in row['semantic_fibers']]
    if len(fiber_ids)!=len(set(fiber_ids)):
        raise JoyflowError('long-term structural fiber IDs must be unique')
    for fiber in row['semantic_fibers']:
        if fiber['from_anchor'] not in anchor_set or fiber['to_anchor'] not in anchor_set:
            raise JoyflowError('long-term structural fiber references an unknown anchor')
    for ref in _structural_projection_source_refs(row):
        if not _valid_repo_path(ref['path']):
            raise JoyflowError('long-term structural projection contains invalid repository-relative source path')
    result={'freshness':'UNASSESSED','changed_relevant_sources':[],'based_on_commit':row['based_on_commit']}
    if repository is None:
        return result
    root,repo_id,head=_repository_source_identity(repository)
    if row['repository_id']!=repo_id:
        raise JoyflowError('long-term structural projection is bound to another repository')
    _git_source_bytes(root,'cat-file','-e',f"{row['based_on_commit']}^{{commit}}")
    for ref in _structural_projection_source_refs(row):
        data=_git_source_bytes(root,'show',f"{row['based_on_commit']}:{ref['path']}")
        if hashlib.sha256(data).hexdigest()!=ref['source_sha256']:
            raise JoyflowError('long-term structural projection source digest does not match its based-on commit')
    if head==row['based_on_commit']:
        result['freshness']='CURRENT_AT_HEAD'; return result
    ancestry=_run_source_command(['git','-C',str(root),'merge-base','--is-ancestor',row['based_on_commit'],head])
    if ancestry.returncode!=0:
        result['freshness']='CONFLICT_BASE_NOT_ANCESTOR'; return result
    changed=set(_git_source_bytes(root,'diff','--name-only',row['based_on_commit'],head).decode('utf-8','replace').splitlines())
    relevant=sorted({ref['path'] for ref in _structural_projection_source_refs(row)} & changed)
    result['changed_relevant_sources']=relevant
    result['freshness']='STALE_RELEVANT_SOURCE_CHANGED' if relevant else 'CURRENT_FOR_REFERENCED_BASIS'
    return result

def _validate_structural_discovery(row: dict[str, Any], projection: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> None:
    structural=row['structural_discovery']; mode=structural['mode']
    frame=(projection.get('repository_evidence',{}).get('path_discovery',{}) or {}).get('structural_decision_frame')
    _validate_structural_frame(frame,goal_binding_digest=_structural_goal_binding(projection))
    if frame is None:
        if mode!='NOT_APPLICABLE' or structural['architecture_question'] is not None or structural['semantic_relations'] or structural['closure_obligations'] or structural['counterevidence_refs'] or structural['unresolved_structural_questions'] or structural['omitted_material_summary'] or structural['candidate_routes'] or structural['recommended_route_id'] is not None or structural['task_structural_projection']['status']!='NOT_APPLICABLE' or any(structural['task_structural_projection'][k] for k in ('material_relation_ids','counterevidence_refs','unresolved_questions','omitted_material_summary')):
            raise JoyflowError('non-structural discovery must not carry structural conclusions')
        return
    if mode!='GOAL_CONDITIONED':
        raise JoyflowError('Brain-required structural discovery cannot be downgraded to NOT_APPLICABLE')
    q=structural['architecture_question']
    if q is None:
        raise JoyflowError('Brain-required structural discovery lacks the exact architecture question')
    expected_q={'question_id':frame['question_id'],'statement':frame['statement'],'materiality_basis':frame['materiality_basis'],'goal_binding_digest':frame['goal_binding_digest'],'closure_dimensions':frame['required_dimensions'],'frame_digest':frame['frame_digest']}
    if q!=expected_q:
        raise JoyflowError('Codex structural discovery rewrote or substituted the Brain-owned architecture question')
    dims=q['closure_dimensions']; rows=structural['closure_obligations']
    if sorted(r['dimension'] for r in rows)!=sorted(dims) or len(rows)!=len(dims):
        raise JoyflowError('structural discovery closure obligations must cover each requested dimension exactly once')
    relation_ids=[]; relation_by_evidence={}; relation_by_id={}
    for rel in structural['semantic_relations']:
        relation_ids.append(rel['relation_id']); relation_by_id[rel['relation_id']]=rel; relation_by_evidence[rel['evidence_ref']]=rel
        ev=evidence.get(rel['evidence_ref'])
        if not ev or ev['kind']!='STRUCTURAL_RELATION_DERIVATION' or ev['subject_type']!='STRUCTURAL_RELATION' or ev['subject_id']!=rel['relation_id'] or ev['claim']!=_local_item_claim('STRUCTURAL_RELATION_DERIVATION',rel):
            raise JoyflowError('structural relation evidence does not bind the exact semantic relation')
        if sorted(ev['source_evidence_refs'])!=sorted(rel['basis_evidence_refs']):
            raise JoyflowError('structural relation derivation sources differ from relation basis')
        source_snapshot_seen=False
        for ref in rel['basis_evidence_refs']:
            src=evidence.get(ref)
            if not src or src['kind']!='SOURCE_SNAPSHOT_OBSERVATION' or src['produced_by']!='TOOL':
                raise JoyflowError('material structural semantics require direct current source snapshots; path existence alone is insufficient')
            if src.get('observed_path')==rel['source']:
                source_snapshot_seen=True
        if not source_snapshot_seen:
            raise JoyflowError('structural relation source is not grounded by a matching direct source snapshot')
    if len(relation_ids)!=len(set(relation_ids)):
        raise JoyflowError('structural relation IDs must be unique')
    dimension_relation_types={
      'AUTHORITY_BOUNDARY':{'AUTHORITY_WRITER','PROJECTION_CACHE_RELATION'},
      'RULE_OWNERSHIP':{'RULE_OWNERSHIP'},
      'LIFECYCLE':{'LIFECYCLE_TRANSITION'},
      'DEPENDENCY':{'DEPENDENCY','CONSUMER_PRODUCER'},
      'SHARED_CORE':{'SHARED_CORE'},
      'RUNTIME_RELATION':{'RUNTIME_RELATION'},
      'VALIDATION_SURFACE':{'VALIDATION_SURFACE'},
    }
    for closure in rows:
        status=closure['status']; refs=closure['evidence_refs']; app=closure['applicability_basis']
        if status=='UNRESOLVED':
            if closure['unresolved_reason'] is None or app is not None:
                raise JoyflowError('unresolved structural closure requires a reason and cannot claim applicability closure')
        elif status=='CHECKED':
            if closure['unresolved_reason'] is not None or app is not None or not refs:
                raise JoyflowError('checked structural closure requires compatible evidence and no unresolved/applicability substitute')
            compatible=False
            for ref in refs:
                rel=relation_by_evidence.get(ref)
                if rel and rel['relation_type'] in dimension_relation_types[closure['dimension']]:
                    compatible=True
            if not compatible:
                raise JoyflowError('checked structural dimension lacks a dimension-compatible semantic relation')
        elif status=='NOT_APPLICABLE':
            if closure['unresolved_reason'] is not None or not app or not refs:
                raise JoyflowError('NOT_APPLICABLE structural dimension requires explicit current-source applicability basis and evidence')
            for ref in refs:
                src=evidence.get(ref)
                if not src or src['kind'] not in {'SOURCE_SNAPSHOT_OBSERVATION','STRUCTURAL_RELATION_DERIVATION'}:
                    raise JoyflowError('structural NOT_APPLICABLE basis lacks compatible current-source evidence')
        for ref in refs:
            if ref not in evidence:
                raise JoyflowError('structural closure cites unknown evidence')
    all_unresolved=bool(structural['unresolved_structural_questions']) or any(r['status']=='UNRESOLVED' for r in rows)
    taskp=structural['task_structural_projection']; expected_status='INCOMPLETE' if all_unresolved else 'CLOSED'
    if taskp['status']!=expected_status:
        raise JoyflowError('task structural projection closure status does not match unresolved structural state')
    if sorted(taskp['material_relation_ids'])!=sorted(r['relation_id'] for r in structural['semantic_relations'] if r['materiality']=='MATERIAL'):
        raise JoyflowError('task structural projection must preserve every material semantic relation')
    if sorted(taskp['counterevidence_refs'])!=sorted(structural['counterevidence_refs']) or sorted(taskp['unresolved_questions'])!=sorted(structural['unresolved_structural_questions']) or sorted(taskp['omitted_material_summary'])!=sorted(structural['omitted_material_summary']):
        raise JoyflowError('task structural projection may not drop counterevidence, unresolved questions or material omissions')
    for ref in structural['counterevidence_refs']:
        if ref not in evidence: raise JoyflowError('structural counterevidence reference is unknown')
    route_ids=[]
    for route in structural['candidate_routes']:
        route_ids.append(route['route_id']); ev=evidence.get(route['evidence_ref'])
        if not ev or ev['kind']!='ARCHITECTURE_ROUTE_DERIVATION' or ev['subject_type']!='ARCHITECTURE_ROUTE' or ev['subject_id']!=route['route_id'] or ev['claim']!=_local_item_claim('ARCHITECTURE_ROUTE_DERIVATION',route):
            raise JoyflowError('architecture route evidence does not bind the exact candidate route')
        if sorted(ev['source_evidence_refs'])!=sorted(route['evidence_refs']):
            raise JoyflowError('architecture route derivation sources differ from route evidence refs')
        if not route['evidence_refs'] or any(ref not in relation_by_evidence for ref in route['evidence_refs']):
            raise JoyflowError('architecture route must derive from exact structural semantic relations, not generic path evidence')
    if len(route_ids)!=len(set(route_ids)): raise JoyflowError('architecture route IDs must be unique')
    if structural['recommended_route_id'] is not None and structural['recommended_route_id'] not in route_ids:
        raise JoyflowError('recommended architecture route is not one of the discovered candidate routes')
    if all_unresolved and structural['recommended_route_id'] is not None:
        raise JoyflowError('incomplete structural discovery cannot recommend a final architecture route')

def validate_path_discovery_return_structure(row: dict[str, Any], projection: dict[str, Any]) -> None:
    validate_schema(row, PATH_DISCOVERY_RETURN_SCHEMA)
    if row['return_digest'] != digest(strip_digest(row, 'return_digest')):
        raise JoyflowError('Path Discovery Return digest mismatch')
    if projection.get('route_profile') != 'READ_ONLY_DISCOVERY' or projection.get('execution_mode') != 'READ_ONLY' or projection.get('delivery',{}).get('mutation_allowed') is not False:
        raise JoyflowError('Path Discovery Return requires an exact Web-Brain-authorized read-only discovery Projection')
    expected={'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest']}
    if any(row.get(k)!=v for k,v in expected.items()):
        raise JoyflowError('Path Discovery Return is bound to another task round or Projection')
    anchor=projection['task_anchor'].get('repository_anchor') or {}
    if row['repository']['repository_id'] != anchor.get('repository_id'):
        raise JoyflowError('Path Discovery Return repository mismatch')
    expected_github_ref=projection.get('repository_evidence',{}).get('path_discovery',{}).get('github_ref')
    if row['repository']['github_ref'] != expected_github_ref:
        raise JoyflowError('Path Discovery Return GitHub ref differs from the Brain discovery basis')

    coverage=row['ignored_path_coverage']
    if coverage['mode']!='DECLARED_EXECUTION_RELEVANT_ONLY' or coverage['full_local_filesystem_unchanged_claim'] is not False:
        raise JoyflowError('ignored-path coverage must remain bounded and cannot claim the full local filesystem')
    coverage=_normalize_ignored_coverage(coverage)
    if coverage['coverage_status']=='READ_ONLY_COVERAGE_INCOMPLETE' and not row['unresolved_questions']:
        raise JoyflowError('incomplete ignored-path coverage requires an unresolved question')

    evidence={r['evidence_id']:r for r in row['evidence_rows']}
    if len(evidence)!=len(row['evidence_rows']):
        raise JoyflowError('Path Discovery Return evidence IDs must be unique')
    direct_kinds={'GIT_STATE_FINGERPRINT','PATH_OBSERVATION','SOURCE_SNAPSHOT_OBSERVATION'}
    derivation_kinds={'PATH_CANDIDATE_DERIVATION','DEPENDENCY_DERIVATION','VALIDATION_ENTRY_DERIVATION','LOCAL_FINDING_DERIVATION','STRUCTURAL_RELATION_DERIVATION','ARCHITECTURE_ROUTE_DERIVATION'}
    for ev in evidence.values():
        if ev['claim_digest'] != digest(ev['claim']):
            raise JoyflowError('Path Discovery Return evidence claim digest mismatch')
        if ev['kind'] in direct_kinds:
            if ev['produced_by']!='TOOL' or not ev.get('raw_output_ref') or not re.fullmatch(r'[0-9a-f]{64}',ev.get('raw_output_sha256','')) or ev.get('source_evidence_refs'):
                raise JoyflowError('direct Path Discovery evidence must be TOOL-produced and raw-output bound')
            if ev['kind']=='PATH_OBSERVATION':
                if ev['subject_type']!='REPOSITORY_PATH' or not ev.get('observed_path') or ev.get('source_sha256') is not None or ev['claim']!=_path_observation_claim(ev['subject_id'],ev['observed_path']):
                    raise JoyflowError('direct path observation does not bind one exact path')
            elif ev['kind']=='SOURCE_SNAPSHOT_OBSERVATION':
                if ev['subject_type']!='REPOSITORY_SOURCE_SNAPSHOT' or not ev.get('observed_path') or not re.fullmatch(r'[0-9a-f]{64}',ev.get('source_sha256') or '') or ev['claim']!=_source_snapshot_claim(ev['subject_id'],ev['observed_path'],ev['source_sha256']):
                    raise JoyflowError('direct source snapshot observation does not bind exact repository bytes')
            elif ev.get('observed_path') is not None or ev.get('source_sha256') is not None:
                raise JoyflowError('non-source direct evidence cannot carry source snapshot fields')
        elif ev['kind'] in derivation_kinds:
            if ev['produced_by']!='CODEX' or ev.get('raw_output_ref') is not None or ev.get('raw_output_sha256') is not None or ev.get('observed_path') is not None or ev.get('source_sha256') is not None or not ev.get('source_evidence_refs'):
                raise JoyflowError('local semantic relation must be a Codex derivation over direct repository facts')
            allowed_sources={'PATH_OBSERVATION','SOURCE_SNAPSHOT_OBSERVATION','STRUCTURAL_RELATION_DERIVATION'} if ev['kind']=='ARCHITECTURE_ROUTE_DERIVATION' else {'PATH_OBSERVATION','SOURCE_SNAPSHOT_OBSERVATION'}
            if any(ref not in evidence or evidence[ref]['kind'] not in allowed_sources for ref in ev['source_evidence_refs']):
                raise JoyflowError('local derivation cites a missing or incompatible repository fact')
        else:
            raise JoyflowError('unsupported Path Discovery evidence kind')

    before=row['repository_state_before']; after=row['repository_state_after']
    validate_worktree_fingerprint(before,evidence,expected_phase='BEFORE')
    validate_worktree_fingerprint(after,evidence,expected_phase='AFTER')
    if before['capture_id']==after['capture_id'] or before['evidence_ref']==after['evidence_ref']:
        raise JoyflowError('read-only discovery requires distinct before and after capture records')
    if row['mutation_performed'] is not False or before['state_fingerprint_sha256'] != after['state_fingerprint_sha256']:
        raise JoyflowError('read-only discovery changed the declared repository state or reported mutation')

    all_ids=[]
    confirmed=row['confirmed_paths']; ids=[item['path_id'] for item in confirmed]
    if len(ids)!=len(set(ids)): raise JoyflowError('confirmed_paths item IDs must be unique')
    all_ids.extend(ids)
    for item in confirmed:
        ev=evidence.get(item['evidence_ref'])
        if not ev or ev['kind']!='PATH_OBSERVATION' or ev['subject_id']!=item['path_id'] or ev['observed_path']!=item['path']:
            raise JoyflowError('confirmed path lacks exact direct path observation')

    group_specs=(
      ('candidate_paths','path_id','PATH_CANDIDATE_DERIVATION','REPOSITORY_PATH_CANDIDATE'),
      ('dependency_edges','edge_id','DEPENDENCY_DERIVATION','DEPENDENCY_EDGE'),
      ('validation_entries','validation_id','VALIDATION_ENTRY_DERIVATION','VALIDATION_ENTRY'),
      ('local_only_findings','finding_id','LOCAL_FINDING_DERIVATION','LOCAL_FINDING'),
    )
    for group,id_key,kind,subject_type in group_specs:
        rows=row[group]; ids=[item[id_key] for item in rows]
        if len(ids)!=len(set(ids)): raise JoyflowError(f'{group} item IDs must be unique')
        all_ids.extend(ids)
        for item in rows:
            ev=evidence.get(item['evidence_ref'])
            if not ev or ev['kind']!=kind or ev['subject_type']!=subject_type or ev['subject_id']!=item[id_key]:
                raise JoyflowError(f'{group} item lacks compatible Codex derivation')
            if ev['claim']!=_local_item_claim(kind,item):
                raise JoyflowError(f'{group} derivation does not bind the exact item')
    if len(all_ids)!=len(set(all_ids)):
        raise JoyflowError('Path Discovery Return item IDs must be globally unique')
    for group in ('confirmed_paths','candidate_paths'):
        for item in row[group]:
            if not _valid_repo_path(item['path']): raise JoyflowError('Path Discovery Return contains invalid repository-relative path')
    for edge in row['dependency_edges']:
        if not _valid_repo_path(edge['from']) or not _valid_repo_path(edge['to']): raise JoyflowError('Path Discovery Return contains invalid dependency path')
    for val in row['validation_entries']:
        if not _valid_repo_path(val['path']): raise JoyflowError('Path Discovery Return contains invalid validation path')
    for finding in row['local_only_findings']:
        if any(not _valid_repo_path(path) for path in finding['affected_paths']): raise JoyflowError('Path Discovery Return contains invalid local-finding path')
    _validate_structural_discovery(row,projection,evidence)

def validate_execution_projection_sources(projection: dict[str,Any], *, repository: str | pathlib.Path, path_discovery_return: dict[str,Any] | None=None, path_discovery_projection: dict[str,Any] | None=None) -> None:
    validate_schema(projection, PROJECTION_SCHEMA)
    verify_projection_path_sources_against_repository(projection, repository, path_discovery_return, path_discovery_projection, require_current_head=True)

def validate_path_discovery_return(row: dict[str,Any], projection: dict[str,Any], *, repository: str | pathlib.Path) -> None:
    validate_path_discovery_return_structure(row,projection)
    verify_path_discovery_return_against_repository(row,projection,repository)

def validate_codex_execution_evidence_bundle(bundle: dict[str,Any], projection: dict[str,Any], *, repository: str | pathlib.Path | None=None, artifact: str | pathlib.Path | None=None, artifact_outputs: list[str | pathlib.Path] | None=None, artifact_output_root: str | pathlib.Path | None=None, replay_tests: bool=True, source_materials: dict[str,str | pathlib.Path] | None=None) -> tuple[dict[str,dict[str,Any]],dict[str,dict[str,Any]],dict[str,dict[str,Any]]]:
    result=validate_codex_execution_evidence_bundle_structure(bundle,projection)
    verify_execution_evidence_bundle_against_source(bundle,projection,repository=repository,artifact=artifact,artifact_outputs=artifact_outputs,artifact_output_root=artifact_output_root,replay_tests=replay_tests,execution_lifecycle_result=None,source_materials=source_materials)
    return result

def validate_codex_execution_return(row: dict[str,Any], projection: dict[str,Any], evidence_bundle: dict[str,Any], *, repository: str | pathlib.Path | None=None, artifact: str | pathlib.Path | None=None, artifact_outputs: list[str | pathlib.Path] | None=None, artifact_output_root: str | pathlib.Path | None=None, replay_tests: bool=True, path_discovery_return: dict[str,Any] | None=None, path_discovery_projection: dict[str,Any] | None=None, source_materials: dict[str,str | pathlib.Path] | None=None) -> None:
    validate_codex_execution_return_structure(row,projection,evidence_bundle)
    if projection['execution_object']['object_type']=='REPOSITORY':
        if repository is None:
            raise JoyflowError('strict Codex Return validation requires the current repository source')
        verify_projection_path_sources_against_repository(projection,repository,path_discovery_return,path_discovery_projection)
    elif projection['execution_object']['source_mode']=='EXISTING_ARTIFACT':
        if artifact is None or source_materials:
            raise JoyflowError('strict existing Artifact Return validation requires the current source Artifact')
    elif artifact is not None or not source_materials:
        raise JoyflowError('strict new Artifact Return validation requires the exact source-material set')
    verify_execution_evidence_bundle_against_source(evidence_bundle,projection,repository=repository,artifact=artifact,artifact_outputs=artifact_outputs,artifact_output_root=artifact_output_root,replay_tests=replay_tests,execution_lifecycle_result=row['execution_lifecycle_result'],source_materials=source_materials)

def _post_freeze_acceptance_binding(capsule: dict[str, Any], merge_candidate_freeze: dict[str, Any]) -> dict[str, Any]:
    validate_capsule(capsule)
    validate_schema(merge_candidate_freeze, MERGE_FREEZE_SCHEMA)
    if merge_candidate_freeze['freeze_digest'] != digest(strip_digest(merge_candidate_freeze, 'freeze_digest')):
        raise JoyflowError('merge candidate freeze digest mismatch')
    try:
        review = capsule['active_fibers']['execution_review']['payload']
    except (KeyError, TypeError) as exc:
        raise JoyflowError('user acceptance Capsule lacks execution_review payload') from exc
    target = review.get('review_target') or {}
    if capsule.get('task_progress',{}).get('stage') != 'MERGE_DECISION':
        raise JoyflowError('user acceptance must be recorded after the exact Merge Candidate Freeze')
    if review.get('brain_review_verdict') != 'PASS':
        raise JoyflowError('user acceptance requires current Brain Review PASS')
    if target.get('target_type') != 'REPOSITORY_PR_HEAD' or target.get('repository_id') != merge_candidate_freeze['repository_id'] or target.get('head_sha') != merge_candidate_freeze['head_sha']:
        raise JoyflowError('user acceptance Capsule is bound to another frozen PR Head')
    if review.get('merge_candidate_freeze_digest') != merge_candidate_freeze['freeze_digest']:
        raise JoyflowError('user acceptance Capsule is not bound to the exact Merge Candidate Freeze')
    status = review.get('user_acceptance')
    if status == 'PASS':
        if not review.get('user_acceptance_evidence_refs') or review.get('acceptance_not_applicable_reason') is not None:
            raise JoyflowError('user acceptance PASS requires a current user decision reference')
    elif status == 'NOT_APPLICABLE':
        if review.get('user_acceptance_evidence_refs') or not review.get('acceptance_not_applicable_reason'):
            raise JoyflowError('NOT_APPLICABLE acceptance requires a reason')
    else:
        raise JoyflowError('pending or blocked user acceptance cannot authorize merge')
    return {'status': status, 'target': target, 'review': review}


def validate_user_merge_authorization(
    row: dict[str, Any],
    merge_candidate_freeze: dict[str, Any] | None = None,
    user_acceptance_capsule: dict[str, Any] | None = None,
) -> None:
    validate_schema(row, USER_MERGE_AUTHORIZATION_SCHEMA)
    if row['authorization_digest'] != digest(strip_digest(row, 'authorization_digest')):
        raise JoyflowError('user merge authorization digest mismatch')
    if row['owner'] != 'USER' or row['decision'] != 'ALLOW_MERGE':
        raise JoyflowError('merge authorization must be an explicit current USER decision')
    if merge_candidate_freeze is None or user_acceptance_capsule is None:
        raise JoyflowError('user merge authorization requires the exact freeze and post-freeze acceptance Capsule')
    acceptance = _post_freeze_acceptance_binding(user_acceptance_capsule, merge_candidate_freeze)
    if row['merge_candidate_freeze_digest'] != merge_candidate_freeze['freeze_digest']:
        raise JoyflowError('user merge authorization is bound to another merge candidate freeze')
    if row['user_acceptance_capsule_digest'] != user_acceptance_capsule['capsule_digest']:
        raise JoyflowError('user merge authorization is bound to another acceptance Capsule')
    if acceptance['target']['head_sha'] != merge_candidate_freeze['head_sha']:
        raise JoyflowError('user merge authorization does not bind the current frozen PR Head')


def validate_merge_gate_record(
    row: dict[str, Any],
    merge_candidate_freeze: dict[str, Any] | None = None,
    user_acceptance_capsule: dict[str, Any] | None = None,
    user_authorization: dict[str, Any] | None = None,
) -> None:
    # MERGE_READY / MERGE_ALLOWED are optional derived diagnostic snapshots.
    # They never authorize merge and are not predecessors of task completion.
    validate_schema(row, MERGE_GATE_SCHEMA)
    if row['record_digest'] != digest(strip_digest(row, 'record_digest')):
        raise JoyflowError('merge gate derived snapshot digest mismatch')
    if row.get('artifact_role') != 'DERIVED_GATE_SNAPSHOT_ONLY' or row.get('owner') != 'WEB_BRAIN':
        raise JoyflowError('merge gate record is not a derived Web Brain diagnostic snapshot')
    if merge_candidate_freeze is None or user_acceptance_capsule is None:
        raise JoyflowError('derived merge gate snapshot requires exact freeze and acceptance inputs')
    acceptance = _post_freeze_acceptance_binding(user_acceptance_capsule, merge_candidate_freeze)
    target = acceptance['target']
    expected = {
        'project_id': merge_candidate_freeze['project_id'], 'task_id': merge_candidate_freeze['task_id'],
        'round_id': merge_candidate_freeze['round_id'], 'repository_id': merge_candidate_freeze['repository_id'],
        'pr_url': target.get('pr_url'), 'reviewed_head_sha': merge_candidate_freeze['head_sha'],
        'merge_candidate_freeze_digest': merge_candidate_freeze['freeze_digest'],
        'user_acceptance_status': acceptance['status'], 'user_acceptance_capsule_digest': user_acceptance_capsule['capsule_digest'],
    }
    if any(row.get(k) != v for k, v in expected.items()):
        raise JoyflowError('derived merge gate snapshot differs from the exact freeze/acceptance state')
    if row['status'] == 'MERGE_READY':
        if row.get('user_merge_authorization_digest') is not None or row.get('derivation_basis') != 'CURRENT_FREEZE_AND_ACCEPTANCE':
            raise JoyflowError('MERGE_READY snapshot must be derived only from current freeze and acceptance')
    elif row['status'] == 'MERGE_ALLOWED':
        if user_authorization is None:
            raise JoyflowError('MERGE_ALLOWED snapshot requires exact USER authorization input')
        validate_user_merge_authorization(user_authorization, merge_candidate_freeze, user_acceptance_capsule)
        if row.get('user_merge_authorization_digest') != user_authorization['authorization_digest'] or row.get('derivation_basis') != 'CURRENT_FREEZE_ACCEPTANCE_AND_USER_AUTHORIZATION':
            raise JoyflowError('MERGE_ALLOWED snapshot differs from the exact USER authorization')


def validate_completion_pointer(
    row: dict[str, Any],
    merge_candidate_freeze: dict[str, Any] | None = None,
    user_acceptance_capsule: dict[str, Any] | None = None,
    user_authorization: dict[str, Any] | None = None,
) -> None:
    validate_schema(row, COMPLETION_POINTER_SCHEMA)
    if row['pointer_digest'] != digest(strip_digest(row, 'pointer_digest')):
        raise JoyflowError('task completion pointer digest mismatch')
    if row['owner'] != 'WEB_BRAIN':
        raise JoyflowError('only WEB_BRAIN may record observed repository result')
    if merge_candidate_freeze is None or user_acceptance_capsule is None or user_authorization is None:
        raise JoyflowError('completion pointer requires exact freeze, acceptance Capsule and USER merge authorization')
    validate_user_merge_authorization(user_authorization, merge_candidate_freeze, user_acceptance_capsule)
    acceptance = _post_freeze_acceptance_binding(user_acceptance_capsule, merge_candidate_freeze)
    target = acceptance['target']
    expected = {
        'project_id': merge_candidate_freeze['project_id'], 'task_id': merge_candidate_freeze['task_id'],
        'round_id': merge_candidate_freeze['round_id'], 'repository_id': merge_candidate_freeze['repository_id'],
        'pr_url': target.get('pr_url'), 'reviewed_head_sha': merge_candidate_freeze['head_sha'],
        'merge_candidate_freeze_digest': merge_candidate_freeze['freeze_digest'],
        'user_acceptance_capsule_digest': user_acceptance_capsule['capsule_digest'],
        'user_merge_authorization_digest': user_authorization['authorization_digest'],
    }
    if any(row.get(k) != v for k, v in expected.items()):
        raise JoyflowError('completion pointer changed or bypassed the exact frozen/user-authorized merge object')

def validate_build_identity(*_: Any) -> dict[str, Any]:
    return build_identity()

def validate_promotion_gate(*_: Any) -> None:
    raise JoyflowError('automatic promotion is outside Joyflow human semi-automatic architecture')

def _parse_source_material_args(values: list[str] | None) -> dict[str,str]:
    result={}
    for value in values or []:
        if '=' not in value:
            raise JoyflowError('source material must use MATERIAL_ID=PATH')
        material_id,path=value.split('=',1)
        if not material_id or not path or material_id in result:
            raise JoyflowError('source material IDs and paths must be non-empty and unique')
        result[material_id]=path
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    seal = sub.add_parser('seal'); seal.add_argument('input'); seal.add_argument('output'); seal.add_argument('--previous'); seal.add_argument('--projection'); seal.add_argument('--codex-return'); seal.add_argument('--evidence-bundle'); seal.add_argument('--path-discovery-projection'); seal.add_argument('--path-discovery-return'); seal.add_argument('--source-repository'); seal.add_argument('--source-artifact'); seal.add_argument('--source-material',action='append',default=[]); seal.add_argument('--artifact-output', action='append', default=[]); seal.add_argument('--artifact-output-root')
    seal_repo = sub.add_parser('seal-repository-review'); seal_repo.add_argument('input'); seal_repo.add_argument('output'); seal_repo.add_argument('--previous',required=True); seal_repo.add_argument('--projection',required=True); seal_repo.add_argument('--codex-return',required=True); seal_repo.add_argument('--evidence-bundle',required=True); seal_repo.add_argument('--source-repository',required=True); seal_repo.add_argument('--path-discovery-projection'); seal_repo.add_argument('--path-discovery-return')
    seal_art = sub.add_parser('seal-artifact-review'); seal_art.add_argument('input'); seal_art.add_argument('output'); seal_art.add_argument('--previous',required=True); seal_art.add_argument('--projection',required=True); seal_art.add_argument('--codex-return',required=True); seal_art.add_argument('--evidence-bundle',required=True); seal_art.add_argument('--source-artifact'); seal_art.add_argument('--source-material',action='append',default=[]); seal_art.add_argument('--artifact-output',action='append',required=True); seal_art.add_argument('--artifact-output-root',required=True)
    draft = sub.add_parser('draft'); draft.add_argument('capsule'); draft.add_argument('projection'); draft.add_argument('approval_view'); draft.add_argument('binding')
    compile_cmd = sub.add_parser('compile'); compile_cmd.add_argument('capsule'); compile_cmd.add_argument('projection'); compile_cmd.add_argument('prompt')
    verify = sub.add_parser('verify'); verify.add_argument('projection'); verify.add_argument('approval_record'); verify.add_argument('prompt')
    codex_ret = sub.add_parser('verify-codex-return'); codex_ret.add_argument('return_file'); codex_ret.add_argument('projection'); codex_ret.add_argument('evidence_bundle'); codex_ret.add_argument('--repository'); codex_ret.add_argument('--artifact'); codex_ret.add_argument('--source-material',action='append',default=[]); codex_ret.add_argument('--artifact-output', action='append', default=[]); codex_ret.add_argument('--artifact-output-root'); codex_ret.add_argument('--path-discovery-projection'); codex_ret.add_argument('--path-discovery-return')
    path_ret = sub.add_parser('verify-path-discovery-return'); path_ret.add_argument('return_file'); path_ret.add_argument('projection'); path_ret.add_argument('--repository', required=True)
    structural_projection = sub.add_parser('verify-structural-projection'); structural_projection.add_argument('projection_file'); structural_projection.add_argument('--repository')
    projection_source = sub.add_parser('verify-execution-projection'); projection_source.add_argument('projection'); projection_source.add_argument('--repository', required=True); projection_source.add_argument('--path-discovery-projection'); projection_source.add_argument('--path-discovery-return')
    merge_rec = sub.add_parser('verify-merge-record'); merge_rec.add_argument('record'); merge_rec.add_argument('--merge-freeze', required=True); merge_rec.add_argument('--user-acceptance-capsule', required=True); merge_rec.add_argument('--user-authorization')
    completion = sub.add_parser('verify-completion-pointer'); completion.add_argument('pointer'); completion.add_argument('--merge-freeze', required=True); completion.add_argument('--user-acceptance-capsule', required=True); completion.add_argument('--user-authorization', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'seal':
            previous = load_json(args.previous) if args.previous else None; review_projection = load_json(args.projection) if args.projection else None; codex_return = load_json(args.codex_return) if args.codex_return else None; evidence_bundle = load_json(args.evidence_bundle) if args.evidence_bundle else None; discovery_projection = load_json(args.path_discovery_projection) if args.path_discovery_projection else None; discovery_return = load_json(args.path_discovery_return) if args.path_discovery_return else None; write_json(args.output, prepare_capsule(load_json(args.input), previous, review_projection=review_projection, codex_return=codex_return, evidence_bundle=evidence_bundle, path_discovery_projection=discovery_projection, path_discovery_return=discovery_return, source_repository=args.source_repository, source_artifact=args.source_artifact, source_materials=_parse_source_material_args(args.source_material), artifact_outputs=args.artifact_output, artifact_output_root=args.artifact_output_root, replay_tests=True))
        elif args.command == 'seal-repository-review':
            write_json(args.output,prepare_repository_review_capsule(load_json(args.input),load_json(args.previous),review_projection=load_json(args.projection),codex_return=load_json(args.codex_return),evidence_bundle=load_json(args.evidence_bundle),source_repository=args.source_repository,path_discovery_projection=load_json(args.path_discovery_projection) if args.path_discovery_projection else None,path_discovery_return=load_json(args.path_discovery_return) if args.path_discovery_return else None))
        elif args.command == 'seal-artifact-review':
            write_json(args.output,prepare_artifact_review_capsule(load_json(args.input),load_json(args.previous),review_projection=load_json(args.projection),codex_return=load_json(args.codex_return),evidence_bundle=load_json(args.evidence_bundle),source_artifact=args.source_artifact,source_materials=_parse_source_material_args(args.source_material),artifact_outputs=args.artifact_output,artifact_output_root=args.artifact_output_root))
        elif args.command == 'draft':
            projection, view, binding = draft_handoff(load_json(args.capsule)); write_json(args.projection, projection); pathlib.Path(args.approval_view).write_text(view, encoding='utf-8'); write_json(args.binding, binding)
        elif args.command == 'compile':
            projection, prompt = compile_handoff(load_json(args.capsule)); write_json(args.projection, projection); pathlib.Path(args.prompt).write_text(prompt, encoding='utf-8')
        elif args.command == 'verify':
            verify_prompt(load_json(args.projection), load_json(args.approval_record), pathlib.Path(args.prompt).read_text(encoding='utf-8'))
        elif args.command == 'verify-codex-return':
            validate_codex_execution_return(load_json(args.return_file), load_json(args.projection), load_json(args.evidence_bundle), repository=args.repository, artifact=args.artifact, source_materials=_parse_source_material_args(args.source_material), artifact_outputs=args.artifact_output, artifact_output_root=args.artifact_output_root, replay_tests=True, path_discovery_projection=load_json(args.path_discovery_projection) if args.path_discovery_projection else None, path_discovery_return=load_json(args.path_discovery_return) if args.path_discovery_return else None)
        elif args.command == 'verify-path-discovery-return':
            validate_path_discovery_return(load_json(args.return_file), load_json(args.projection), repository=args.repository)
        elif args.command == 'verify-structural-projection':
            print(json.dumps(validate_long_term_structural_projection(load_json(args.projection_file), repository=args.repository), ensure_ascii=False))
        elif args.command == 'verify-execution-projection': validate_execution_projection_sources(load_json(args.projection), repository=args.repository, path_discovery_projection=load_json(args.path_discovery_projection) if args.path_discovery_projection else None, path_discovery_return=load_json(args.path_discovery_return) if args.path_discovery_return else None)
        elif args.command == 'verify-merge-record': validate_merge_gate_record(load_json(args.record), load_json(args.merge_freeze), load_json(args.user_acceptance_capsule), load_json(args.user_authorization) if args.user_authorization else None)
        elif args.command == 'verify-completion-pointer':
            freeze=load_json(args.merge_freeze); acceptance=load_json(args.user_acceptance_capsule); auth=load_json(args.user_authorization); validate_completion_pointer(load_json(args.pointer), freeze, acceptance, auth)
    except (JoyflowError, OSError, json.JSONDecodeError) as exc:
        print(f'JOYFLOW_BLOCK: {exc}', file=sys.stderr); return 2
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
