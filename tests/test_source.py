"""Read current source safely without executing learner code."""
from pathlib import Path
import tempfile
import unittest

from module_b.source import source_excerpt


SOURCE = '''from somewhere import router

# Merely reading this file must not execute it.
raise RuntimeError("Do not import me")

@router.post(
    "/sample",
    response_model=Response,
)
def handle(request: Request) -> Response:
    """Preserve the learner's current implementation."""
    return work(request)

class Container:
    @staticmethod
    async def inner():
        return "learner edit"
'''


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        (self.project / "app").mkdir(parents=True)
        self.file = self.project / "app/routes.py"
        self.file.write_text(SOURCE, encoding="utf-8")

    def test_complete_file_is_returned_without_import(self):
        self.assertEqual(source_excerpt(self.project, "app/routes.py"), SOURCE)

    def test_function_excerpt_includes_multiline_decorator_and_not_other_code(self):
        expected = '''@router.post(
    "/sample",
    response_model=Response,
)
def handle(request: Request) -> Response:
    """Preserve the learner's current implementation."""
    return work(request)
'''
        self.assertEqual(source_excerpt(self.project, "app/routes.py", "handle"), expected)

    def test_dotted_class_method_retains_indent_decorator_and_async(self):
        excerpt = source_excerpt(self.project, "app/routes.py", "Container.inner")
        self.assertEqual(excerpt, '    @staticmethod\n    async def inner():\n        return "learner edit"\n')

    def test_source_reflects_current_user_edits(self):
        self.file.write_text(SOURCE.replace("return work(request)", "return different(request)"), encoding="utf-8")
        self.assertIn("return different(request)", source_excerpt(self.project, "app/routes.py", "handle"))

    def test_missing_or_invalid_symbol_fails_explicitly(self):
        for symbol in ("missing", "Container.missing", "handle()", "", "Container..inner"):
            with self.subTest(symbol=symbol), self.assertRaises(ValueError):
                source_excerpt(self.project, "app/routes.py", symbol)

    def test_traversal_absolute_paths_and_non_application_files_are_rejected(self):
        for path in ("../outside.py", "app/../../outside.py", "app/../app/routes.py",
                     str(self.file), ".env", "tests/test_routes.py", "app/private.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                source_excerpt(self.project, path)

    def test_symlink_file_and_symlink_directory_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "private.py").write_text("SECRET = True\n", encoding="utf-8")
        (self.project / "app/link.py").symlink_to(outside / "private.py")
        (self.project / "app/external").symlink_to(outside, target_is_directory=True)
        for path in ("app/link.py", "app/external/private.py"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                source_excerpt(self.project, path)

    def test_symlink_project_is_rejected(self):
        alias = self.root / "alias"
        alias.symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(ValueError):
            source_excerpt(alias, "app/routes.py")


if __name__ == "__main__":
    unittest.main()
