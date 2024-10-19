import os
import base64
import io

import dash
from dash import dcc, html, Input, Output
import pandas as pd
from pandas.errors import EmptyDataError


DATA_DIR = 'tournaments'

app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("Iterative Prisoner's dilemma Visualizer"),
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

        scores = calculate_scores(df)

        score_fig = {
                        'data': [
                            {'x': list(range(len(scores[0]))), 'y': scores[0], 'type': 'line', 'name': a_name},
                            {'x': list(range(len(scores[1]))), 'y': scores[1], 'type': 'line', 'name': b_name}
                        ],
                        'layout': {
                            # Remove '.csv'
                            'title': f'Score Progression {filename[:-4]}: {a_name} vs {b_name}',
                            'xaxis': {'title': 'Iterations'},
                            'yaxis': {'title': 'Cumulative Score'},
                        }
                    }

        graphs.append(dcc.Graph(figure=score_fig))

        # TODO: Plot choices

    return graphs

if __name__ == '__main__':
    app.run_server(debug=True)