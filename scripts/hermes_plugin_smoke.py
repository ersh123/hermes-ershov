1|from __future__ import annotations
2|
3|import argparse
4|import contextlib
5|import importlib.util
6|import io
7|import json
8|import os
9|from pathlib import Path
10|import sqlite3
11|import tempfile
12|
13|
14|ROOT = Path(__file__).resolve().parents[1]
15|
16|
17|class DummyHermesContext:
18|    def __init__(self) -> None:
19|        self.cli_commands: dict[str, dict] = {}
20|        self.skills: list[tuple[str, Path]] = []
21|
22|    def register_cli_command(self, **kwargs) -> None:
23|        self.cli_commands[kwargs["name"]] = kwargs
24|
25|    def register_skill(self, bare_name: str, skill_path: Path) -> None:
26|        self.skills.append((bare_name, Path(skill_path)))
27|
28|
29|def _load_root_plugin():
30|    spec = importlib.util.spec_from_file_location("self_ershov_memory_root_plugin_smoke", ROOT / "__init__.py")
31|    if spec is None or spec.loader is None:
32|        raise RuntimeError("could not load root plugin module")
33|    module = importlib.util.module_from_spec(spec)
34|    spec.loader.exec_module(module)
35|    return module
36|
37|
38|def _write_session_db(db_path: Path) -> None:
39|    conn = sqlite3.connect(db_path)
40|    try:
41|        conn.executescript(
42|            """
43|            CREATE TABLE sessions (
44|                id TEXT PRIMARY KEY,
45|                title TEXT,
46|                started_at REAL,
47|                message_count INTEGER,
48|                source TEXT,
49|                parent_session_id TEXT,
50|                end_reason TEXT
51|            );
52|            CREATE TABLE messages (
53|                id INTEGER PRIMARY KEY AUTOINCREMENT,
54|                session_id TEXT NOT NULL,
55|                role TEXT NOT NULL,
56|                content TEXT,
57|                timestamp REAL NOT NULL
58|            );
59|            """
60|        )
61|        conn.execute(
62|            "INSERT INTO sessions (id, title, started_at, message_count, source, parent_session_id, end_reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
63|            ("smoke-1", "Plugin smoke", 2_000.0, 1, "cli", None, None),
64|        )
65|        conn.execute(
66|            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
67|            (
68|                "smoke-1",
69|                "user",
70|                "MEMORY: memory: Keep Self Ershov Memory plugin smoke gates strict.",
71|                2_000.0,
72|            ),
73|        )
74|        conn.commit()
75|    finally:
76|        conn.close()
77|
78|
79|def _assert_bad_command_exits(handler) -> None:
80|    stdout = io.StringIO()
81|    stderr = io.StringIO()
82|    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
83|        try:
84|            handler(argparse.Namespace(dreaming_args=["__definitely_unknown__"]))
85|        except SystemExit as exc:
86|            if exc.code == 2:
87|                return
88|            raise AssertionError(f"bad command raised exit {exc.code!r}, expected 2") from exc
89|    raise AssertionError("bad command returned success instead of raising SystemExit(2)")
90|
91|
92|def _assert_nightly_stages_proposal(handler) -> None:
93|    old_env = os.environ.get("HERMES_ERSHOV_SESSION_DB")
94|    with tempfile.TemporaryDirectory(prefix="self-ershov-memory-plugin-smoke-") as raw_tmp:
95|        tmp = Path(raw_tmp)
96|        db_path = tmp / "state.db"
97|        live_root = tmp / "live"
98|        artifact_root = tmp / "artifacts"
99|        archive_root = tmp / "archive"
100|        state_root = tmp / "state"
101|        for path in (live_root, artifact_root, archive_root, state_root):
102|            path.mkdir(parents=True, exist_ok=True)
103|        (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")
104|        (live_root / "user.md").write_text("# USER\n", encoding="utf-8")
105|        _write_session_db(db_path)
106|
107|        os.environ["HERMES_ERSHOV_SESSION_DB"] = str(db_path)
108|        code: int | None = None
109|        try:
110|            stdout = io.StringIO()
111|            stderr = io.StringIO()
112|            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
113|                try:
114|                    code = handler(
115|                        argparse.Namespace(
116|                            dreaming_args=[
117|                                "nightly",
118|                                "--no-llm",
119|                                "--live-root",
120|                                str(live_root),
121|                                "--artifact-root",
122|                                str(artifact_root),
123|                                "--archive-root",
124|                                str(archive_root),
125|                                "--state-root",
126|                                str(state_root),
127|                                "--recent",
128|                                "1",
129|                            ]
130|                        )
131|                    )
132|                except SystemExit as exc:
133|                    raise AssertionError(f"nightly smoke raised exit {exc.code!r}, expected return 0") from exc
134|        finally:
135|            if old_env is None:
136|                os.environ.pop("HERMES_ERSHOV_SESSION_DB", None)
137|            else:
138|                os.environ["HERMES_ERSHOV_SESSION_DB"] = old_env
139|
140|        if code != 0:
141|            raise AssertionError(f"nightly smoke returned {code}, expected 0")
142|
143|        manifests = list(artifact_root.glob("*/manifest.json"))
144|        if len(manifests) != 1:
145|            raise AssertionError(f"expected one staged artifact, found {len(manifests)}")
146|        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
147|        proposals = manifest.get("proposals", [])
148|        if manifest.get("status") != "staged" or len(proposals) != 1:
149|            raise AssertionError(
150|                f"expected staged artifact with one proposal, got status={manifest.get('status')!r}, proposals={len(proposals)}"
151|            )
152|
153|        ledger_path = state_root / "runs.jsonl"
154|        runs = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
155|        if not runs or runs[-1].get("success") is not True or runs[-1].get("artifact_status") != "staged":
156|            raise AssertionError("nightly smoke did not record a successful staged run")
157|
158|
159|def main() -> int:
160|    plugin = _load_root_plugin()
161|    ctx = DummyHermesContext()
162|    plugin.register(ctx)
163|
164|    required = {"ershov", "mnemos", "nightmem", "dreaming"}
165|    missing = required.difference(ctx.cli_commands)
166|    if missing:
167|        raise AssertionError(f"missing plugin CLI commands: {sorted(missing)}")
168|    if not ctx.skills:
169|        raise AssertionError("plugin did not register its skill")
170|
171|    handler = ctx.cli_commands["ershov"]["handler_fn"]
172|    _assert_bad_command_exits(handler)
173|    _assert_nightly_stages_proposal(handler)
174|
175|    print("Hermes plugin smoke: PASS")
176|    return 0
177|
178|
179|if __name__ == "__main__":
180|    raise SystemExit(main())
181|