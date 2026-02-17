"""Entry point for running dtJiraMCPServer as a module.

Usage:
    python -m dtjiramcpserver
"""

from dtjiramcpserver.app import JiraMCPServerApp


def main() -> None:
    """Main entry point for the application."""
    app = JiraMCPServerApp()
    app.run()


if __name__ == "__main__":
    main()
