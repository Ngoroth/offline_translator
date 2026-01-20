import pytest
from unittest.mock import patch
from app.core.output_console import ConsoleOutput


def test_console_output_status():
    output = ConsoleOutput()
    with patch("builtins.print") as mock_print:
        output.status("Hello World")
        mock_print.assert_called_with("[*] Hello World")


def test_console_output_error():
    output = ConsoleOutput()
    with patch("builtins.print") as mock_print:
        output.error("Something went wrong")
        mock_print.assert_called_with("[!] ERROR: Something went wrong")
