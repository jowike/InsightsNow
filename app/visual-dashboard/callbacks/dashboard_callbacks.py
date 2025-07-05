from dash import Input, Output, State, html, callback_context, ALL
from dash_spa.components.table import TableContext

from dash.exceptions import PreventUpdate
from pathlib import Path
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
import os
import subprocess
import socket
import signal
import base64
import pandas as pd
from dash import (
    ctx,
    no_update,
)  # Dash context to track which input triggered the callback

from config import (
    load_predictions,
    load_cards,
    load_contributions,
    load_series,
    load_evaluation,
    format_diff,
)
from pages.icons.hero import ICON
from pages.dashboard.table_local import LocalExplanationTable

from dash import html, Output
from pages.icons.hero import ICON

from dash_spa.components.table import TableContext
import dash_bootstrap_components as dbc

LocalExplanationTable = TableContext.Provider(id="local_explanation_table")(LocalExplanationTable)

kedro_viz_process = None
viz_port = None

from config import parameters, data_catalog, load_contributions

_, dropdown_options = load_contributions()


def register_callbacks(app, project_root):
    @app.callback(
        Output("pipeline-status", "children"), Input("run-pipeline-button", "n_clicks")
    )
    def trigger_pipeline_run(n_clicks):
        if n_clicks > 0:
            try:
                print(os.getcwd())
                # Initialize Kedro session
                bootstrap_project(Path(project_root))
                with KedroSession.create(Path(project_root)) as session:
                    session.run()
                return html.Div(
                    [
                        html.Span(ICON.DIAMOND, className="me-1"),
                        html.Span(
                            "Pipeline executed successfully!", style={"color": "green"}
                        ),
                    ]
                )
            except Exception as e:
                return html.Div(
                    [
                        html.Span(ICON.DIAMOND, className="me-1"),
                        html.Span(
                            f"Pipeline execution failed: {str(e)}",
                            style={"color": "red"},
                        ),
                    ]
                )
        return html.Div([html.Span("")])

    @app.callback(
        Output("pipeline-viz", "children"),
        [
            Input("start-viz-button", "n_clicks"),
            Input("stop-viz-button", "n_clicks"),
        ],
    )
    def manage_pipeline_viz(start_clicks, stop_clicks):
        global kedro_viz_process, viz_port

        # def __find_free_port(port=5003, max_port=65535):
        #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     while port <= max_port:
        #         try:
        #             sock.bind(("", port))
        #             sock.close()
        #             return port
        #         except OSError:
        #             port += 1
        #     raise IOError("no free ports")

        # Start Kedro Viz
        if start_clicks > 0:
            if kedro_viz_process is None or kedro_viz_process.poll() is not None:
                try:
                    # viz_port = __find_free_port()
                    viz_port = 5000

                    # Start Kedro Viz in a new process group
                    kedro_viz_process = subprocess.Popen(
                        f"cd {project_root} && kedro viz run --host 0.0.0.0 --port={viz_port}",
                        shell=True,
                        preexec_fn=os.setsid,  # Create a new process group
                    )
                    return html.Div(
                        [
                            html.Div(
                                [
                                    "✨ Kedro Viz is running at ",
                                    html.A(
                                        f"https://insightsviz.mini.pw.edu.pl",
                                        href=f"https://insightsviz.mini.pw.edu.pl",
                                        target="_blank",
                                        style={
                                            "color": "#7FBBFF",
                                            "text-decoration": "underline",
                                        },
                                    ),
                                ]
                            ),
                        ]
                    )
                except Exception as e:
                    return html.Div(
                        f"✨ Failed to start Kedro Viz: {str(e)}", style={"color": "red"}
                    )

        # Stop Kedro Viz
        if stop_clicks > 0:
            if kedro_viz_process:
                try:
                    # Kill the entire process group
                    os.killpg(os.getpgid(kedro_viz_process.pid), signal.SIGTERM)
                    kedro_viz_process.wait(timeout=5)  # Ensure the process terminates
                    kedro_viz_process = None  # Reset the process variable
                    viz_port = None  # Reset the port variable
                    return html.Div(
                        "✨ Kedro Viz has been stopped.", className="text-muted"
                    )
                except subprocess.TimeoutExpired:
                    return html.Div(
                        "✨ Failed to stop Kedro Viz: Timeout occurred.",
                        style={"color": "red"},
                    )
                except Exception as e:
                    return html.Div(
                        f"✨ Failed to stop Kedro Viz: {str(e)}", style={"color": "red"}
                    )

        # Default output if no action is triggered
        return html.Div([html.Span("")])

    # Callback to toggle the modal visibility
    @app.callback(
        Output("guidelines-modal", "is_open"),
        [Input("info-icon", "n_clicks"), Input("close-modal", "n_clicks")],
        [State("guidelines-modal", "is_open")],
    )
    def toggle_modal(info_clicks, close_clicks, is_open):
        if info_clicks or close_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output("advanced-config-modal", "is_open"),
        [
            Input("advanced-config-modal-open", "n_clicks"),
            Input("advanced-config-modal-close", "n_clicks"),
        ],
        [State("advanced-config-modal", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        Output("upload-files-modal", "is_open"),
        [
            Input("upload-files-modal-open", "n_clicks"),
            Input("upload-files-modal-close", "n_clicks"),
        ],
        [State("upload-files-modal", "is_open")],
    )
    def toggle_upload(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    # Callback
    @app.callback(
        Output("output-data-upload", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
    )
    def update_output(list_of_contents, list_of_names):
        def __handle_upload(contents, filename):
            try:
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)

                # Save the file to the target folder
                target_path = os.path.join(app.upload_target, filename)
                with open(target_path, "wb") as f:
                    f.write(decoded)

                # Calculate file size
                file_size_kb = len(decoded) / 1024
                file_size_str = (
                    f"{file_size_kb:.2f} KB"
                    if file_size_kb < 1024
                    else f"{file_size_kb / 1024:.2f} MB"
                )

                # Success message with file details
                message = f"Upload successful!\nFile: {filename} ({file_size_str})"
                icon_color = "#37BE67"  # Green for success
                icon_class = "fa fa-check"  # Font Awesome check icon
            except Exception:
                # Failure message
                message = "Upload failed! Please try again."
                icon_color = "#F4405E"  # Red for failure
                icon_class = "fas fa-times"  # Font Awesome cross icon

            return html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className=icon_class,
                                style={
                                    "margin-right": "10px",
                                    "font-size": "20px",
                                    "color": icon_color,  # Only the icon is colored
                                },
                            ),
                            html.Span(
                                message,
                                style={
                                    "font-size": "14px",
                                    "font-weight": "bold",
                                    "color": "#000000",  # Message text is black
                                },
                            ),
                        ],
                        style={
                            "padding": "10px",
                            "margin-top": "10px",
                            "text-align": "center",
                            "display": "inline-flex",
                            "align-items": "center",
                        },
                    )
                ]
            )

        if list_of_contents is not None:
            children = [
                __handle_upload(c, n) for c, n in zip(list_of_contents, list_of_names)
            ]
            return children

    # Callback to save changes
    @app.callback(
        Output("output-edit-advanced-config", "children"),
        Input("save-button", "n_clicks"),
        State("textarea-parameters", "value"),
        State("textarea-catalog", "value"),
        prevent_initial_call=True,
    )
    def save_file(n_clicks, parameters_content, data_catalog_content):
        def __save_yaml(file_path, content):
            with open(file_path, "w") as file:
                file.write(content)

        try:
            __save_yaml(app.parameters_path, parameters_content)
            __save_yaml(app.catalog_path, data_catalog_content)

            message = "Update successful!"
            icon_color = "#37BE67"  # Green for success
            icon_class = "fa fa-check"  # Font Awesome check icon

        except Exception:
            message = "Edit failed! Please try again."
            icon_color = "#F4405E"  # Red for failure
            icon_class = "fas fa-times"  # Font Awesome cross icon

        return html.Div(
            [
                html.Div(
                    [
                        html.I(
                            className=icon_class,
                            style={
                                "margin-right": "10px",
                                "font-size": "20px",
                                "color": icon_color,  # Only the icon is colored
                            },
                        ),
                        html.Span(
                            message,
                            style={
                                "font-size": "14px",
                                "font-weight": "bold",
                                "color": "#000000",  # Message text is black
                            },
                        ),
                    ],
                    style={
                        "padding": "10px",
                        "margin-top": "10px",
                        "margin-bottom": "20px",
                        "text-align": "center",
                        "display": "inline-flex",
                        "align-items": "center",
                    },
                )
            ]
        )

    # Callback to enable and disable editing
    @app.callback(
        [
            Output("textarea-parameters", "disabled"),
            Output("textarea-catalog", "disabled"),
            Output("textarea-parameters", "value"),
            Output("textarea-catalog", "value"),
        ],
        [
            Input("enable-edit", "n_clicks"),
            Input("save-button", "n_clicks"),
            Input("discard-changes", "n_clicks"),
        ],
    )
    def toggle_textareas(enable_clicks, save_clicks, discard_clicks):
        # Check which button triggered the callback
        if ctx.triggered_id == "enable-edit":
            return False, False, no_update, no_update  # Enable both textareas
        elif ctx.triggered_id == "save-button":
            return True, True, no_update, no_update  # Disable both textareas
        elif ctx.triggered_id == "discard-changes":
            return True, True, parameters, data_catalog
        # Default case (keep textareas disabled)
        return True, True, no_update, no_update

    # Periodic callback to update data in `dcc.Store` when the file changes
    @app.callback(
        Output("shared-data", "data"), Input("interval-component", "n_intervals")
    )
    def update_shared_data(n_intervals):
        shared_data = {}
        nowcast_series, header = load_predictions()
        contributions, dropdown_options = load_contributions()

        shared_data["nowcast_series"] = nowcast_series
        shared_data["nowcast_header"] = header
        shared_data["cards"] = load_cards()
        shared_data["local_explanation"], shared_data["dropdown_options"] = (
            contributions,
            dropdown_options,
        )

        if all(shared_data.values()):
            return shared_data
        raise PreventUpdate  # Prevent update if no new data

    # Define a callback to update the data in the chart when the store data changes
    @app.callback(
        [
            Output("nowcast-chart", "data"),
            Output("nowcast-series-name", "children"),
            Output("nowcast-pred-value", "children"),
            Output("nowcast-pred-change", "children"),
            Output("nowcast-annotation", "children"),
            Output("global-explanation-legend-gray", "children"),
        ],
        Input("shared-data", "data"),  # Get the data from the store
    )
    def update_nowcast_chart(shared_data):
        if shared_data is None:
            raise PreventUpdate  # Do not update if no data

        value = float(shared_data["nowcast_header"]["Value"])
        pct_diff = float(shared_data["nowcast_header"]["Since Last Month"])

        diff_class, diff_icon = format_diff(pct_diff)

        change_children = [
            "Since Last Month",
            diff_icon,
            html.Span(
                "{:.2%}".format(pct_diff).replace(".0%", "%"), className=diff_class
            ),
        ]

        annot_children = [
            shared_data["nowcast_header"]["Reference Period"],
            ICON.GLOBE.ME1,
            shared_data["nowcast_header"]["Region"],
        ]
        return (
            shared_data["nowcast_series"],
            f'{shared_data["nowcast_header"]["Series Name"]} ({shared_data["nowcast_header"]["Series Code"]})',
            "{:,.1f}".format(value).rstrip(".0"),
            change_children,
            annot_children,
            shared_data["nowcast_header"]["Series Code"],
        )  # Return the transformed data

    # Define a callback to update the data in the chart when the store data changes
    @app.callback(
        [
            Output("data-as-of-date", "children"),
            Output("nowcast-as-of-date", "children"),
        ],
        Input("shared-data", "data"),  # Get the data from the store
    )
    def update_watermarks(shared_data):
        if shared_data is None:
            raise PreventUpdate  # Do not update if no data

        data_watermark = f'⏳ Data as of Date: {pd.to_datetime(shared_data["nowcast_header"]["Data as of"], dayfirst=True).strftime("%-m/%-d/%Y %-I:%M %p CET")}'
        nowcast_watermark = f'Last Run Watermark: {pd.to_datetime(shared_data["nowcast_header"]["Last Run Watermark"], dayfirst=True).strftime("%-m/%-d/%Y %-I:%M %p CET")}'

        return (data_watermark, nowcast_watermark)  # Return the transformed data

    # Define a callback to update the data in the chart when the store data changes
    @app.callback(
        [
            Output("var-pred-value", "children"),
            Output("arima-pred-value", "children"),
            Output("conf-int-value", "children"),
            Output("conf-int-unit", "children"),
            Output("var-pred-change", "children"),
            Output("arima-pred-change", "children"),
            Output("conf-int-change", "children"),
            Output("var-annotation", "children"),
            Output("arima-annotation", "children"),
        ],
        Input("shared-data", "data"),  # Get the data from the store
    )
    def update_cards(shared_data):
        if not shared_data:
            raise PreventUpdate  # Do not update if no data

        data = shared_data.get("cards", {})

        # Extract values
        var_value = float(data["VAR"]["Value"])
        arima_value = float(data["ARIMA"]["Value"])
        conf_int_value = float(data["Confidence Interval"]["Value"])

        # Calculate differences for "Since Last Month"
        var_diff = float(data["VAR"]["Since Last Month"])
        arima_diff = float(data["ARIMA"]["Since Last Month"])
        conf_int_diff = float(data["Confidence Interval"]["Since Last Month"])

        # Format VAR and ARIMA differences
        var_diff_class, var_diff_icon = format_diff(var_diff)
        arima_diff_class, arima_diff_icon = format_diff(arima_diff)

        # Format children for VAR and ARIMA change
        var_div_children = [
            "Since Last Month",
            var_diff_icon,
            html.Span(
                "{:.2%}".format(var_diff).replace(".0%", "%"), className=var_diff_class
            ),
        ]
        arima_div_children = [
            "Since Last Month",
            arima_diff_icon,
            html.Span(
                "{:.2%}".format(arima_diff).replace(".0%", "%"),
                className=arima_diff_class,
            ),
        ]

        # Format children for VAR and ARIMA change
        var_annot_children = [
            "Prediction Uncertainty: ",
            "{:,.0f}".format(float(data["VAR"]["Prediction Range"])),
        ]
        arima_annot_children = [
            "Prediction Uncertainty: ",
            "{:,.0f}".format(float(data["ARIMA"]["Prediction Range"])),
        ]

        # Return formatted data
        return (
            "{:,.1f}".format(var_value).rstrip(".0"),  # Format VAR value
            "{:,.1f}".format(arima_value).rstrip(".0"),  # Format ARIMA value
            "{:,.1f}".format(
                conf_int_value
            ),  # Format Confidence Interval value in thousands
            shared_data["nowcast_header"]["Unit"],
            var_div_children,  # VAR change
            arima_div_children,  # ARIMA change
            "{:,.1%}".format(conf_int_diff).replace(
                ".0%", "%"
            ),  # Confidence interval change
            var_annot_children,  # VAR annotation
            arima_annot_children,  # ARIMA annotation
        )

    # Define a callback to update the data in the chart when the store data changes
    @app.callback(
        Output("local-explanation-table", "children"), Input("shared-data", "data")
    )
    def update_local_explanation(shared_data):
        if not shared_data:
            raise PreventUpdate

        local_explanation_data = shared_data["local_explanation"]
        columns = [
            {"id": c, "name": c} for c in ["Release Date", "Data Series", "Impact"]
        ]

        # Instantiate the PageVisitsTable with the updated data
        table = LocalExplanationTable(
            data=local_explanation_data,
            columns=columns,
        )
        return table

    # Define a callback to update the data in the chart when the store data changes
    @app.callback(
        [
            Output("average-error-rate", "children"),
            Output("adjusted-r-squared", "children"),
            Output("indicators-count", "children"),
            Output("models-count", "children"),
        ],
        Input("shared-data", "data"),
    )
    def update_evaluation(shared_data):
        if not shared_data:
            raise PreventUpdate

        evaluation_measures = load_evaluation()

        return (
            "{:.2%}".format(evaluation_measures["Average Error Rate"]),
            "{:.2%}".format(evaluation_measures["Adjusted R-Squared"]).replace(
                ".0%", "%"
            ),
            int(evaluation_measures["Processed Variables Count"]),
            int(evaluation_measures["Model Estimations Count"]),
        )

    @app.callback(
        Output("dropdown-menu", "children"),
        [
            Input("shared-data", "data"),
            Input("dropdown-menu", "children"),
            Input("global-explanation-legend-gray", "children"),
        ],
    )
    def update_dropdown_options(shared_data, current_options, series_code):
        if not shared_data:
            raise PreventUpdate

        current_options = [d["props"]["children"] for d in current_options]
        if (set(current_options) == set(shared_data["dropdown_options"])) and (
            shared_data["nowcast_header"]["Series Code"] == series_code
        ):
            raise PreventUpdate

        return [
            dbc.DropdownMenuItem(
                option,
                id={"type": "series-option", "index": option}
            )
            for option in shared_data["dropdown_options"]
        ]

    @app.callback(
        [
            Output("global-explanation-chart", "data"),
            Output("global-explanation-value", "children"),
            Output("global-explanation-change", "children"),
            Output("global-explanation-selected-option", "children"),
        ],
        Input({"type": "series-option", "index": ALL}, "n_clicks"),
    )
    def update_selection(n_clicks_list):
        # ⛔️ zabezpieczenie przed uruchomieniem bez triggera
        if not ctx.triggered_id or all(n is None for n in n_clicks_list):
            raise PreventUpdate

        selected_option = ctx.triggered_id["index"]  # ✅ pattern-matching ID

        data = load_series(series_id=selected_option, diff=False)
        value = float(data["series"][1][-1])
        lag = float(data["series"][1][-2])
        pct_diff = (value - lag) / lag

        diff_class, diff_icon = format_diff(pct_diff)

        children = [
            "Since Last Month",
            diff_icon,
            html.Span(
                "{:.2%}".format(pct_diff).replace(".0%", "%"),
                className=diff_class
            ),
        ]

        data = load_series(series_id=selected_option)

        return data, "{:,.1f}".format(value).rstrip(".0"), children, selected_option

    @app.callback(
        Output("legend-hidden-row", "style"),
        Output("legend-toggle-btn", "children"),
        Input("legend-toggle-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_legend(n):
        if n and n % 2 == 1:
            return {
                "display": "flex",
                "justifyContent": "center",
                "gap": "20px",
                "flexWrap": "wrap",
                "marginBottom": "8px",
            }, "Show less"
        else:
            return {
                "display": "none",
                "justifyContent": "center",
                "gap": "20px",
                "flexWrap": "wrap",
                "marginBottom": "8px",
            }, "Show more"
