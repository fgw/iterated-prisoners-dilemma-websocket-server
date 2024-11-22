from dash import dash_table, dcc
from styles import TABLE_STYLES, COLORS, TYPOGRAPHY, SPACING, LINE_COLORS

TOURNAMENT_ID = "Tournament ID"


def generate_tournament_overview_table(dataframes):
    data = []
    for tournament_id, df in dataframes.items():
        progress = len(df) if df is not None else 0
        data.append(
            {
                TOURNAMENT_ID: tournament_id,
                "Progress": "Completed" if progress == 100 else f"Iteration {progress}",
            }
        )

    return dash_table.DataTable(
        data=data,
        columns=[
            {"name": [TOURNAMENT_ID], "id": TOURNAMENT_ID},
            {"name": ["Progress"], "id": "Progress"},
        ],
        style_cell=TABLE_STYLES["cell"],
        style_header=TABLE_STYLES["header"],
        style_data=TABLE_STYLES["data"],
        style_data_conditional=TABLE_STYLES["data_conditional"],
        markdown_options={"html": True},
        style_table=TABLE_STYLES["table"],
    )


def generate_group_overview_table(all_scores):
    pass


def generate_score_progression_figure(tournament_uuid, scores):
    title = f"Tournament ID: {tournament_uuid}"
    subtitle = "in progress"
    if all(len(score) == 100 for score in scores.values()):
        winner = max(scores, key=lambda k: sum(scores[k]))
        score = scores[winner][-1]
        subtitle = f"{winner} won with {score} points"

    return dcc.Graph(
        figure={
            "data": [
                {
                    "x": list(range(len(score))),
                    "y": score,
                    "type": "line",
                    "name": participant,
                    "line": {"color": LINE_COLORS[i % len(LINE_COLORS)]},
                }
                for i, (participant, score) in enumerate(scores.items())
            ],
            "layout": {
                "title": {
                    "text": title
                    + f"<br><span style='font-size: {TYPOGRAPHY['sizes']['medium']}'>"
                    + subtitle
                    + "</span>",
                    "font": {
                        "family": TYPOGRAPHY["fontFamily"],
                        "size": int(TYPOGRAPHY["sizes"]["medium"].replace("px", "")),
                        "color": COLORS["text"],
                    },
                    "x": 0.5,
                    "y": 0.95,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                "xaxis": {
                    "title": "Iteration",
                    "dtick": 10,
                    "gridcolor": COLORS["background"]["alternate"],
                    "titlefont": {
                        "family": TYPOGRAPHY["fontFamily"],
                        "size": int(TYPOGRAPHY["sizes"]["small"].replace("px", "")),
                        "color": COLORS["text"],
                    },
                    "tickfont": {
                        "family": TYPOGRAPHY["fontFamily"],
                        "size": int(TYPOGRAPHY["sizes"]["body"].replace("px", "")),
                        "color": COLORS["text"],
                    },
                    "x": 0.5,  # Center the x-axis title
                    "y": -0.15,  # Move the x-axis title down
                },
                "yaxis": {
                    "title": "Cumulative Score",
                    "gridcolor": COLORS["background"]["alternate"],
                    "titlefont": {
                        "family": TYPOGRAPHY["fontFamily"],
                        "size": int(TYPOGRAPHY["sizes"]["small"].replace("px", "")),
                        "color": COLORS["text"],
                    },
                    "tickfont": {
                        "family": TYPOGRAPHY["fontFamily"],
                        "size": int(TYPOGRAPHY["sizes"]["body"].replace("px", "")),
                        "color": COLORS["text"],
                    },
                    "x": -0.15,  # Move the y-axis title to the left
                    "y": 0.5,  # Center the y-axis title
                },
                "paper_bgcolor": COLORS["background"]["light"],
                "plot_bgcolor": COLORS["background"]["light"],
                "margin": {
                    "l": int(SPACING["large"].replace("px", ""))
                    + 40,  # Increased left margin
                    "r": int(SPACING["large"].replace("px", "")),
                    "t": int(SPACING["large"].replace("px", ""))
                    + 20,  # Increased top margin for subtitle
                    "b": int(SPACING["large"].replace("px", ""))
                    + 40,  # Increased bottom margin
                },
                "font": {"family": TYPOGRAPHY["fontFamily"]},
                "showlegend": True,
                "legend": {
                    "font": {
                        "family": TYPOGRAPHY["fontFamily"],
                        "size": int(TYPOGRAPHY["sizes"]["body"].replace("px", "")),
                        "color": COLORS["text"],
                    }
                },
            },
        },
        style={"margin": SPACING["large"]},
    )
