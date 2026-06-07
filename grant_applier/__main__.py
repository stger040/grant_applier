"""Module entrypoint for ``python -m grant_applier``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
