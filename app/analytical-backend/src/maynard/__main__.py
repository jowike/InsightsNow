"""maynard file for ensuring the package is executable
as `maynard` and `python -m maynard`
"""
import sys
from pathlib import Path
from typing import Any

from kedro.framework.cli.utils import find_run_command
from kedro.framework.project import configure_project

from kedro_viz.server import run_server

import os
import subprocess
import socket

from typing import List, Optional

import typer

app = typer.Typer()
project_root="../.."

@app.command()
def run(
    nodes: str = typer.Option(None, "--nodes", help="Specify nodes to run"),
    from_nodes: str = typer.Option(None, "--from-nodes", help="Specify the nodes to run from"),
    to_nodes: str = typer.Option(None, "--to-nodes", help="Specify the nodes to run to"),
) -> Any:
    """
    Run the Kedro pipeline with optional node parameters.

    This function triggers the Kedro pipeline with a user-defined node, a set of
    source nodes, or a set of target nodes. The user can specify **only one** of the 
    following options at a time:
    
    - `--nodes`: Specify nodes to run.
    - `--from-nodes`: Specify the nodes to run from.
    - `--to-nodes`: Specify the nodes to run to.

    **Mutually Exclusive Rule**:
    Only **one** of the options `--nodes`, `--from-nodes`, or `--to-nodes` can be specified at a time. If multiple options are provided, a `BadParameter` error will be raised, and the user will be prompted to choose just one.

    Parameters:
    -----------
    nodes : str, optional
       The nodes to run in the pipeline.
    from_nodes : str, optional
        The nodes to start the pipeline from.
    to_nodes : str, optional
        The nodes to run to in the pipeline.
    
    Raises:
    -------
    typer.BadParameter
        If more than one of the mutually exclusive arguments (`--nodes`, `--from-nodes`, or `--to-nodes`) is specified.
    """
    package_name = Path(__file__).parent.name
    configure_project(package_name)

    # Ensure only one of the options is passed
    if sum([bool(nodes), bool(from_nodes), bool(to_nodes)]) > 1:
        raise typer.BadParameter("❌ You can only specify one of --node, --from-nodes, or --to-nodes at a time.")
    
    # Collect arguments for Kedro run
    kedro_args = sys.argv[2:]  # Skip the initial "maynard run"
    # Append the selected option to kedro_args
    if nodes:
        kedro_args = ["--nodes", nodes]
    elif from_nodes:
        kedro_args = ["--from-nodes", from_nodes]
    elif to_nodes:
        kedro_args = ["--to-nodes", to_nodes]

    # Check if interactive mode is enabled
    interactive = hasattr(sys, 'ps1')
    standalone_mode = not interactive

    run_command = find_run_command(package_name)

    return run_command(args=kedro_args, standalone_mode=standalone_mode)

@app.command()
def viz():
    """Launch Kedro Viz with an available port"""

    def __find_free_port(port=5001, max_port=65535):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while port <= max_port:
            try:
                sock.bind(("", port))
                sock.close()
                return port
            except OSError:
                port += 1
        raise IOError("no free ports")

    try:
        viz_port = __find_free_port()
    except IOError:
        typer.echo("🚨 No free ports available for Kedro Viz!", err=True)
        raise typer.Exit(1)

    try:
        package_name = Path(__file__).parent.name
        configure_project(package_name)

        project_path = os.path.abspath(os.path.join(__file__, "../../.."))
        typer.echo(f"🔍 Using project path: {project_path}")

        typer.echo(f"✨ Kedro Viz is starting at http://127.0.0.1:{viz_port}/")
        run_server(project_path=project_path, port=viz_port)
        # subprocess.Popen(
        #     f"cd {project_path} && kedro viz --host 0.0.0.0 --port={viz_port}",
        #     shell=True,
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.DEVNULL,
        #     start_new_session=True  # Detach from the current process
        # )
        # typer.echo(f"✨ Kedro Viz is running at http://127.0.0.1:{viz_port}/")
    except Exception as e:
        typer.echo(f"❌ Failed to start Kedro Viz: {str(e)}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
