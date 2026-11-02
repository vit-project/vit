"""Launch the interactive application from the installed command."""

from __future__ import annotations

from vit import parse_options, Application


def main() -> None:
    """Parse command-line arguments and start the VIT event loop."""
    options, filters = parse_options()
    Application(options, filters).run()


if __name__ == "__main__":
    main()
