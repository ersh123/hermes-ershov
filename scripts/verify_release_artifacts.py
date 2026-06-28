1|from __future__ import annotations
2|
3|import argparse
4|from email.parser import Parser
5|import hashlib
6|import json
7|from pathlib import Path
8|import sys
9|import tarfile
10|import tomllib
11|from typing import Any
12|import zipfile
13|
14|
15|EXPECTED_CONSOLE_SCRIPTS = {
16|    "ershov": "hermes_dreaming.cli:main",
17|    "mnemos": "hermes_dreaming.cli:main",
18|    "nightmem": "hermes_dreaming.cli:main",
19|    "dreaming": "hermes_dreaming.cli:main",
20|}
21|SBOM_NAME = "self-ershov-memory-sbom.spdx.json"
22|CHECKSUM_MANIFEST = "SHA256SUMS"
23|RELEASE_MANIFEST = "release-manifest.json"
24|REPO_URL = "https://github.com/ersh123/self-ershov-memory"
25|
26|
27|class VerificationError(Exception):
28|    pass
29|
30|
31|def _load_toml(path: Path) -> dict[str, Any]:
32|    return tomllib.loads(path.read_text(encoding="utf-8"))
33|
34|
35|def _project_metadata(pyproject_path: Path) -> tuple[str, str]:
36|    project = _load_toml(pyproject_path)["project"]
37|    return str(project["name"]), str(project["version"])
38|
39|
40|def _normalized_distribution_name(name: str) -> str:
41|    return name.replace("-", "_").replace(".", "_")
42|
43|
44|def _single_file(dist_dir: Path, pattern: str, label: str) -> Path:
45|    matches = sorted(dist_dir.glob(pattern))
46|    if len(matches) != 1:
47|        names = ", ".join(path.name for path in matches) or "none"
48|        raise VerificationError(f"expected exactly one {label} matching {pattern}, found {len(matches)}: {names}")
49|    if matches[0].stat().st_size <= 0:
50|        raise VerificationError(f"{label} is empty: {matches[0]}")
51|    return matches[0]
52|
53|
54|def _sha256(path: Path) -> str:
55|    digest = hashlib.sha256()
56|    with path.open("rb") as handle:
57|        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
58|            digest.update(chunk)
59|    return digest.hexdigest()
60|
61|
62|def _read_checksum_manifest(path: Path) -> dict[str, str]:
63|    entries: dict[str, str] = {}
64|    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
65|        if not line.strip():
66|            continue
67|        parts = line.split()
68|        if len(parts) != 2:
69|            raise VerificationError(f"{path.name}:{line_number} must contain '<sha256>  <filename>'")
70|        digest, filename = parts
71|        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
72|            raise VerificationError(f"{path.name}:{line_number} has invalid SHA256 digest")
73|        if "/" in filename or "\\" in filename or filename in {".", ".."}:
74|            raise VerificationError(f"{path.name}:{line_number} has unsafe filename {filename!r}")
75|        if filename in entries:
76|            raise VerificationError(f"{path.name}:{line_number} duplicates {filename!r}")
77|        entries[filename] = digest
78|    if not entries:
79|        raise VerificationError(f"{path.name} is empty")
80|    return entries
81|
82|
83|def _assert_safe_release_filename(filename: str, *, label: str) -> None:
84|    if "/" in filename or "\\" in filename or filename in {".", ".."}:
85|        raise VerificationError(f"{label} has unsafe filename {filename!r}")
86|
87|
88|def _assert_sha256(value: Any, *, label: str) -> str:
89|    digest = str(value)
90|    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
91|        raise VerificationError(f"{label} has invalid SHA256 digest")
92|    return digest
93|
94|
95|def _read_zip_text(zip_path: Path, suffix: str) -> str:
96|    with zipfile.ZipFile(zip_path) as archive:
97|        matches = [name for name in archive.namelist() if name.endswith(suffix)]
98|        if len(matches) != 1:
99|            raise VerificationError(f"{zip_path.name} expected one {suffix}, found {len(matches)}")
100|        return archive.read(matches[0]).decode("utf-8")
101|
102|
103|def _assert_wheel(wheel_path: Path, *, project_name: str, project_version: str) -> None:
104|    expected_prefix = f"{_normalized_distribution_name(project_name)}-{project_version}"
105|    if not wheel_path.name.startswith(expected_prefix) or not wheel_path.name.endswith("-py3-none-any.whl"):
106|        raise VerificationError(f"unexpected wheel filename: {wheel_path.name}")
107|
108|    metadata = Parser().parsestr(_read_zip_text(wheel_path, "/METADATA"))
109|    if metadata.get("Name") != project_name:
110|        raise VerificationError(f"wheel METADATA Name mismatch: {metadata.get('Name')!r}")
111|    if metadata.get("Version") != project_version:
112|        raise VerificationError(f"wheel METADATA Version mismatch: {metadata.get('Version')!r}")
113|
114|    entry_points = _read_zip_text(wheel_path, "/entry_points.txt")
115|    for name, target in EXPECTED_CONSOLE_SCRIPTS.items():
116|        expected_line = f"{name} = {target}"
117|        if expected_line not in entry_points:
118|            raise VerificationError(f"wheel entry_points.txt missing {expected_line!r}")
119|
120|    with zipfile.ZipFile(wheel_path) as archive:
121|        names = set(archive.namelist())
122|    for suffix in (
123|        "/RECORD",
124|        "hermes_dreaming/cli.py",
125|        "self_ershov_memory/__main__.py",
126|        "hermes_mnemos/__main__.py",
127|    ):
128|        if not any(name.endswith(suffix) for name in names):
129|            raise VerificationError(f"wheel missing {suffix}")
130|
131|
132|def _read_tar_text(tar_path: Path, suffix: str) -> str:
133|    with tarfile.open(tar_path, "r:gz") as archive:
134|        matches = [member for member in archive.getmembers() if member.name.endswith(suffix)]
135|        if len(matches) != 1:
136|            raise VerificationError(f"{tar_path.name} expected one {suffix}, found {len(matches)}")
137|        extracted = archive.extractfile(matches[0])
138|        if extracted is None:
139|            raise VerificationError(f"{tar_path.name} could not read {suffix}")
140|        return extracted.read().decode("utf-8")
141|
142|
143|def _assert_sdist(sdist_path: Path, *, project_name: str, project_version: str) -> None:
144|    expected_name = f"{_normalized_distribution_name(project_name)}-{project_version}.tar.gz"
145|    if sdist_path.name != expected_name:
146|        raise VerificationError(f"unexpected sdist filename: {sdist_path.name}")
147|
148|    metadata = Parser().parsestr(_read_tar_text(sdist_path, "/PKG-INFO"))
149|    if metadata.get("Name") != project_name:
150|        raise VerificationError(f"sdist PKG-INFO Name mismatch: {metadata.get('Name')!r}")
151|    if metadata.get("Version") != project_version:
152|        raise VerificationError(f"sdist PKG-INFO Version mismatch: {metadata.get('Version')!r}")
153|
154|    pyproject = _read_tar_text(sdist_path, "/pyproject.toml")
155|    if f'name = "{project_name}"' not in pyproject:
156|        raise VerificationError("sdist pyproject.toml does not carry the expected project name")
157|
158|    with tarfile.open(sdist_path, "r:gz") as archive:
159|        names = set(archive.getnames())
160|    for suffix in (
161|        "/src/hermes_dreaming/cli.py",
162|        "/src/self_ershov_memory/__main__.py",
163|        "/src/hermes_mnemos/__main__.py",
164|    ):
165|        if not any(name.endswith(suffix) for name in names):
166|            raise VerificationError(f"sdist missing {suffix}")
167|
168|
169|def _purl(name: str, version: str) -> str:
170|    return f"pkg:pypi/{name.lower().replace('_', '-')}@{version}"
171|
172|
173|def _lock_hash(package: dict[str, Any]) -> str | None:
174|    sdist = package.get("sdist")
175|    if isinstance(sdist, dict) and isinstance(sdist.get("hash"), str):
176|        return sdist["hash"]
177|    wheels = package.get("wheels")
178|    if isinstance(wheels, list):
179|        for wheel in wheels:
180|            if isinstance(wheel, dict) and isinstance(wheel.get("hash"), str):
181|                return wheel["hash"]
182|    return None
183|
184|
185|def _locked_packages(lock_path: Path) -> dict[tuple[str, str], str | None]:
186|    lock = _load_toml(lock_path)
187|    packages: dict[tuple[str, str], str | None] = {}
188|    for package in lock.get("package", []):
189|        source = package.get("source")
190|        if isinstance(source, dict) and source.get("editable") == ".":
191|            continue
192|        name = str(package["name"])
193|        version = str(package["version"])
194|        packages[(name, version)] = _lock_hash(package)
195|    return packages
196|
197|
198|def _external_ref_locators(package: dict[str, Any]) -> set[str]:
199|    refs = package.get("externalRefs")
200|    if not isinstance(refs, list):
201|        return set()
202|    return {
203|        str(ref.get("referenceLocator"))
204|        for ref in refs
205|        if isinstance(ref, dict)
206|        and ref.get("referenceCategory") == "PACKAGE-MANAGER"
207|        and ref.get("referenceType") == "purl"
208|    }
209|
210|
211|def _sha256_checksums(package: dict[str, Any]) -> set[str]:
212|    checksums = package.get("checksums")
213|    if not isinstance(checksums, list):
214|        return set()
215|    return {
216|        str(item.get("checksumValue"))
217|        for item in checksums
218|        if isinstance(item, dict) and item.get("algorithm") == "SHA256"
219|    }
220|
221|
222|def _assert_spdx_package_basics(package: dict[str, Any]) -> None:
223|    for field in (
224|        "name",
225|        "SPDXID",
226|        "versionInfo",
227|        "downloadLocation",
228|        "filesAnalyzed",
229|        "licenseConcluded",
230|        "licenseDeclared",
231|        "copyrightText",
232|    ):
233|        if field not in package:
234|            raise VerificationError(f"SBOM package {package.get('name', '<unknown>')!r} missing {field}")
235|
236|
237|def _assert_sbom(
238|    sbom_path: Path,
239|    *,
240|    project_name: str,
241|    project_version: str,
242|    lock_path: Path,
243|) -> None:
244|    sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
245|    if sbom.get("spdxVersion") != "SPDX-2.3":
246|        raise VerificationError(f"SBOM spdxVersion mismatch: {sbom.get('spdxVersion')!r}")
247|    if sbom.get("SPDXID") != "SPDXRef-DOCUMENT":
248|        raise VerificationError(f"SBOM SPDXID mismatch: {sbom.get('SPDXID')!r}")
249|    if sbom.get("dataLicense") != "CC0-1.0":
250|        raise VerificationError(f"SBOM dataLicense mismatch: {sbom.get('dataLicense')!r}")
251|
252|    packages = sbom.get("packages")
253|    if not isinstance(packages, list):
254|        raise VerificationError("SBOM packages must be a list")
255|    for package in packages:
256|        if not isinstance(package, dict):
257|            raise VerificationError("SBOM package entries must be objects")
258|        _assert_spdx_package_basics(package)
259|
260|    ids = [str(package["SPDXID"]) for package in packages]
261|    if len(ids) != len(set(ids)):
262|        raise VerificationError("SBOM package SPDXIDs are not unique")
263|
264|    package_by_key = {(str(package["name"]), str(package["versionInfo"])): package for package in packages}
265|    root = package_by_key.get((project_name, project_version))
266|    if root is None:
267|        raise VerificationError(f"SBOM missing root package {project_name}@{project_version}")
268|    root_id = str(root["SPDXID"])
269|    if _purl(project_name, project_version) not in _external_ref_locators(root):
270|        raise VerificationError("SBOM root package missing purl externalRef")
271|
272|    locked = _locked_packages(lock_path)
273|    expected_keys = {(project_name, project_version), *locked.keys()}
274|    if set(package_by_key) != expected_keys:
275|        missing = sorted(expected_keys - set(package_by_key))
276|        extra = sorted(set(package_by_key) - expected_keys)
277|        raise VerificationError(f"SBOM package set mismatch: missing={missing}, extra={extra}")
278|
279|    relationships = sbom.get("relationships")
280|    if not isinstance(relationships, list):
281|        raise VerificationError("SBOM relationships must be a list")
282|    relationship_keys = {
283|        (
284|            str(item.get("spdxElementId")),
285|            str(item.get("relationshipType")),
286|            str(item.get("relatedSpdxElement")),
287|        )
288|        for item in relationships
289|        if isinstance(item, dict)
290|    }
291|    if ("SPDXRef-DOCUMENT", "DESCRIBES", root_id) not in relationship_keys:
292|        raise VerificationError("SBOM missing SPDXRef-DOCUMENT DESCRIBES root relationship")
293|
294|    for key, lock_hash in locked.items():
295|        package = package_by_key[key]
296|        if _purl(*key) not in _external_ref_locators(package):
297|            raise VerificationError(f"SBOM package {key[0]}@{key[1]} missing purl externalRef")
298|        if (root_id, "DEPENDS_ON", str(package["SPDXID"])) not in relationship_keys:
299|            raise VerificationError(f"SBOM missing root DEPENDS_ON relationship for {key[0]}@{key[1]}")
300|        if lock_hash and lock_hash.startswith("sha256:"):
301|            expected_hash = lock_hash.split(":", 1)[1]
302|            if expected_hash not in _sha256_checksums(package):
303|                raise VerificationError(f"SBOM package {key[0]}@{key[1]} missing locked SHA256 checksum")
304|
305|
306|def _assert_release_manifest(
307|    manifest_path: Path,
308|    *,
309|    project_name: str,
310|    project_version: str,
311|    artifacts: dict[str, Path],
312|) -> list[str]:
313|    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
314|    if manifest.get("schema_version") != 1:
315|        raise VerificationError(f"release manifest schema_version mismatch: {manifest.get('schema_version')!r}")
316|    if manifest.get("generator") != "self-ershov-memory-release-manifest":
317|        raise VerificationError(f"release manifest generator mismatch: {manifest.get('generator')!r}")
318|
319|    project = manifest.get("project")
320|    if not isinstance(project, dict):
321|        raise VerificationError("release manifest project must be an object")
322|    if project.get("name") != project_name:
323|        raise VerificationError(f"release manifest project.name mismatch: {project.get('name')!r}")
324|    if project.get("version") != project_version:
325|        raise VerificationError(f"release manifest project.version mismatch: {project.get('version')!r}")
326|
327|    source = manifest.get("source")
328|    if not isinstance(source, dict):
329|        raise VerificationError("release manifest source must be an object")
330|    if source.get("repository") != REPO_URL:
331|        raise VerificationError(f"release manifest repository mismatch: {source.get('repository')!r}")
332|    for field in ("ref", "commit"):
333|        value = source.get(field)
334|        if not isinstance(value, str) or not value:
335|            raise VerificationError(f"release manifest source.{field} must be a non-empty string")
336|
337|    build = manifest.get("build")
338|    if not isinstance(build, dict):
339|        raise VerificationError("release manifest build must be an object")
340|    for field in ("workflow", "run_id", "run_attempt"):
341|        value = build.get(field)
342|        if not isinstance(value, str) or not value:
343|            raise VerificationError(f"release manifest build.{field} must be a non-empty string")
344|
345|    sbom = manifest.get("sbom")
346|    if not isinstance(sbom, dict) or sbom.get("name") != SBOM_NAME:
347|        raise VerificationError("release manifest sbom.name mismatch")
348|
349|    subjects = manifest.get("subjects")
350|    if not isinstance(subjects, list):
351|        raise VerificationError("release manifest subjects must be a list")
352|    expected_names = set(artifacts)
353|    seen_names: set[str] = set()
354|    expected_kinds = {
355|        "wheel": "wheel",
356|        "sdist": "sdist",
357|        SBOM_NAME: "spdx-sbom",
358|    }
359|    for subject in subjects:
360|        if not isinstance(subject, dict):
361|            raise VerificationError("release manifest subjects must contain objects")
362|        name = str(subject.get("name"))
363|        _assert_safe_release_filename(name, label="release manifest subject")
364|        if name in seen_names:
365|            raise VerificationError(f"release manifest duplicates subject {name!r}")
366|        seen_names.add(name)
367|        if name not in artifacts:
368|            raise VerificationError(f"release manifest has unexpected subject {name!r}")
369|        expected_kind = expected_kinds.get(name)
370|        if expected_kind is None and name.endswith(".whl"):
371|            expected_kind = "wheel"
372|        if expected_kind is None and name.endswith(".tar.gz"):
373|            expected_kind = "sdist"
374|        if subject.get("kind") != expected_kind:
375|            raise VerificationError(f"release manifest subject {name!r} kind mismatch: {subject.get('kind')!r}")
376|        digest = subject.get("digest")
377|        if not isinstance(digest, dict):
378|            raise VerificationError(f"release manifest subject {name!r} digest must be an object")
379|        if _assert_sha256(digest.get("sha256"), label=f"release manifest subject {name!r}") != _sha256(
380|            artifacts[name]
381|        ):
382|            raise VerificationError(f"release manifest digest mismatch for {name}")
383|        if subject.get("size") != artifacts[name].stat().st_size:
384|            raise VerificationError(f"release manifest size mismatch for {name}")
385|    if seen_names != expected_names:
386|        missing = sorted(expected_names - seen_names)
387|        extra = sorted(seen_names - expected_names)
388|        raise VerificationError(f"release manifest subject set mismatch: missing={missing}, extra={extra}")
389|
390|    checksum_manifest = manifest.get("checksum_manifest")
391|    if not isinstance(checksum_manifest, dict):
392|        raise VerificationError("release manifest checksum_manifest must be an object")
393|    if checksum_manifest.get("name") != CHECKSUM_MANIFEST:
394|        raise VerificationError("release manifest checksum_manifest.name mismatch")
395|    if checksum_manifest.get("generated_after_manifest") is not True:
396|        raise VerificationError("release manifest checksum_manifest.generated_after_manifest must be true")
397|    covers = checksum_manifest.get("covers")
398|    if not isinstance(covers, list) or any(not isinstance(item, str) for item in covers):
399|        raise VerificationError("release manifest checksum_manifest.covers must be a string list")
400|    expected_covers = sorted([manifest_path.name, *expected_names])
401|    if sorted(covers) != expected_covers:
402|        raise VerificationError(
403|            f"release manifest checksum cover set mismatch: expected={expected_covers}, actual={sorted(covers)}"
404|        )
405|
406|    return sorted(seen_names)
407|
408|
409|def verify_release_artifacts(*, dist_dir: Path, pyproject_path: Path, lock_path: Path) -> list[str]:
410|    project_name, project_version = _project_metadata(pyproject_path)
411|    normalized_name = _normalized_distribution_name(project_name)
412|
413|    wheel = _single_file(dist_dir, f"{normalized_name}-{project_version}-*.whl", "wheel")
414|    sdist = _single_file(dist_dir, f"{normalized_name}-{project_version}.tar.gz", "sdist")
415|    sbom = _single_file(dist_dir, SBOM_NAME, "SPDX SBOM")
416|    release_manifest = _single_file(dist_dir, RELEASE_MANIFEST, "release manifest")
417|    checksum_manifest = _single_file(dist_dir, CHECKSUM_MANIFEST, "checksum manifest")
418|
419|    _assert_wheel(wheel, project_name=project_name, project_version=project_version)
420|    _assert_sdist(sdist, project_name=project_name, project_version=project_version)
421|    _assert_sbom(sbom, project_name=project_name, project_version=project_version, lock_path=lock_path)
422|    manifest_subjects = _assert_release_manifest(
423|        release_manifest,
424|        project_name=project_name,
425|        project_version=project_version,
426|        artifacts={
427|            wheel.name: wheel,
428|            sdist.name: sdist,
429|            sbom.name: sbom,
430|        },
431|    )
432|
433|    expected_files = {wheel.name, sdist.name, sbom.name, release_manifest.name}
434|    checksum_entries = _read_checksum_manifest(checksum_manifest)
435|    if set(checksum_entries) != expected_files:
436|        missing = sorted(expected_files - set(checksum_entries))
437|        extra = sorted(set(checksum_entries) - expected_files)
438|        raise VerificationError(f"{CHECKSUM_MANIFEST} file set mismatch: missing={missing}, extra={extra}")
439|    for path in (wheel, sdist, sbom, release_manifest):
440|        actual = _sha256(path)
441|        if checksum_entries[path.name] != actual:
442|            raise VerificationError(f"{CHECKSUM_MANIFEST} digest mismatch for {path.name}")
443|
444|    return [
445|        f"wheel {wheel.name} sha256={_sha256(wheel)}",
446|        f"sdist {sdist.name} sha256={_sha256(sdist)}",
447|        f"sbom {sbom.name} sha256={_sha256(sbom)}",
448|        f"manifest {release_manifest.name} subjects={len(manifest_subjects)} sha256={_sha256(release_manifest)}",
449|        f"checksums {checksum_manifest.name} entries={len(checksum_entries)}",
450|    ]
451|
452|
453|def main() -> int:
454|    parser = argparse.ArgumentParser(description="Verify Self Ershov Memory release artifacts before upload/attestation.")
455|    parser.add_argument("--dist", type=Path, default=Path("dist"))
456|    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
457|    parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
458|    args = parser.parse_args()
459|
460|    try:
461|        evidence = verify_release_artifacts(dist_dir=args.dist, pyproject_path=args.pyproject, lock_path=args.lock)
462|    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, tarfile.TarError, VerificationError) as exc:
463|        print(f"release artifact verification failed: {exc}", file=sys.stderr)
464|        return 1
465|
466|    print("release artifacts verified")
467|    for line in evidence:
468|        print(f"- {line}")
469|    return 0
470|
471|
472|if __name__ == "__main__":
473|    raise SystemExit(main())
474|