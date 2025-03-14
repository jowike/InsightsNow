"""
Test CLI command execution: Ensure the run command works as expected with valid inputs.
"""

import subprocess

def test_run_command_with_nodes():
    import maynard
    
    result = subprocess.run(
        ["maynard", "run", "--nodes", "estimate_ml_models_node,estimate_arima_node,estimate_var_node"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Expected success, but got {result.returncode}"
    assert result.stderr == ''
