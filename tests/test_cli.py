import subprocess
import sys
import pytest

def run_cli_command(args):
    """Run CLI command and return stdout, stderr, and return code."""
    cmd = [sys.executable, "-m", "seekify.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def test_cli_version():
    result = run_cli_command(["version"])
    assert result.returncode == 0
    assert "1.0.0" in result.stdout

def test_cli_text_search():
    # Test basic text search with a specific backend
    result = run_cli_command(["text", "-q", "python", "-m", "1", "-b", "duckduckgo"])
    if result.returncode != 0:
        print(f"CLI Output: {result.stdout}")
        print(f"CLI Error: {result.stderr}")
    assert result.returncode == 0
    # Check for likely content
    assert "python" in result.stdout.lower() or "programming" in result.stdout.lower()

def test_cli_json_output(tmp_path):
    # Test output to JSON
    output_file = tmp_path / "results.json"
    result = run_cli_command(["text", "-q", "test", "-m", "1", "-o", str(output_file)])
    assert result.returncode == 0
    assert output_file.exists()
