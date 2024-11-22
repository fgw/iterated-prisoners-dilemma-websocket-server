import os
import base64
import io
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from pandas.errors import EmptyDataError
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
DATA_DIR = os.path.join(parent_dir, "tournaments")

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Iterative Prisoner's Dilemma Visualizer"),
    html.Div([
        html.H2("Current Scores"),
        html.Table(id='score-table', className='score-table')
    ], className='leaderboard-container'),
    html.Div(id='graphs-container'),
    dcc.Interval(
        id='interval-component',
        interval=2*1000,
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
    return dfs

def calculate_scores(df):
    scoring_matrix = [
        [(3, 3), (5, 0)],
        [(0, 5), (1, 1)]
    ]
    
    forfeit_score = 0
    opponent_forfeitted_score = 3
    
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
        elif row[df.columns[0]] == 'Forfeit' and row[df.columns[1]] == 'Forfeit':
            cumulative_scores[0] += forfeit_score
            cumulative_scores[1] += forfeit_score
        elif row[df.columns[0]] == 'Forfeit':
            cumulative_scores[0] += forfeit_score
            cumulative_scores[1] += opponent_forfeitted_score
        elif row[df.columns[1]] == 'Forfeit':
            cumulative_scores[0] += opponent_forfeitted_score
            cumulative_scores[1] += forfeit_score

        scores[0].append(cumulative_scores[0])
        scores[1].append(cumulative_scores[1])
        
    return scores

@app.callback(
    Output('score-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_score_table(n):
    dfs = read_csv_files_from_directory(DATA_DIR)
    if not dfs:
        return [html.Tr([html.Td("No active games")])]
    
    header = html.Thead([
        html.Tr([
            html.Th("Tournament"),
            html.Th("Player 1"),
            html.Th("Score"),
            html.Th("vs"),
            html.Th("Score"),
            html.Th("Player 2")
        ])
    ])
    
    rows = []
    for df, filename in dfs:
        a_name, b_name = df.columns
        tournament_uuid = filename[:-4]
        scores = calculate_scores(df)
        score_a = scores[0][-1] if scores[0] else 0
        score_b = scores[1][-1] if scores[1] else 0
        
        row = html.Tr([
            html.Td(tournament_uuid),
            html.Td(a_name),
            html.Td(score_a),
            html.Td("vs"),
            html.Td(score_b),
            html.Td(b_name)
        ])
        rows.append(row)
    
    return [header, html.Tbody(rows)]

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
        
        choice_matrix = df.replace({'C': 1.0, 'B': 0.0, 'Forfeit': 0.5}).values.T
        choice_fig = go.Figure(data=go.Heatmap(
            z=choice_matrix,
            colorscale=[[0, 'red'], [0.5, 'gray'], [1, 'blue']],
            zmin=0,
            zmax=1,
            colorbar=dict(
                title='Choices',
                tickvals=[0, 0.5, 1],
                ticktext=['B', 'Forfeit', 'C']
            )
        ))
        
        choice_fig.update_layout(
            title=f'Choices Heatmap {tournament_uuid}: {a_name} vs {b_name}',
            xaxis_title='Rounds',
            yaxis_title='Participants',
            yaxis=dict(tickvals=np.arange(len(df.columns)), ticktext=df.columns)
        )
        graphs.append(dcc.Graph(figure=choice_fig))
    
    return graphs

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .score-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .score-table th, .score-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            .score-table th {
                background-color: #f4f4f4;
            }
            .score-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .leaderboard-container {
                margin: 20px;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1, h2 {
                text-align: center;
                color: #333;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()
    app.run_server(debug=args.debug)
