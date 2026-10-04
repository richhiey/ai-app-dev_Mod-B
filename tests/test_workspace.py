"""Filesystem contracts for editable workspace copies and portable exports."""
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from module_b import workspace
from module_b.workspace import DEFAULT_POLICY, WorkspacePolicy, export_workspace, prepare_example, restore_workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repository"
        self.repo.mkdir()
        (self.repo / "pyproject.toml").write_text(
            '[project]\nname = "ms-app-dev-module-b"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        self.example = self.repo / "examples" / "fieldcare"
        for folder in ("app", "data", "fixtures", "tests"):
            (self.example / folder).mkdir(parents=True)
        (self.example / "app/main.py").write_text("VALUE = 'starter'\n", encoding="utf-8")
        (self.example / "data/equipment.json").write_text('{"id": "example"}\n', encoding="utf-8")
        (self.example / "fixtures/request.json").write_text('{"question": "example"}\n', encoding="utf-8")
        (self.example / "tests/test_example.py").write_text("assert True\n", encoding="utf-8")
        self.destination = self.root / "work" / "fieldcare"

    def prepare(self):
        return prepare_example(destination=self.destination, repo_root=self.repo)

    def test_fresh_copy_records_origin_and_leaves_source_unchanged(self):
        result = self.prepare()
        self.assertEqual(result, self.destination.resolve())
        marker = json.loads((result / ".module-b-workspace.json").read_text())
        self.assertEqual(marker["example"], "fieldcare")
        self.assertEqual(marker["source_version"], "0.1.0")
        self.assertEqual((result / "app/main.py").read_bytes(), (self.example / "app/main.py").read_bytes())
        self.assertTrue((result / "tests/test_example.py").is_file())
        self.assertFalse((self.example / ".module-b-workspace.json").exists())

    def test_repeated_setup_preserves_edits_deletions_and_new_files(self):
        project = self.prepare()
        (project / "app/main.py").write_text("VALUE = 'learner'\n", encoding="utf-8")
        (project / "app/custom.py").write_text("# my new route\n", encoding="utf-8")
        (project / "data/equipment.json").unlink()
        (project / ".env").write_text("PRIVATE=local-only\n", encoding="utf-8")
        before = {p.relative_to(project): p.read_bytes() for p in project.rglob("*") if p.is_file()}
        # A newer packaged version must not replace any learner work either.
        (self.repo / "pyproject.toml").write_text(
            '[project]\nname = "ms-app-dev-module-b"\nversion = "0.2.0"\n', encoding="utf-8"
        )
        self.assertEqual(self.prepare(), project)
        after = {p.relative_to(project): p.read_bytes() for p in project.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertIn("starter", (self.example / "app/main.py").read_text())

    def test_unknown_existing_directory_is_not_overwritten(self):
        self.destination.mkdir(parents=True)
        important = self.destination / "my-notes.txt"
        important.write_text("keep me", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(important.read_text(), "keep me")
        self.assertEqual(list(self.destination.iterdir()), [important])

    def test_empty_directory_and_existing_file_are_collisions(self):
        self.destination.mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            self.prepare()
        file_path = self.root / "already-a-file"
        file_path.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            prepare_example(destination=file_path, repo_root=self.repo)
        self.assertEqual(file_path.read_text(), "keep")

    def test_wrong_example_marker_and_malformed_marker_are_rejected(self):
        project = self.prepare()
        marker_path = project / ".module-b-workspace.json"
        marker = json.loads(marker_path.read_text())
        marker["example"] = "something-else"
        marker_path.write_text(json.dumps(marker), encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.prepare()
        marker_path.write_text("not JSON", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_invalid_example_paths_do_not_create_a_destination(self):
        for name in ("../fieldcare", "/tmp/fieldcare", "fieldcare/other", ".", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                prepare_example(name, self.destination, repo_root=self.repo)
        self.assertFalse(self.destination.exists())

    def test_wrong_repository_identity_and_missing_example_are_rejected(self):
        (self.repo / "pyproject.toml").write_text('[project]\nname="other"\nversion="0.1.0"\n')
        with self.assertRaises(ValueError):
            self.prepare()
        (self.repo / "pyproject.toml").write_text('[project]\nname="ms-app-dev-module-b"\nversion="0.1.0"\n')
        with self.assertRaises(FileNotFoundError):
            prepare_example("missing", self.destination, repo_root=self.repo)
        self.assertFalse(self.destination.exists())

    def test_implicit_root_is_based_on_module_location_not_current_directory(self):
        fake_module = self.repo / "src/module_b/workspace.py"
        with patch.object(workspace, "__file__", str(fake_module)):
            project = prepare_example(destination=self.destination)
        self.assertTrue((project / "app/main.py").is_file())

    def test_new_destination_creates_a_separate_checkpoint(self):
        first = self.prepare()
        (first / "app/main.py").write_text("EDITED = True\n", encoding="utf-8")
        second = prepare_example(destination=self.root / "another-checkpoint", repo_root=self.repo)
        self.assertIn("starter", (second / "app/main.py").read_text())
        self.assertEqual((first / "app/main.py").read_text(), "EDITED = True\n")

    def test_symbolic_link_inputs_are_rejected(self):
        outside = self.root / "outside.py"
        outside.write_text("PRIVATE = True\n", encoding="utf-8")
        (self.example / "app/link.py").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.destination.exists())
        (self.example / "app/link.py").unlink()
        self.destination.parent.mkdir(parents=True)
        self.destination.symlink_to(self.example, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_export_preserves_allowed_edits_and_excludes_other_files(self):
        project = self.prepare()
        (project / "app/main.py").write_text("VALUE = 'edited'\n", encoding="utf-8")
        (project / "app/nested").mkdir()
        (project / "app/nested/extra.py").write_text("# learner code\n", encoding="utf-8")
        (project / "trace-record.md").write_text("My trace\n", encoding="utf-8")
        (project / ".env").write_text("SECRET=not-for-export\n", encoding="utf-8")
        for folder in (".git", ".venv", "app/.venv", "app/__pycache__"):
            (project / folder).mkdir(parents=True, exist_ok=True)
            (project / folder / "private.py").write_text("# exclude\n", encoding="utf-8")
        output = export_workspace(project, self.root / "exports" / "work.zip")
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(set(archive.namelist()), {
                "app/main.py", "app/nested/extra.py", "data/equipment.json",
                "fixtures/request.json", "trace-record.md",
                ".module-b-workspace.json",
            })
            self.assertEqual(archive.read("app/main.py"), b"VALUE = 'edited'\n")
            self.assertEqual(archive.read("trace-record.md"), b"My trace\n")

    def test_export_refuses_to_overwrite_existing_output(self):
        project = self.prepare()
        output = self.root / "existing.zip"
        output.write_bytes(b"original bytes")
        with self.assertRaises(FileExistsError):
            export_workspace(project, output)
        self.assertEqual(output.read_bytes(), b"original bytes")

    def test_export_skips_symlink_files_and_directories_in_allowlist(self):
        project = self.prepare()
        outside = self.root / "private"
        outside.mkdir()
        (outside / "secret.py").write_text("SECRET = 'keep local'\n", encoding="utf-8")
        (outside / "secret.json").write_text('{"secret":"keep local"}', encoding="utf-8")
        (project / "app/leaked.py").symlink_to(outside / "secret.py")
        (project / "app/external").symlink_to(outside, target_is_directory=True)
        (project / "fixtures/leaked.json").symlink_to(outside / "secret.json")
        (project / "trace-record.md").symlink_to(outside / "secret.py")
        (project / "app/dangling.py").symlink_to(outside / "missing.py")
        output = export_workspace(project, self.root / "safe.zip")
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(set(archive.namelist()), {"app/main.py", "data/equipment.json", "fixtures/request.json", ".module-b-workspace.json"})

    def test_export_rejects_symbolic_link_workspace_and_output(self):
        project = self.prepare()
        alias = self.root / "workspace-alias"
        alias.symlink_to(project, target_is_directory=True)
        with self.assertRaises(ValueError):
            export_workspace(alias, self.root / "alias.zip")
        output = self.root / "output.zip"
        output.symlink_to(self.root / "missing.zip")
        with self.assertRaises(FileExistsError):
            export_workspace(project, output)

    def test_export_restore_roundtrip_retains_edits_and_setup_reuses_them(self):
        project = self.prepare()
        (project / "app/main.py").write_text("VALUE = 'my saved work'\n", encoding="utf-8")
        (project / "fixtures/request.json").unlink()
        (project / "trace-record.md").write_text("I traced the route.\n", encoding="utf-8")
        exported = export_workspace(project, self.root / "my-work.zip")
        restored = restore_workspace(exported, self.root / "restored")
        self.assertEqual((restored / "app/main.py").read_bytes(), (project / "app/main.py").read_bytes())
        self.assertFalse((restored / "fixtures/request.json").exists())
        self.assertEqual((restored / "trace-record.md").read_text(), "I traced the route.\n")
        before = {p.relative_to(restored): p.read_bytes() for p in restored.rglob("*") if p.is_file()}
        self.assertEqual(prepare_example(destination=restored, repo_root=self.repo), restored)
        after = {p.relative_to(restored): p.read_bytes() for p in restored.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_export_canonicalizes_manifest_without_copying_extra_metadata(self):
        project = self.prepare()
        marker_path = project / ".module-b-workspace.json"
        marker = json.loads(marker_path.read_text())
        marker["private_note"] = "do not export this"
        marker_path.write_text(json.dumps(marker), encoding="utf-8")
        exported = export_workspace(project, self.root / "canonical.zip")
        with zipfile.ZipFile(exported) as package:
            saved = json.loads(package.read(".module-b-workspace.json"))
        self.assertEqual(set(saved), {"schema_version", "source_project", "source_version", "example"})
        self.assertIn("private_note", json.loads(marker_path.read_text()))

    def test_export_rejects_invalid_marker_before_writing_output(self):
        project = self.prepare()
        (project / ".module-b-workspace.json").write_text("{}", encoding="utf-8")
        output = self.root / "invalid-manifest.zip"
        with self.assertRaises(FileExistsError):
            export_workspace(project, output)
        self.assertFalse(output.exists())

    def test_unmarked_export_has_no_manifest_and_is_not_restorable(self):
        exported = export_workspace(self.example, self.root / "unmarked.zip")
        with zipfile.ZipFile(exported) as package:
            self.assertNotIn(".module-b-workspace.json", package.namelist())
        target = self.root / "unmarked-restored"
        with self.assertRaises(ValueError):
            restore_workspace(exported, target)
        self.assertFalse(target.exists())

    def test_restore_refuses_existing_directory_file_and_symlink(self):
        exported = export_workspace(self.prepare(), self.root / "valid.zip")
        existing_directory = self.root / "existing-directory"
        existing_directory.mkdir()
        existing_file = self.root / "existing-file"
        existing_file.write_text("preserve", encoding="utf-8")
        alias = self.root / "existing-link"
        alias.symlink_to(self.root / "missing")
        for target in (existing_directory, existing_file, alias):
            with self.subTest(target=target), self.assertRaises(FileExistsError):
                restore_workspace(exported, target)
        self.assertEqual(existing_file.read_text(), "preserve")
        self.assertEqual(list(existing_directory.iterdir()), [])

    def test_restore_rejects_unsafe_members_before_creating_destination(self):
        marker = (self.prepare() / ".module-b-workspace.json").read_bytes()
        invalid_names = (
            "../escape.py", "/absolute.py", "app/../../escape.py", "app\\escape.py",
            "app/C:stream.py", "app/.venv/private.py", ".env", "tests/test_source.py",
            "app//empty.py", "app/./dot.py",
        )
        for index, name in enumerate(invalid_names):
            with self.subTest(name=name):
                archive = self.root / f"unsafe-{index}.zip"
                with zipfile.ZipFile(archive, "w") as package:
                    package.writestr(".module-b-workspace.json", marker)
                    package.writestr("app/main.py", "# innocent first file\n")
                    package.writestr(name, "# unsafe path\n")
                target = self.root / f"unsafe-{index}"
                with self.assertRaises(ValueError):
                    restore_workspace(archive, target)
                self.assertFalse(target.exists())

    def test_restore_rejects_symlink_and_oversize_archive(self):
        marker = (self.prepare() / ".module-b-workspace.json").read_bytes()
        archive = self.root / "linked.zip"
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(".module-b-workspace.json", marker)
            link = zipfile.ZipInfo("app/link.py")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            package.writestr(link, "../../outside.py")
        target = self.root / "linked"
        with self.assertRaises(ValueError):
            restore_workspace(archive, target)
        self.assertFalse(target.exists())
        oversized = self.root / "oversized.zip"
        with zipfile.ZipFile(oversized, "w", compression=zipfile.ZIP_DEFLATED) as package:
            package.writestr(".module-b-workspace.json", marker)
            package.writestr("app/big.py", b"x" * (20 * 1024 * 1024))
        target = self.root / "oversized"
        with self.assertRaises(ValueError):
            restore_workspace(oversized, target)
        self.assertFalse(target.exists())

    def test_restore_rejects_bad_zip_invalid_manifest_and_file_directory_collision(self):
        archive = self.root / "not-a-zip.zip"
        archive.write_bytes(b"invalid zip")
        target = self.root / "bad-zip"
        with self.assertRaises(ValueError):
            restore_workspace(archive, target)
        self.assertFalse(target.exists())
        invalid_manifest = self.root / "invalid-manifest.zip"
        with zipfile.ZipFile(invalid_manifest, "w") as package:
            package.writestr(".module-b-workspace.json", '{"source_project": "another-project"}')
            package.writestr("app/main.py", "# valid Python path\n")
        with self.assertRaises(ValueError):
            restore_workspace(invalid_manifest, target)
        self.assertFalse(target.exists())
        marker = (self.prepare() / ".module-b-workspace.json").read_bytes()
        collision = self.root / "collision.zip"
        with zipfile.ZipFile(collision, "w") as package:
            package.writestr(".module-b-workspace.json", marker)
            package.writestr("app/parent.py", "# file\n")
            package.writestr("app/parent.py/child.py", "# conflicts with parent file\n")
        with self.assertRaises(ValueError):
            restore_workspace(collision, target)
        self.assertFalse(target.exists())

    def test_explicit_policy_roundtrip_for_second_example_components(self):
        example = self.repo / "examples" / "support-dashboard"
        contents = {
            "src/support/main.py": "def answer():\n    return 'learner edit'\n",
            "web/src/App.tsx": "export const App = () => <main>Support</main>;\n",
            "web/client.ts": "export const version = 2;\n",
            "web/events.js": "export const events = [];\n",
            "web/styles.css": "main { color: blue; }\n",
            "web/index.html": "<main>Support</main>\n",
            "events/requests.jsonl": '{"request_id":"synthetic-1"}\n',
            "package.json": '{"name":"support-dashboard"}\n',
            "README.md": "My saved component notes\n",
        }
        for name, content in contents.items():
            path = example / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        project = prepare_example("support-dashboard", self.root / "dashboard", repo_root=self.repo)
        policy = WorkspacePolicy(
            directory_suffixes={"src": (".py",), "web": (".ts", ".tsx", ".js", ".css", ".html"), "events": (".jsonl",)},
            root_files=("package.json", "README.md"),
        )
        archive = export_workspace(project, self.root / "dashboard.zip", policy=policy)
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(set(package.namelist()), {*contents, ".module-b-workspace.json"})
        rejected = self.root / "default-rejected"
        with self.assertRaises(ValueError):
            restore_workspace(archive, rejected)
        self.assertFalse(rejected.exists())
        restored = restore_workspace(archive, self.root / "dashboard-restored", policy=policy)
        for name, content in contents.items():
            self.assertEqual((restored / name).read_text(), content)
        self.assertEqual(prepare_example("support-dashboard", restored, repo_root=self.repo), restored)

    def test_policy_is_immutable_and_defensively_copies_inputs(self):
        suffixes = [".py"]
        directories = {"src": suffixes}
        roots = ["README.md"]
        policy = WorkspacePolicy(directories, roots)
        suffixes.append(".pem")
        directories["private"] = (".json",)
        roots.append("unrequested.json")
        self.assertEqual(dict(policy.directory_suffixes), {"src": frozenset({".py"})})
        self.assertEqual(policy.root_files, frozenset({"README.md"}))
        with self.assertRaises(TypeError):
            policy.directory_suffixes["other"] = (".py",)
        with self.assertRaises(FrozenInstanceError):
            policy.root_files = frozenset({"changed.txt"})
        self.assertEqual(dict(DEFAULT_POLICY.directory_suffixes), {
            "app": frozenset({".py"}), "data": frozenset({".json"}), "fixtures": frozenset({".json"}),
        })

    def test_policy_rejects_traversal_wildcards_and_ambiguous_extensions(self):
        for directory in ("../src", "/src", "src/../web", "src\\web", "src/*", ".venv", ""):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                WorkspacePolicy({directory: (".py",)})
        for suffixes in (("*",), ("py",), (".py/other",), (), ".py"):
            with self.subTest(suffixes=suffixes), self.assertRaises(ValueError):
                WorkspacePolicy({"src": suffixes})
        for name in ("../README.md", "/README.md", "web/index.html", "*.json", ".module-b-workspace.json"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                WorkspacePolicy(root_files=(name,))

    def test_private_files_remain_excluded_under_broad_explicit_policy(self):
        project = self.prepare()
        contents = {
            "web/nested/visible.json": '{}\n',
            "web/nested/.env.json": '{"secret":"synthetic"}\n',
            "web/nested/certificate.pem": "synthetic private key\n",
            "web/.env.local": "PRIVATE=synthetic\n",
            "web/node_modules/vendor/client.js": "// dependency\n",
            "web/.cache/compiled.js": "// cache\n",
            ".env.example": "EXAMPLE_VALUE=\n",
            ".env": "PRIVATE=synthetic\n",
            "root.pem": "synthetic private key\n",
        }
        for name, content in contents.items():
            path = project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        policy = WorkspacePolicy(
            {"web": (".json", ".pem", ".local", ".js")},
            root_files=(".env.example", ".env", "root.pem"),
        )
        archive = export_workspace(project, self.root / "excluded.zip", policy=policy)
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(set(package.namelist()), {"web/nested/visible.json", ".env.example", ".module-b-workspace.json"})
        restored = restore_workspace(archive, self.root / "excluded-restored", policy=policy)
        self.assertTrue((restored / ".env.example").is_file())
        marker = (project / ".module-b-workspace.json").read_bytes()
        for index, name in enumerate(("web/nested/.env.json", "web/nested/certificate.pem", "root.pem")):
            poisoned = self.root / f"private-{index}.zip"
            with zipfile.ZipFile(poisoned, "w") as package:
                package.writestr(".module-b-workspace.json", marker)
                package.writestr(name, "synthetic private content")
            target = self.root / f"private-{index}"
            with self.assertRaises(ValueError):
                restore_workspace(poisoned, target, policy=policy)
            self.assertFalse(target.exists())

    def test_prepare_omits_environment_variants_caches_and_dependencies_only(self):
        excluded = (
            ".env", ".env.local", "data/.env.json", "web/tls.pem",
            "web/node_modules/vendor/index.js", "app/.pytest_cache/state.json",
            "web/.cache/compiled.js", "notebooks/.ipynb_checkpoints/copy.ipynb",
        )
        retained = (".env.example", "data/.env.example", "data/real.json", "build/report.json", "dist/index.html")
        for name in (*excluded, *retained):
            path = self.example / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic content\n", encoding="utf-8")
        # Ignored dependencies may themselves contain links; do not traverse them.
        (self.example / "web/node_modules/external").symlink_to(self.root / "missing", target_is_directory=True)
        project = self.prepare()
        for name in excluded:
            self.assertFalse((project / name).exists(), name)
        for name in retained:
            self.assertTrue((project / name).is_file(), name)

    def test_export_and_restore_use_the_same_file_count_limit_including_manifest(self):
        project = self.prepare()
        # Three original permitted files plus 1,996 new files and one manifest = 2,000.
        for index in range(1996):
            (project / "app" / f"part_{index}.py").write_text("# saved\n", encoding="utf-8")
        archive = export_workspace(project, self.root / "limit.zip")
        restored = restore_workspace(archive, self.root / "limit-restored")
        self.assertTrue((restored / "app/part_1995.py").exists())
        (project / "app/one-too-many.py").write_text("# overflow\n", encoding="utf-8")
        rejected = self.root / "too-many.zip"
        with self.assertRaises(ValueError):
            export_workspace(project, rejected)
        self.assertFalse(rejected.exists())

    def test_archive_metadata_cannot_expand_caller_trusted_policy(self):
        marker = json.loads((self.prepare() / ".module-b-workspace.json").read_text())
        marker["policy"] = {"directory_suffixes": {"web": [".html"]}}
        archive = self.root / "self-authorized.zip"
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(".module-b-workspace.json", json.dumps(marker))
            package.writestr("web/index.html", "<main>Not in the caller's policy</main>")
        target = self.root / "self-authorized"
        with self.assertRaises(ValueError):
            restore_workspace(archive, target)
        self.assertFalse(target.exists())

    def test_policy_can_scope_nested_directories_and_exact_root_files(self):
        project = self.prepare()
        for name in ("web/src/app.ts", "web/other.ts", "web/src/style.css", "README.md", "other.md"):
            path = project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic example\n", encoding="utf-8")
        policy = WorkspacePolicy({"web/src": (".ts",)}, root_files=("README.md",))
        archive = export_workspace(project, self.root / "nested.zip", policy=policy)
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(set(package.namelist()), {"web/src/app.ts", "README.md", ".module-b-workspace.json"})


if __name__ == "__main__":
    unittest.main()
