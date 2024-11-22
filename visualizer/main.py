import os

import dash
from dash import dcc, html, Input, Output
import pandas as pd
from pandas.errors import EmptyDataError
from component_generator import generate_tournament_overview_table, generate_score_progression_figure
from styles import HEADER_1, HEADER_2, CONTAINER

DATA_DIR = 'tournaments'

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1("Iterative Prisoner's Dilemma Dashboard", style=HEADER_1),
        html.H2("Tournament Status Overview", style=HEADER_2),
        html.Div(id="overview-container"),
        html.Br(),
        html.H2("Tournament Breakdowns", style=HEADER_2),
        html.Div(id='graphs-container'),
        dcc.Interval(
            id='interval-component',
            interval=2.5*1000,  # Update every 10 seconds (adjust as needed)
            n_intervals=0
        )
    ], style=CONTAINER)
])

@app.callback(
    Output('overview-container', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_overview_container(n):
    components = []
    dataframes = read_csv_files_from_directory(DATA_DIR)
    components.append(generate_tournament_overview_table(dataframes))
    return components

def read_csv_files_from_directory(directory):
    tournament_dataframes = {}
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            try:
                tournament_dataframes[filename.replace(".csv", "")] = pd.read_csv(file_path, comment='#')
            except EmptyDataError:
                tournament_dataframes[filename.replace(".csv", "")] = None
                continue
    return tournament_dataframes

def calculate_scores(df):
    # Define scoring rules (C,C -> 3 points each; C,B -> 0 points for C; B,C -> 5 points for B; B,B -> 1 point each)
    scoring_matrix = [
        # C      B    
        [(3, 3), (5, 0)], # C
        [(0, 5), (1, 1)] # B
    ]

    forfeit_score = 0
    opponent_forfeitted_score = 3

    p1, p2 = df.columns
    p1, p2 = p1.strip(), p2.strip()

    # scores = [[], []]
    scores = {
        p1 : [],
        p2 : []
    }
    cumulative_scores = [0, 0] 

    for index, row in df.iterrows():
        participant_1_choice = row[df.columns[0]].strip()
        participant_2_choice = row[df.columns[1]].strip()
        if participant_1_choice == 'C' and participant_2_choice == 'C':
            cumulative_scores[0] += scoring_matrix[0][0][0]
            cumulative_scores[1] += scoring_matrix[0][0][1]
        elif participant_1_choice == 'C' and participant_2_choice == 'B':
            cumulative_scores[0] += scoring_matrix[1][0][0]
            cumulative_scores[1] += scoring_matrix[1][0][1]
        elif participant_1_choice == 'B' and participant_2_choice == 'C':
            cumulative_scores[0] += scoring_matrix[0][1][0]
            cumulative_scores[1] += scoring_matrix[0][1][1]
        elif participant_1_choice == 'B' and participant_2_choice == 'B':
            cumulative_scores[0] += scoring_matrix[1][1][0]
            cumulative_scores[1] += scoring_matrix[1][1][1]
        elif participant_1_choice == 'Forfeit' and participant_2_choice == 'Forfeit':
            cumulative_scores[0] += forfeit_score
            cumulative_scores[1] += forfeit_score
        elif participant_1_choice == 'Forfeit':
            cumulative_scores[0] += forfeit_score
            cumulative_scores[1] += opponent_forfeitted_score
        elif participant_2_choice == 'Forfeit':
            cumulative_scores[0] += opponent_forfeitted_score
            cumulative_scores[1] += forfeit_score
        else:
            app.logger.info(f"Unhandled case - p1 input:{participant_1_choice} | p2 input: {participant_2_choice}")

        scores[p1].append(cumulative_scores[0])
        scores[p2].append(cumulative_scores[1])

    return scores    

@app.callback(
    Output('graphs-container', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    tournament_dataframes = read_csv_files_from_directory(DATA_DIR)

    if not tournament_dataframes:
        return "No CSV files found.", {}

    graphs = []

    for filename, df in tournament_dataframes.items():
        if df is None:
            continue
            
        participant_1, participant_2 = df.columns
        # Remove '.csv'
        tournament_uuid = filename

        scores = calculate_scores(df)
        graphs.append(generate_score_progression_figure(tournament_uuid, scores))

        # # Convert choices to numerical values: C -> 1, B -> 0
        # choice_matrix = df.replace({'C': 1.0, 'B': 0.0, 'Forfeit': 0.5}).values
        # # Transpose to show better
        # choice_matrix = choice_matrix.T

        # # Create a heatmap using go.Heatmap
        # choice_fig = go.Figure(data=go.Heatmap(
        #     z=choice_matrix,
        #     colorscale=[[0, 'red'], [0.5, 'gray'], [1, 'blue']],  # Red for B (0), Blue for C (1)
        #     zmin=0,
        #     zmax=1,
        #     colorbar=dict(
        #         title='Choices',
        #         tickvals=[0, 0.5, 1],
        #         ticktext=['B', 'Forfeit', 'C']  # Custom tick labels for the color scale
        #     )
        # ))
        
        # # Set axis titles
        # choice_fig.update_layout(
        #     title=f'Choices Heatmap {tournament_uuid}: {participant_1} vs {participant_2}',
        #     xaxis_title='Rounds',
        #     yaxis_title='Participants',
        #     yaxis=dict(tickvals=np.arange(len(df.columns)), ticktext=df.columns)  # Set y-axis labels to participant names
        # )

        # graphs.append(dcc.Graph(figure=choice_fig))  # Add each figure to the list of graphs

    return graphs

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug',
                    action='store_true')

    args = parser.parse_args()

    app.run_server(debug=args.debug)
