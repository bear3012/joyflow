#!/usr/bin/env python3
from __future__ import annotations
import argparse, contextlib, hashlib, json, pathlib, re, shlex, shutil, subprocess, sys, tempfile
from typing import Any, Iterator

TOOL_NAME = "joyflow-typed-execution-evidence-runner"

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode("utf-8")

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def run(argv: list[str], *, cwd: pathlib.Path | None=None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv,cwd=str(cwd) if cwd else None,capture_output=True)

def git(repo: pathlib.Path,*args: str) -> bytes:
    proc=run(["git","-C",str(repo),*args])
    if proc.returncode!=0:
        raise RuntimeError(proc.stderr.decode("utf-8",errors="replace").strip() or "git command failed")
    return proc.stdout

def canonical_repo_id(remote: str) -> str:
    remote=remote.strip()
    for pat in (r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$",r"^https?://[^/]+/([^/]+/[^/]+?)(?:\.git)?$"):
        m=re.search(pat,remote)
        if m: return m.group(1)
    raise RuntimeError("repository origin cannot be converted to owner/repo identity")

def repo_identity(repo_arg: str) -> tuple[pathlib.Path,str,str,str]:
    repo=pathlib.Path(repo_arg).resolve()
    root=pathlib.Path(git(repo,"rev-parse","--show-toplevel").decode().strip()).resolve()
    head=git(root,"rev-parse","HEAD").decode().strip()
    remote=git(root,"config","--get","remote.origin.url").decode().strip()
    return root,canonical_repo_id(remote),head,remote

def resolve_commit(root: pathlib.Path, ref: str) -> str:
    return git(root,"rev-parse",f"{ref}^{{commit}}").decode().strip()

def require_ancestor(root: pathlib.Path, base: str, head: str) -> None:
    proc=run(["git","-C",str(root),"merge-base","--is-ancestor",base,head])
    if proc.returncode!=0:
        raise RuntimeError("approved base is not an ancestor of result head")

@contextlib.contextmanager
def detached_worktree(root: pathlib.Path, ref: str) -> Iterator[pathlib.Path]:
    commit=resolve_commit(root,ref)
    tmp=pathlib.Path(tempfile.mkdtemp(prefix="joyflow-capture-")).resolve(); added=False
    try:
        proc=run(["git","-C",str(root),"worktree","add","--detach","--force",str(tmp),commit])
        if proc.returncode!=0:
            raise RuntimeError(proc.stderr.decode("utf-8",errors="replace").strip() or "failed to create detached worktree")
        added=True
        actual=git(tmp,"rev-parse","HEAD").decode().strip()
        if actual!=commit: raise RuntimeError("detached worktree ref mismatch")
        yield tmp
    finally:
        if added: run(["git","-C",str(root),"worktree","remove","--force",str(tmp)])
        shutil.rmtree(tmp,ignore_errors=True)

def artifact_object(path_arg: str) -> tuple[pathlib.Path,dict[str,Any],bytes]:
    path=pathlib.Path(path_arg).resolve(); data=path.read_bytes(); sha=sha256_bytes(data)
    return path,{"object_type":"ARTIFACT","source_mode":"EXISTING_ARTIFACT","object_id":path.name,"ref_or_sha256":sha},data

def repository_object(repo_id: str, ref: str) -> dict[str,Any]:
    return {"object_type":"REPOSITORY","source_mode":"REPOSITORY_REF","object_id":repo_id,"ref_or_sha256":ref}

def _state_path_row(root: pathlib.Path, name: str) -> dict[str,Any]:
    rel=pathlib.PurePosixPath(name).as_posix()
    if rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts: raise RuntimeError("repository state path must be safe and relative")
    path=root/pathlib.PurePosixPath(rel)
    if path.is_symlink(): data=path.readlink().as_posix().encode("utf-8","surrogateescape"); kind="SYMLINK"
    elif path.is_file(): data=path.read_bytes(); kind="FILE"
    elif path.is_dir(): data=b""; kind="DIRECTORY"
    else: data=b""; kind="MISSING"
    return {"path":rel,"kind":kind,"bytes":len(data),"sha256":sha256_bytes(data)}

def repository_state_observation(root: pathlib.Path, phase: str, declared_ignored_paths: list[str]) -> dict[str,Any]:
    head=git(root,"rev-parse","HEAD").decode().strip()
    index=git(root,"diff","--cached","--binary","--no-ext-diff","--no-textconv")
    worktree=git(root,"diff","--binary","--no-ext-diff","--no-textconv")
    tracked=git(root,"ls-files","-s","-z")
    untracked=[_state_path_row(root,name.decode("utf-8","surrogateescape").replace("\\","/")) for name in sorted(x for x in git(root,"ls-files","--others","--exclude-standard","-z").split(b"\0") if x)]
    ignored=[_state_path_row(root,name) for name in sorted(set(declared_ignored_paths))]
    components={"head_commit":head,"index_diff_sha256":sha256_bytes(index),"worktree_diff_sha256":sha256_bytes(worktree),"tracked_source_set_sha256":sha256_bytes(tracked),"untracked_manifest_sha256":digest(untracked),"declared_ignored_coverage_sha256":digest(ignored)}
    return {"capture_phase":phase,**components,"declared_ignored_paths":sorted(set(declared_ignored_paths)),"state_fingerprint_sha256":digest(components)}

def build_capture(*,capture_id: str,capture_kind: str,command: str,exit_code: int,stdout: bytes,stderr: bytes,observed_object: dict[str,Any],observation: dict[str,Any],subject_type: str,subject_id: str) -> dict[str,Any]:
    row={"capture_id":capture_id,"tool":TOOL_NAME,"capture_kind":capture_kind,"command":command,"exit_code":exit_code,"stdout":stdout.decode("utf-8",errors="replace"),"stderr":stderr.decode("utf-8",errors="replace"),"stdout_sha256":hashlib.sha256(stdout).hexdigest(),"stderr_sha256":hashlib.sha256(stderr).hexdigest(),"observed_object":observed_object,"observation":observation,"subject_type":subject_type,"subject_id":subject_id,"capture_sha256":None}
    row["capture_sha256"]=digest({k:v for k,v in row.items() if k!="capture_sha256"})
    return row

def common(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--capture-id",required=True); sub.add_argument("--subject-type",required=True); sub.add_argument("--subject-id",required=True); sub.add_argument("--output")

def main() -> int:
    parser=argparse.ArgumentParser(description="Capture typed source facts from an exact repository ref or Artifact.")
    subs=parser.add_subparsers(dest="mode",required=True)
    p=subs.add_parser("repository-head"); common(p); p.add_argument("--repository",required=True)
    p=subs.add_parser("repository-commit"); common(p); p.add_argument("--repository",required=True); p.add_argument("--ref",required=True); p.add_argument("--role",required=True,choices=["APPROVED_INPUT","EXECUTION_RESULT"])
    p=subs.add_parser("repository-state"); common(p); p.add_argument("--repository",required=True); p.add_argument("--phase",required=True,choices=["BEFORE","AFTER"]); p.add_argument("--include-ignored-path",action="append",default=[])
    p=subs.add_parser("artifact-sha256"); common(p); p.add_argument("--artifact",required=True)
    p=subs.add_parser("repository-file"); common(p); p.add_argument("--repository",required=True); p.add_argument("--ref",required=True); p.add_argument("--path",required=True)
    p=subs.add_parser("repository-diff"); common(p); p.add_argument("--repository",required=True); p.add_argument("--base-ref",required=True); p.add_argument("--head-ref",required=True)
    p=subs.add_parser("test-command"); common(p); g=p.add_mutually_exclusive_group(required=True); g.add_argument("--repository"); g.add_argument("--artifact"); p.add_argument("--repository-ref"); p.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args(); stdout=b""; stderr=b""; exit_code=0
    if args.mode=="repository-head":
        root,repo_id,head,remote=repo_identity(args.repository); obj=repository_object(repo_id,head)
        observation={"repository_id":repo_id,"remote_url":remote,"head_sha":head}; stdout=(head+"\n").encode(); command=f"git -C {shlex.quote(str(root))} rev-parse HEAD"; kind="REPOSITORY_HEAD"
    elif args.mode=="repository-commit":
        root,repo_id,_,remote=repo_identity(args.repository); commit=resolve_commit(root,args.ref); obj=repository_object(repo_id,commit)
        observation={"repository_id":repo_id,"remote_url":remote,"commit_sha":commit,"role":args.role}; stdout=(commit+"\n").encode(); command=f"git -C {shlex.quote(str(root))} rev-parse {shlex.quote(args.ref+'^{commit}')}"; kind="REPOSITORY_COMMIT"
    elif args.mode=="repository-state":
        root,repo_id,head,_=repo_identity(args.repository); observation=repository_state_observation(root,args.phase,args.include_ignored_path); obj={"object_type":"REPOSITORY","source_mode":"EXISTING_PR_HEAD","object_id":repo_id,"ref_or_sha256":head}; stdout=canonical_bytes(observation)+b"\n"; command=f"joyflow repository-state {args.phase} {shlex.quote(str(root))}"; kind="REPOSITORY_STATE"
    elif args.mode=="artifact-sha256":
        path,obj,data=artifact_object(args.artifact); observation={"artifact_id":path.name,"artifact_path":str(path),"artifact_sha256":obj["ref_or_sha256"],"bytes":len(data)}; command=f"sha256 {shlex.quote(str(path))}"; kind="ARTIFACT_SHA256"
    elif args.mode=="repository-file":
        root,repo_id,_,_=repo_identity(args.repository); ref=resolve_commit(root,args.ref); rel=pathlib.PurePosixPath(args.path).as_posix()
        if rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts: raise RuntimeError("repository file path must be safe and relative")
        data=git(root,"show",f"{ref}:{rel}"); obj=repository_object(repo_id,ref); observation={"path":rel,"file_sha256":sha256_bytes(data),"bytes":len(data)}; stdout=data; command=f"git -C {shlex.quote(str(root))} show {shlex.quote(ref+':'+rel)}"; kind="REPOSITORY_FILE"
    elif args.mode=="repository-diff":
        root,repo_id,_,_=repo_identity(args.repository); base=resolve_commit(root,args.base_ref); head=resolve_commit(root,args.head_ref); require_ancestor(root,base,head)
        diff=git(root,"diff","--binary",base,head); names=sorted(x for x in git(root,"diff","--name-only",base,head).decode("utf-8",errors="strict").splitlines() if x)
        obj=repository_object(repo_id,head); observation={"base_ref":base,"head_ref":head,"changed_paths":names,"diff_sha256":sha256_bytes(diff)}; stdout=diff; command=f"git -C {shlex.quote(str(root))} diff --binary {shlex.quote(base)} {shlex.quote(head)}"; kind="REPOSITORY_DIFF"
    else:
        cmd=args.command
        if cmd and cmd[0]=="--": cmd=cmd[1:]
        if not cmd: parser.error("test-command requires a command after --")
        if args.repository:
            if not args.repository_ref: parser.error("repository test-command requires --repository-ref")
            root,repo_id,_,_=repo_identity(args.repository); ref=resolve_commit(root,args.repository_ref); obj=repository_object(repo_id,ref)
            with detached_worktree(root,ref) as cwd:
                proc=run(cmd,cwd=cwd)
            observation={"argv":cmd,"cwd_scope":"SOURCE_ROOT","target_ref":ref}
        else:
            if args.repository_ref: parser.error("Artifact test-command does not accept --repository-ref")
            artifact,obj,_=artifact_object(args.artifact); cwd=artifact.parent; proc=run(cmd,cwd=cwd); observation={"argv":cmd,"cwd_scope":"SOURCE_ROOT","target_ref":obj["ref_or_sha256"]}
        stdout,stderr,exit_code=proc.stdout,proc.stderr,proc.returncode; command=shlex.join(cmd); kind="TEST_COMMAND"
    row=build_capture(capture_id=args.capture_id,capture_kind=kind,command=command,exit_code=exit_code,stdout=stdout,stderr=stderr,observed_object=obj,observation=observation,subject_type=args.subject_type,subject_id=args.subject_id)
    text=json.dumps(row,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if args.output: pathlib.Path(args.output).write_text(text,encoding="utf-8",newline="\n")
    else: sys.stdout.write(text)
    return exit_code

if __name__=="__main__":
    try: raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc),file=sys.stderr); raise SystemExit(2)
