1|from __future__ import annotations
2|
3|import argparse
4|import datetime as dt
5|import hashlib
6|import json
7|import os
8|import re
9|import tomllib
10|from pathlib import Path
11|from typing import Any
12|
13|
14|REPO_URL = "https://github.com/ersh123/self-ershov-memory"
15|TOOL_NAME = "self-ershov-memory-release-sbom"
16|
17|
18|def _load_toml(path: Path) -> dict[str, Any]:
19|    return tomllib.loads(path.read_text(encoding="utf-8"))
20|
21|
22|def _created_timestamp() -> str:
23|    epoch = os.environ.get("SOURCE_DATE_EPOCH")
24|    if epoch:
25|        created = dt.datetime.fromtimestamp(int(epoch), tz=dt.UTC)
26|    else:
27|        created = dt.datetime.now(tz=dt.UTC)
28|    return created.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
29|
30|
31|def _spdx_id(name: str, version: str, *, prefix: str = "Package") -> str:
32|    digest = hashlib.sha256(f"{name}@{version}".encode("utf-8")).hexdigest()[:10]
33|    safe = re.sub(r"[^A-Za-z0-9.-]+", "-", name).strip("-") or "package"
34|    return f"SPDXRef-{prefix}-{safe}-{digest}"
35|
36|
37|def _hash_from_lock_entry(package: dict[str, Any]) -> str | None:
38|    sdist = package.get("sdist")
39|    if isinstance(sdist, dict) and isinstance(sdist.get("hash"), str):
40|        return sdist["hash"]
41|    wheels = package.get("wheels")
42|    if isinstance(wheels, list):
43|        for wheel in wheels:
44|            if isinstance(wheel, dict) and isinstance(wheel.get("hash"), str):
45|                return wheel["hash"]
46|    return None
47|
48|
49|def _url_from_lock_entry(package: dict[str, Any]) -> str:
50|    sdist = package.get("sdist")
51|    if isinstance(sdist, dict) and isinstance(sdist.get("url"), str):
52|        return sdist["url"]
53|    wheels = package.get("wheels")
54|    if isinstance(wheels, list):
55|        for wheel in wheels:
56|            if isinstance(wheel, dict) and isinstance(wheel.get("url"), str):
57|                return wheel["url"]
58|    return "NOASSERTION"
59|
60|
61|def _checksum(hash_value: str | None) -> list[dict[str, str]]:
62|    if not hash_value:
63|        return []
64|    if ":" not in hash_value:
65|        return []
66|    algorithm, value = hash_value.split(":", 1)
67|    if algorithm.lower() != "sha256":
68|        return []
69|    return [{"algorithm": "SHA256", "checksumValue": value}]
70|
71|
72|def _purl(name: str, version: str) -> str:
73|    normalized = name.lower().replace("_", "-")
74|    return f"pkg:pypi/{normalized}@{version}"
75|
76|
77|def _package(
78|    *,
79|    name: str,
80|    version: str,
81|    spdx_id: str,
82|    download_location: str,
83|    license_declared: str,
84|    checksum: list[dict[str, str]] | None = None,
85|) -> dict[str, Any]:
86|    package: dict[str, Any] = {
87|        "name": name,
88|        "SPDXID": spdx_id,
89|        "versionInfo": version,
90|        "downloadLocation": download_location,
91|        "filesAnalyzed": False,
92|        "licenseConcluded": "NOASSERTION",
93|        "licenseDeclared": license_declared,
94|        "copyrightText": "NOASSERTION",
95|        "primaryPackagePurpose": "LIBRARY",
96|        "externalRefs": [
97|            {
98|                "referenceCategory": "PACKAGE-MANAGER",
99|                "referenceType": "purl",
100|                "referenceLocator": _purl(name, version),
101|            }
102|        ],
103|    }
104|    if checksum:
105|        package["checksums"] = checksum
106|    return package
107|
108|
109|def build_sbom(
110|    *,
111|    pyproject_path: Path,
112|    lock_path: Path,
113|    created: str | None = None,
114|) -> dict[str, Any]:
115|    pyproject = _load_toml(pyproject_path)
116|    lock = _load_toml(lock_path)
117|    project = pyproject["project"]
118|    project_name = str(project["name"])
119|    project_version = str(project["version"])
120|    lock_digest = hashlib.sha256(lock_path.read_bytes()).hexdigest()
121|    root_id = _spdx_id(project_name, project_version, prefix="Root")
122|
123|    packages = [
124|        _package(
125|            name=project_name,
126|            version=project_version,
127|            spdx_id=root_id,
128|            download_location=REPO_URL,
129|            license_declared="MIT",
130|        )
131|    ]
132|    relationships = [
133|        {
134|            "spdxElementId": "SPDXRef-DOCUMENT",
135|            "relationshipType": "DESCRIBES",
136|            "relatedSpdxElement": root_id,
137|        }
138|    ]
139|
140|    for package in sorted(lock.get("package", []), key=lambda item: (item.get("name", ""), item.get("version", ""))):
141|        source = package.get("source")
142|        if isinstance(source, dict) and source.get("editable") == ".":
143|            continue
144|        name = str(package["name"])
145|        version = str(package["version"])
146|        spdx_id = _spdx_id(name, version)
147|        packages.append(
148|            _package(
149|                name=name,
150|                version=version,
151|                spdx_id=spdx_id,
152|                download_location=_url_from_lock_entry(package),
153|                license_declared="NOASSERTION",
154|                checksum=_checksum(_hash_from_lock_entry(package)),
155|            )
156|        )
157|        relationships.append(
158|            {
159|                "spdxElementId": root_id,
160|                "relationshipType": "DEPENDS_ON",
161|                "relatedSpdxElement": spdx_id,
162|            }
163|        )
164|
165|    return {
166|        "spdxVersion": "SPDX-2.3",
167|        "dataLicense": "CC0-1.0",
168|        "SPDXID": "SPDXRef-DOCUMENT",
169|        "name": f"{project_name}-{project_version}-release-sbom",
170|        "documentNamespace": f"{REPO_URL}/sbom/{project_name}-{project_version}-{lock_digest[:16]}",
171|        "creationInfo": {
172|            "created": created or _created_timestamp(),
173|            "creators": [f"Tool: {TOOL_NAME}"],
174|        },
175|        "packages": packages,
176|        "relationships": relationships,
177|    }
178|
179|
180|def main() -> int:
181|    parser = argparse.ArgumentParser(description="Generate the Self Ershov Memory release SPDX SBOM.")
182|    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
183|    parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
184|    parser.add_argument("--output", type=Path, required=True)
185|    args = parser.parse_args()
186|
187|    sbom = build_sbom(pyproject_path=args.pyproject, lock_path=args.lock)
188|    args.output.parent.mkdir(parents=True, exist_ok=True)
189|    args.output.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
190|    print(f"wrote SBOM: {args.output}")
191|    return 0
192|
193|
194|if __name__ == "__main__":
195|    raise SystemExit(main())
196|