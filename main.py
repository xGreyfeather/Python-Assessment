import dash
from dash import dcc, html, Input, Output, ClientsideFunction
import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
import pathlib

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Clinical Analytics Dashboard"

server = app.server
app.config.suppress_callback_exceptions = True

BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("data").resolve()

df = pd.read_csv(DATA_PATH.joinpath("clinical_analytics.csv.gz"))

clinic_list = df["Clinic Name"].unique()
df["Admit Source"] = df["Admit Source"].fillna("Not Identified")
admit_list = df["Admit Source"].unique().tolist()

df["Check-In Time"] = df["Check-In Time"].apply(
    lambda x: dt.strptime(x, "%Y-%m-%d %I:%M:%S %p")
)

df["Days of Wk"] = df["Check-In Time"].apply(lambda x: dt.strftime(x, "%A"))
df["Check-In Hour"] = df["Check-In Time"].apply(lambda x: dt.strftime(x, "%I %p"))

day_list = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]

check_in_duration = df["Check-In Time"].describe()

all_departments = df["Department"].unique().tolist()
wait_time_inputs = [Input((i + "_wait_time_graph"), "selectedData") for i in all_departments]
score_inputs = [Input((i + "_score_graph"), "selectedData") for i in all_departments]


def description_card():
    return html.Div(
        id="description-card",
        children=[
            html.H5("Clinical Analytics"),
            html.H3("Welcome to the Clinical Analytics Dashboard"),
            html.Div(
                id="intro",
                children=(
                    "Explore clinic patient volume by time of day, waiting time, and care score. "
                    "Click on the heatmap to visualize patient experience at different time points."
                ),
            ),
        ],
    )


def generate_control_card():
    return html.Div(
        id="control-card",
        children=[
            html.P("Select Clinic"),
            dcc.Dropdown(
                id="clinic-select",
                options=[{"label": i, "value": i} for i in clinic_list],
                value=clinic_list[0],
            ),
            html.Br(),
            html.P("Select Check-In Time"),
            dcc.DatePickerRange(
                id="date-picker-select",
                start_date=dt(2014, 1, 1),
                end_date=dt(2014, 1, 15),
                min_date_allowed=dt(2014, 1, 1),
                max_date_allowed=dt(2014, 12, 31),
                initial_visible_month=dt(2014, 1, 1),
            ),
            html.Br(),
            html.Br(),
            html.P("Select Admit Source"),
            dcc.Dropdown(
                id="admit-select",
                options=[{"label": i, "value": i} for i in admit_list],
                value=admit_list[:],
                multi=True,
            ),
            html.Br(),
        ],
    )


def generate_patient_volume_heatmap(start, end, clinic, hm_click, admit_type, reset):
    filtered_df = df[
        (df["Clinic Name"] == clinic) & (df["Admit Source"].isin(admit_type))
    ]
    filtered_df = (
        filtered_df.sort_values("Check-In Time")
        .set_index("Check-In Time")[start:end]
    )

    x_axis = [datetime.time(i).strftime("%I %p") for i in range(24)]
    y_axis = day_list

    hour_of_day = ""
    weekday = ""
    shapes = []

    if hm_click is not None:
        hour_of_day = hm_click["points"][0]["x"]
        weekday = hm_click["points"][0]["y"]

        x0 = x_axis.index(hour_of_day) / 24
        x1 = x0 + 1 / 24
        y0 = y_axis.index(weekday) / 7
        y1 = y0 + 1 / 7

        shapes = [
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=x0,
                x1=x1,
                y0=y0,
                y1=y1,
                line=dict(color="#ff6347"),
            )
        ]

    z = np.zeros((7, 24))
    annotations = []

    for ind_y, day in enumerate(y_axis):
        filtered_day = filtered_df[filtered_df["Days of Wk"] == day]
        for ind_x, x_val in enumerate(x_axis):
            total_records = filtered_day[filtered_day["Check-In Hour"] == x_val][
                "Number of Records"
            ].sum()
            z[ind_y][ind_x] = total_records

            annotation = dict(
                showarrow=False,
                text=f"<b>{total_records}<b>",
                xref="x",
                yref="y",
                x=x_val,
                y=day,
                font=dict(family="sans-serif"),
            )

            if x_val == hour_of_day and day == weekday and not reset:
                annotation.update(size=15, font=dict(color="#ff6347"))

            annotations.append(annotation)

    hovertemplate = "<b>%{y}  %{x}<br><br>%{z} Patient Records"

    data = [
        dict(
            x=x_axis,
            y=y_axis,
            z=z,
            type="heatmap",
            name="",
            hovertemplate=hovertemplate,
            showscale=False,
            colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]],
        )
    ]

    layout = dict(
        margin=dict(l=70, b=50, t=50, r=50),
        modebar={"orientation": "v"},
        font=dict(family="Open Sans"),
        annotations=annotations,
        shapes=shapes,
        xaxis=dict(
            side="top",
            ticks="",
            ticklen=2,
            tickfont=dict(family="sans-serif"),
            tickcolor="#ffffff",
        ),
        yaxis=dict(
            side="left",
            ticks="",
            tickfont=dict(family="sans-serif"),
            ticksuffix=" "
        ),
        hovermode="closest",
        showlegend=False,
    )
    return {"data": data, "layout": layout}


def generate_table_row(id, style, col1, col2, col3):
    return html.Div(
        id=id,
        className="row table-row",
        style=style,
        children=[
            html.Div(
                id=col1["id"],
                style={"display": "table", "height": "100%"},
                className="two columns row-department",
                children=col1["children"],
            ),
            html.Div(
                id=col2["id"],
                style={"textAlign": "center", "height": "100%"},
                className="five columns",
                children=col2["children"],
            ),
            html.Div(
                id=col3["id"],
                style={"textAlign": "center", "height": "100%"},
                className="five columns",
                children=col3["children"],
            ),
        ],
    )


def generate_table_row_helper(department):
    return generate_table_row(
        department,
        {},
        {"id": department + "_department", "children": html.B(department)},
        {
            "id": department + "wait_time",
            "children": dcc.Graph(
                id=department + "_wait_time_graph",
                style={"height": "100%", "width": "100%"},
                className="wait_time_graph",
                config={"staticPlot": False, "editable": False, "displayModeBar": False},
                figure={
                    "layout": dict(
                        margin=dict(l=0, r=0, b=0, t=0, pad=0),
                        xaxis=dict(showgrid=False, showline=False,
                                   showticklabels=False, zeroline=False),
                        yaxis=dict(showgrid=False, showline=False,
                                   showticklabels=False, zeroline=False),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                },
            ),
        },
        {
            "id": department + "_patient_score",
            "children": dcc.Graph(
                id=department + "_score_graph",
                style={"height": "100%", "width": "100%"},
                className="patient_score_graph",
                config={"staticPlot": False, "editable": False, "displayModeBar": False},
                figure={
                    "layout": dict(
                        margin=dict(l=0, r=0, b=0, t=0, pad=0),
                        xaxis=dict(showgrid=False, showline=False,
                                   showticklabels=False, zeroline=False),
                        yaxis=dict(showgrid=False, showline=False,
                                   showticklabels=False, zeroline=False),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                },
            ),
        },
    )


def initialize_table():
    header = [
        generate_table_row(
            "header",
            {"height": "50px"},
            {"id": "header_department", "children": html.B("Department")},
            {"id": "header_wait_time_min", "children": html.B("Wait Time Minutes")},
            {"id": "header_care_score", "children": html.B("Care Score")},
        )
    ]
    header.extend(generate_table_row_helper(dept) for dept in all_departments)
    return header


def generate_patient_table(figure_list, departments, wait_time_xrange, score_xrange):
    header = [
        generate_table_row(
            "header",
            {"height": "50px"},
            {"id": "header_department", "children": html.B("Department")},
            {"id": "header_wait_time_min", "children": html.B("Wait Time Minutes")},
            {"id": "header_care_score", "children": html.B("Care Score")},
        )
    ]

    rows = [generate_table_row_helper(dep) for dep in departments]

    empty_deps = [d for d in all_departments if d not in departments]
    empty_rows = [generate_table_row_helper(dep) for dep in empty_deps]

    for i, dep in enumerate(departments):
        rows[i].children[1].children.figure = figure_list[i]
        rows[i].children[2].children.figure = figure_list[i + len(departments)]

    if empty_rows:
        for r in empty_rows[1:]:
            r.style = {"display": "none"}

        example = empty_rows[0]
        example.children[0].children = html.B("graph_ax",
                                               style={"visibility": "hidden"})

        ex_wait = example.children[1].children
        ex_wait.figure["layout"].update(margin=dict(t=-70, b=50, l=0, r=0, pad=0))
        ex_wait.config["staticPlot"] = True
        ex_wait.figure["layout"]["xaxis"].update(
            showline=True, showticklabels=True, tick0=0, dtick=20,
            range=wait_time_xrange
        )

        ex_score = example.children[2].children
        ex_score.figure["layout"].update(margin=dict(t=-70, b=50, l=0, r=0, pad=0))
        ex_score.config["staticPlot"] = True
        ex_score.figure["layout"]["xaxis"].update(
            showline=True, showticklabels=True, tick0=0, dtick=0.5,
            range=score_xrange
        )

    header.extend(rows)
    header.extend(empty_rows)
    return header


def create_table_figure(department, filtered_df, category, category_xrange, selected_index):
    aggregation = {
        "Wait Time Min": "mean",
        "Care Score": "mean",
        "Days of Wk": "first",
        "Check-In Time": "first",
        "Check-In Hour": "first",
    }

    df_by_dep = filtered_df[filtered_df["Department"] == department].reset_index()
    grouped = df_by_dep.groupby("Encounter Number").agg(aggregation).reset_index()

    patient_ids = grouped["Encounter Number"].astype(str)

    f = lambda x: dt.strftime(x, "%Y-%m-%d")
    check_in_str = (
        grouped["Check-In Time"].apply(f)
        + " "
        + grouped["Days of Wk"]
        + " "
        + grouped["Check-In Hour"].astype(str)
    )

    text_wait = (
        "Patient #: " + patient_ids +
        "<br>Check-in Time: " + check_in_str +
        "<br>Wait Time: " +
        grouped["Wait Time Min"].round(1).astype(str) +
        " Minutes, Care Score: " +
        grouped["Care Score"].round(1).astype(str)
    )

    layout = dict(
        margin=dict(l=0, r=0, b=0, t=0, pad=0),
        clickmode="event+select",
        hovermode="closest",
        xaxis=dict(showgrid=False, showline=False, showticklabels=False,
                   zeroline=False, range=category_xrange),
        yaxis=dict(showgrid=False, showline=False, showticklabels=False,
                   zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    trace = dict(
        x=grouped[category],
        y=[department] * len(grouped),
        mode="markers",
        marker=dict(size=14, line=dict(width=1, color="#ffffff"), color="#2c82ff"),
        selected=dict(marker=dict(color="#ff6347", opacity=1)),
        unselected=dict(marker=dict(opacity=0.1)),
        selectedpoints=selected_index,
        hoverinfo="text",
        customdata=patient_ids,
        text=text_wait,
    )

    return {"data": [trace], "layout": layout}


app.layout = html.Div(
    id="app-container",
    children=[
        html.Div(
            id="banner",
            className="banner",
            children=[html.Img(src=app.get_asset_url("plotly_logo.png"))],
        ),
        html.Div(
            id="left-column",
            className="four columns",
            children=[
                description_card(),
                generate_control_card(),
                html.Div(["initial child"], id="output-clientside", style={"display": "none"}),
            ],
        ),
        html.Div(
            id="right-column",
            className="eight columns",
            children=[
                html.Div(
                    id="patient_volume_card",
                    children=[
                        html.B("Patient Volume"),
                        html.Hr(),
                        dcc.Graph(id="patient_volume_hm"),
                        html.Div(
                            id="reset-btn-outer",
                            children=html.Button(id="reset-btn", children="Show All", n_clicks=0),
                        ),
                    ],
                ),
                html.Div(
                    id="wait_time_card",
                    children=[
                        html.B("Patient Wait Time and Satisfactory Scores"),
                        html.Hr(),
                        html.Div(id="wait_time_table", children=initialize_table()),
                    ],
                ),
            ],
        ),
    ],
)

@app.callback(
    Output("patient_volume_hm", "figure"),
    [
        Input("date-picker-select", "start_date"),
        Input("date-picker-select", "end_date"),
        Input("clinic-select", "value"),
        Input("patient_volume_hm", "clickData"),
        Input("admit-select", "value"),
        Input("reset-btn", "n_clicks"),
    ],
)
def update_heatmap(start, end, clinic, hm_click, admit_type, reset_click):
    start = start + " 00:00:00"
    end = end + " 00:00:00"

    reset = False
    ctx = dash.callback_context

    if ctx.triggered and ctx.triggered[0]["prop_id"].split(".")[0] == "reset-btn":
        reset = True

    return generate_patient_volume_heatmap(
        start, end, clinic, hm_click, admit_type, reset
    )


app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("wait_time_table", "children")] + wait_time_inputs + score_inputs,
)


@app.callback(
    Output("wait_time_table", "children"),
    [
        Input("date-picker-select", "start_date"),
        Input("date-picker-select", "end_date"),
        Input("clinic-select", "value"),
        Input("admit-select", "value"),
        Input("patient_volume_hm", "clickData"),
        Input("reset-btn", "n_clicks"),
    ]
    + wait_time_inputs
    + score_inputs,
)
def update_table(start, end, clinic, admit_type, heatmap_click, reset_click, *args):
    start = start + " 00:00:00"
    end = end + " 00:00:00"

    ctx = dash.callback_context

    prop_id = ""
    prop_type = ""
    triggered_value = None

    if ctx.triggered:
        prop_id, prop_type = ctx.triggered[0]["prop_id"].split(".")
        triggered_value = ctx.triggered[0]["value"]

    filtered_df = df[
        (df["Clinic Name"] == clinic) & (df["Admit Source"].isin(admit_type))
    ]
    filtered_df = (
        filtered_df.sort_values("Check-In Time")
        .set_index("Check-In Time")[start:end]
    )
    departments = filtered_df["Department"].unique()

    if heatmap_click is not None and prop_id != "reset-btn":
        hour = heatmap_click["points"][0]["x"]
        weekday = heatmap_click["points"][0]["y"]
        clicked_df = filtered_df[
            (filtered_df["Days of Wk"] == weekday)
            & (filtered_df["Check-In Hour"] == hour)
        ]
        departments = clicked_df["Department"].unique()
        filtered_df = clicked_df

    wait_range = [
        filtered_df["Wait Time Min"].min() - 2,
        filtered_df["Wait Time Min"].max() + 2,
    ]
    score_range = [
        filtered_df["Care Score"].min() - 0.5,
        filtered_df["Care Score"].max() + 0.5,
    ]

    figure_list = []

    if prop_type != "selectedData" or (prop_type == "selectedData" and triggered_value is None):
        for dep in departments:
            figure_list.append(
                create_table_figure(dep, filtered_df, "Wait Time Min", wait_range, "")
            )
        for dep in departments:
            figure_list.append(
                create_table_figure(dep, filtered_df, "Care Score", score_range, "")
            )

    else:
        selected_idx = [triggered_value["points"][0]["pointIndex"]]
        for dep in departments:
            idx = selected_idx if prop_id.split("_")[0] == dep else []
            figure_list.append(
                create_table_figure(dep, filtered_df, "Wait Time Min", wait_range, idx)
            )
        for dep in departments:
            idx = selected_idx if prop_id.split("_")[0] == dep else []
            figure_list.append(
                create_table_figure(dep, filtered_df, "Care Score", score_range, idx)
            )

    return generate_patient_table(figure_list, departments, wait_range, score_range)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10030,
        debug=True,
    )
