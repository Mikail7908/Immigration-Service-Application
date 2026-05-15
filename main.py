"""Entry point for the immigration verification prototype.

Run: python main.py
"""
from src.logging_setup import configure_logging
from src.cli.console import ConsoleApp

def main() -> None:
    configure_logging(log_dir='logs')
    app = ConsoleApp(data_dir='data', audit_path='logs/audit.jsonl')
    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        print('\nInterrupted. Goodbye.')
if __name__ == '__main__':
    main()
