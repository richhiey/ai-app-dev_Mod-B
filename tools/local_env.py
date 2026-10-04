"""Create a local .env once, keeping generated caller values out of terminal output."""

from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / ".env"
    try:
        with path.open("x") as out:
            out.write(
                "OPENROUTER_API_KEY=\nOPENROUTER_MODEL=google/gemini-3.1-flash-lite\n"
            )
            for name in ("FIELDCARE_DISPATCH_KEY", "FIELDCARE_PARTNER_KEY"):
                out.write(f"{name}={secrets.token_urlsafe(32)}\n")
    except FileExistsError:
        raise SystemExit(
            ".env already exists; keep it and edit it in VS Code. Nothing was overwritten."
        )
    print(
        "Created .env with two distinct caller keys. Open it in VS Code to set the provider key when needed."
    )


if __name__ == "__main__":
    main()
