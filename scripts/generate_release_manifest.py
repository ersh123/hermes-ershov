1|from __future__ import annotations
2|
3|import argparse
4|import datetime as dt
5|import hashlib
6|import json
7|import os
8|from pathlib import Path
9|import subprocess
10|import tomllib
11|from typing import Any
12|
13|
14|REPO_URL = "https://github.com/ersh123/self-ershov-memory"
15|TOOL_NAME = "self-ershov-memory-release-manifest"
16|MANIFEST_NAME = "release-manifest.json"
17|SBOM_NAME = "self-ershov-memory-sbom.spdx.json"
18|CHECKSUM_MANIFEST = "SHA256SUMS"
19|
20|
21|def _load_toml(path: Path) -> dict[str, Any]:
22|    return tomllib.loads(path.read_text(encoding="utf-8"))
23|
24|
25|def _created_timestamp() -> str:
26|    epoch = os.environ.get("SOURCE_DATE_EPOCH")
27|    if epoch:
28|        created = dt.datetime.fromtimestamp(int(epoch), tz=dt.UTC)
29|    else:
30|        created = dt.datetime.now(tz=dt.UTC)
31|    return created.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
32|
33|
34|def _sha256(path: Path) -> str:
35|    digest = hashlib.sha256()
36|    with path.open("rb") as handle:
37|        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
38|            digest.update(chunk)
39|    return digest.hexdigest()
40|
41|
42|def _normalized_distribution_name(name: str) -> str:
43|    return name.replace("-", "_").replace(".", "_")
44|
45|
46|def _single_file(dist_dir: Path, pattern: str, label: str) -> Path:
47|    matches = sorted(dist_dir.glob(pattern))
48|    if len(matches) != 1:
49|        names = ", ".join(path.name for path in matches) or "none"
50|        raise ValueError(f"expected exactly one {label} matching {pattern}, found {len(matches)}: {names}")
51|    if matches[0].stat().st_size <= 0:
52|        raise ValueError(f"{label} is empty: {matches[0]}")
53|    return matches[0]
54|
55|
56|def _git_value(args: list[str]) -> str | None:
57|    try:
58|        result = subprocess.run(
59|            ["git", *args],
60|            check=True,
61|            stdout=subprocess.PIPE,
62|            stderr=subprocess.DEVNULL,
63|            text=True,
64|        )
65|    except (OSError, subprocess.CalledProcessError):
66|        return None
67|    value = result.stdout.strip()
68|    return value or None
69|
70|
71|def _source_commit(explicit: str | None) -> str:
72|    return explicit or os.environ.get("GITHUB_SHA") or _git_value(["rev-parse", "HEAD"]) or "unknown"
73|
74|
75|def _source_ref(explicit: str | None) -> str:
76|    return (
77|        explicit
78|        or os.environ.get("GITHUB_REF_NAME")
79|        or _git_value(["rev-parse", "--abbrev-ref", "HEAD"])
80|        or "unknown"
81|    )
82|
83|
84|def _subject(path: Path, *, kind: str) -> dict[str, Any]:
85|    return {
86|        "name": path.name,
87|        "kind": kind,
88|        "digest": {"sha256": _sha256(path)},
89|        "size": path.stat().st_size,
90|    }
91|
92|
93|def build_release_manifest(
94|    *,
95|    dist_dir: Path,
96|    pyproject_path: Path,
97|    manifest_name: str = MANIFEST_NAME,
98|    created: str | None = None,
99|    commit: str | None = None,
100|    ref: str | None = None,
101|    github_run_id: str | None = None,
102|    github_run_attempt: str | None = None,
103|    github_workflow: str | None = None,
104|) -> dict[str, Any]:
105|    project = _load_toml(pyproject_path)["project"]
106|    project_name = str(project["name"])
107|    project_version = str(project["version"])
108|    normalized_name = _normalized_distribution_name(project_name)
109|
110|    wheel = _single_file(dist_dir, f"{normalized_name}-{project_version}-*.whl", "wheel")
111|    sdist = _single_file(dist_dir, f"{normalized_name}-{project_version}.tar.gz", "sdist")
112|    sbom = _single_file(dist_dir, SBOM_NAME, "SPDX SBOM")
113|    subjects = [
114|        _subject(wheel, kind="wheel"),
115|        _subject(sdist, kind="sdist"),
116|        _subject(sbom, kind="spdx-sbom"),
117|    ]
118|
119|    return {
120|        "schema_version": 1,
121|        "created_at": created or _created_timestamp(),
122|        "generator": TOOL_NAME,
123|        "project": {
124|            "name": project_name,
125|            "version": project_version,
126|        },
127|        "source": {
128|            "repository": REPO_URL,
129|            "ref": _source_ref(ref),
130|            "commit": _source_commit(commit),
131|        },
132|        "build": {
133|            "workflow": github_workflow or os.environ.get("GITHUB_WORKFLOW") or "unknown",
134|            "run_id": github_run_id or os.environ.get("GITHUB_RUN_ID") or "unknown",
135|            "run_attempt": github_run_attempt or os.environ.get("GITHUB_RUN_ATTEMPT") or "unknown",
136|        },
137|        "subjects": subjects,
138|        "sbom": {
139|            "name": SBOM_NAME,
140|        },
141|        "checksum_manifest": {
142|            "name": CHECKSUM_MANIFEST,
143|            "generated_after_manifest": True,
144|            "covers": sorted([manifest_name, *(subject["name"] for subject in subjects)]),
145|        },
146|    }
147|
148|
149|def main() -> int:
150|    parser = argparse.ArgumentParser(description="Generate the Self Ershov Memory release manifest.")
151|    parser.add_argument("--dist", type=Path, default=Path("dist"))
152|    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
153|    parser.add_argument("--output", type=Path, default=None)
154|    parser.add_argument("--commit", default=None)
155|    parser.add_argument("--ref", default=None)
156|    args = parser.parse_args()
157|
158|    output = args.output or (args.dist / MANIFEST_NAME)
159|    manifest = build_release_manifest(
160|        dist_dir=args.dist,
161|        pyproject_path=args.pyproject,
162|        manifest_name=output.name,
163|        commit=args.commit,
164|        ref=args.ref,
165|    )
166|    output.parent.mkdir(parents=True, exist_ok=True)
167|    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
168|    print(f"wrote release manifest: {output}")
169|    return 0
170|
171|
172|if __name__ == "__main__":
173|    raise SystemExit(main())
174|