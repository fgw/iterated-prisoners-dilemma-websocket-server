import os
import base64
import io

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from pandas.errors import EmptyDataError
import numpy as np


DATA_DIR = 'tournaments'

app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("Iterative Prisoner's Dilemma Visualizer"),
    html.Div(id='graphs-container'),
    dcc.Interval(
    id='interval-component',
    interval=10*1000,  # Update every 10 seconds (adjust as needed)
    n_intervals=0
)
])

def read_csv_files_from_directory(directory):
    dfs = []
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            try:
                df = pd.read_csv(file_path, comment='#')
            except EmptyDataError:
                continue
            dfs.append((df, filename))
    # TODO: Order files by datetime desc
    return dfs

def calculate_scores(df):
    # Define scoring rules (C,C -> 3 points each; C,B -> 0 points for C; B,C -> 5 points for B; B,B -> 1 point each)
    scoring_matrix = [
        # C      B    
        [(3, 3), (5, 0)], # C
        [(0, 5), (1, 1)] # B
    ]

    scores = [[], []]
    cumulative_scores = [0, 0] 

    for index, row in df.iterrows():
        if row[df.columns[0]] == 'C' and row[df.columns[1]] == 'C':
            cumulative_scores[0] += scoring_matrix[0][0][0]
            cumulative_scores[1] += scoring_matrix[0][0][1]
        elif row[df.columns[0]] == 'C' and row[df.columns[1]] == 'B':
            cumulative_scores[0] += scoring_matrix[1][0][0]
            cumulative_scores[1] += scoring_matrix[1][0][1]
        elif row[df.columns[0]] == 'B' and row[df.columns[1]] == 'C':
            cumulative_scores[0] += scoring_matrix[0][1][0]
            cumulative_scores[1] += scoring_matrix[0][1][1]
        elif row[df.columns[0]] == 'B' and row[df.columns[1]] == 'B':
            cumulative_scores[0] += scoring_matrix[1][1][0]
            cumulative_scores[1] += scoring_matrix[1][1][1]
        
        # TODO: Handle forfeits

        scores[0].append(cumulative_scores[0])
        scores[1].append(cumulative_scores[1])

    return scores

@app.callback(
    Output('graphs-container', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_output(n):
    dfs = read_csv_files_from_directory(DATA_DIR)

    if not dfs:
        return "No CSV files found.", {}

    graphs = []

    for df, filename in dfs:
        a_name, b_name = df.columns
        # Remove '.csv'
        tournament_uuid = filename[:-4]

        scores = calculate_scores(df)

        score_fig = {
                        'data': [
                            {'x': list(range(len(scores[0]))), 'y': scores[0], 'type': 'line', 'name': a_name},
                            {'x': list(range(len(scores[1]))), 'y': scores[1], 'type': 'line', 'name': b_name}
                        ],
                        'layout': {
                            'title': f'Score Progression {tournament_uuid}: {a_name} vs {b_name}',
                            'xaxis': {'title': 'Iterations'},
                            'yaxis': {'title': 'Cumulative Score'},
                        }
                    }

        graphs.append(dcc.Graph(figure=score_fig))

        # Convert choices to numerical values: C -> 1, B -> 0
        choice_matrix = df.replace({'C': 1.0, 'B': 0.0, 'Forfeit': 0.5}).values
        # Transpose to show better
        choice_matrix = choice_matrix.T

        # Create a heatmap using go.Heatmap
        choice_fig = go.Figure(data=go.Heatmap(
            z=choice_matrix,
            colorscale=[[0, 'red'], [0.5, 'gray'], [1, 'blue']],  # Red for B (0), Blue for C (1)
            zmin=0,
            zmax=1,
            colorbar=dict(
                title='Choices',
                tickvals=[0, 0.5, 1],
                ticktext=['B', 'Forfeit', 'C']  # Custom tick labels for the color scale
            )
        ))
        
        # Set axis titles
        choice_fig.update_layout(
            title=f'Choices Heatmap {tournament_uuid}: {a_name} vs {b_name}',
            xaxis_title='Rounds',
            yaxis_title='Participants',
            yaxis=dict(tickvals=np.arange(len(df.columns)), ticktext=df.columns)  # Set y-axis labels to participant names
        )

        graphs.append(dcc.Graph(figure=choice_fig))  # Add each figure to the list of graphs

    return graphs

if __name__ == '__main__':
    app.run_server(debug=True)