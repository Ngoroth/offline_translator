from unittest.mock import patch
from app.core.output_console import ConsoleOutput


def test_console_output_status() -> None:
    output = ConsoleOutput()
    with patch("builtins.print") as mock_print:
        output.status("Hello World")
        # In recommended mode, we don't need to cast to MagicMock
        # unless we access special attributes not in the original type.
        # But for 'print', it's already Any from patch.
        _ = mock_print.assert_called_with("[*] Hello World")


def test_console_output_error() -> None:
    output = ConsoleOutput()
    with patch("builtins.print") as mock_print:
        output.error("Something went wrong")
        _ = mock_print.assert_called_with("[!] ERROR: Something went wrong")
