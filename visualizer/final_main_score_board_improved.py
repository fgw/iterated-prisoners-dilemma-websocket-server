import os
import base64
import io
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from pandas.errors import EmptyDataError
import numpy as np
import re

# Define directory paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
DATA_DIR = os.path.join(parent_dir, "tournaments")

# Initialize Dash app
app = dash.Dash(__name__)

def extract_participants(file_path):
    """
    Safely extract participants from CSV file header comments
    Returns tuple of (participant_list, is_completed)
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            participants = []
            is_completed = False
            
            for line in lines:
                if line.startswith('# Participants:'):
                    # Extract participants using regex to handle malformed brackets
                    match = re.search(r'\[(.*?)\]', line)
                    if match:
                        participants = [p.strip() for p in match.group(1).split(',')]
                elif line.strip() == '# COMPLETED':
                    is_completed = True
                    
            return participants, is_completed
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return [], False

def safe_read_csv(file_path):
    """
    Safely read CSV content handling various error cases and malformed data
    """
    try:
        # Read CSV skipping comment lines
        df = pd.read_csv(file_path, comment='#')
        
        # Validate move format
        valid_moves = {'C', 'B', 'Forfeit'}
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x if str(x).strip() in valid_moves else 'Forfeit')
            
        return df
    except EmptyDataError:
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return pd.DataFrame()

def calculate_scores(df):
    """
    Calculate scores for each player based on their moves
    Includes handling for forfeits and invalid moves
    """
    scoring_matrix = [
        [(1, 1), (3, 0)],  # CC, CB
        [(0, 3), (2, 2)]   # BC, BB
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
            cumulative_scores[0] += scoring_matrix[0][1][0]
            cumulative_scores[1] += scoring_matrix[0][1][1]
        elif row[df.columns[0]] == 'B' and row[df.columns[1]] == 'C':
            cumulative_scores[0] += scoring_matrix[1][0][0]
            cumulative_scores[1] += scoring_matrix[1][0][1]
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

def calculate_choice_stats(df):
    """
    Calculate statistics for player choices (B, C, Forfeit)
    """
    stats = {}
    for col in df.columns:
        total_moves = len(df[col])
        b_count = len(df[df[col] == 'B'])
        c_count = len(df[df[col] == 'C'])
        forfeit_count = len(df[df[col] == 'Forfeit'])
        
        b_percentage = (b_count / total_moves * 100) if total_moves > 0 else 0
        c_percentage = (c_count / total_moves * 100) if total_moves > 0 else 0
        
        stats[col] = {
            'total_rounds': total_moves,
            'b_count': b_count,
            'c_count': c_count,
            'forfeit_count': forfeit_count,
            'b_percentage': round(b_percentage, 2),
            'c_percentage': round(c_percentage, 2)
        }
    return stats

def calculate_total_rankings(directory):
    """
    Calculate total rankings across all tournaments for each group
    Includes tournament count and average scores
    """
    total_scores = {}
    tournament_counts = {}
    
    # Process all CSV files
    for filename in os.listdir(directory):
        if not filename.endswith('.csv'):
            continue
            
        file_path = os.path.join(directory, filename)
        participants, is_completed = extract_participants(file_path)
        
        # Skip incomplete tournaments
        if not is_completed:
            continue
            
        df = safe_read_csv(file_path)
        if df.empty:
            continue
            
        # Calculate scores for this tournament
        scores = calculate_scores(df)
        
        # Add scores to total for each participant
        for i, player in enumerate(df.columns):
            if player not in total_scores:
                total_scores[player] = 0
                tournament_counts[player] = 0
            total_scores[player] += scores[i][-1] if scores[i] else 0
            tournament_counts[player] += 1
    
    # Create rankings DataFrame
    rankings_data = []
    for player, score in total_scores.items():
        rankings_data.append({
            'Player': player,
            'Total Score': score,
            'Tournaments Played': tournament_counts[player],
            'Average Score': round(score / tournament_counts[player], 2)
        })
    
    rankings_df = pd.DataFrame(rankings_data)
    rankings_df = rankings_df.sort_values('Total Score', ascending=True)
    return rankings_df

def read_csv_files_from_directory(directory):
    """
    Read all CSV files from directory with error handling
    """
    dfs = []
    for filename in os.listdir(directory):
        if not filename.endswith('.csv'):
            continue
            
        file_path = os.path.join(directory, filename)
        participants, is_completed = extract_participants(file_path)
        df = safe_read_csv(file_path)
        
        if not df.empty:
            dfs.append((df, filename))
    return dfs

# Define app layout with rankings and tournament details
app.layout = html.Div([
    html.H1("Tournament Dashboard"),
    
    # Rankings Section
    html.Div([
        html.H2("Overall Rankings"),
        html.Table(id='rankings-table', className='score-table')
    ], className='leaderboard-container'),
    
    # Individual Tournament Scores Section
    html.Div([
        html.H2("Individual Tournament Scores"),
        html.Table(id='score-table', className='score-table')
    ], className='leaderboard-container'),
    
    # Graphs Container
    html.Div(id='graphs-container'),
    
    # Update Interval
    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    )
])

@app.callback(
    Output('rankings-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_rankings_table(n):
    """
    Update the rankings table with latest total scores
    """
    rankings_df = calculate_total_rankings(DATA_DIR)
    
    header = html.Thead([
        html.Tr([
            html.Th("Rank"),
            html.Th("Player"),
            html.Th("Total Years in Jail"),
            html.Th("Tournaments Played"),
            html.Th("Average Years in a Round")
        ])
    ])
    
    rows = []
    for rank, (idx, row) in enumerate(rankings_df.iterrows(), 1):
        rows.append(html.Tr([
            html.Td(rank),
            html.Td(row['Player']),
            html.Td(row['Total Score']),
            html.Td(row['Tournaments Played']),
            html.Td(row['Average Score'])
        ]))
    
    return [header, html.Tbody(rows)]

@app.callback(
    Output('score-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_score_table(n):
    """
    Update the individual tournament scores table
    """
    dfs = read_csv_files_from_directory(DATA_DIR)
    if not dfs:
        return [html.Tr([html.Td("No active games")])]
    
    header = html.Thead([
        html.Tr([
            html.Th("Tournament"),
            html.Th("Player"),
            html.Th("Each Player Years in Jail"),
            html.Th("B Count"),
            html.Th("C Count"),
            html.Th("B %"),
            html.Th("C %"),
            html.Th("Iteration"),
            html.Th("Two Players Total Years in Jail")  # New column
        ])
    ])
    
    rows = []
    for df, filename in dfs:
        tournament_uuid = filename[:-4]
        scores = calculate_scores(df)
        stats = calculate_choice_stats(df)
        
        # Get final scores for both players
        player_scores = [scores[0][-1] if scores[0] else 0, 
                        scores[1][-1] if scores[1] else 0]
        # Calculate total years for this tournament
        tournament_total_years = sum(player_scores)
        winning_score = min(player_scores)
        
        for i, player in enumerate(df.columns):
            score = player_scores[i]
            player_stats = stats[player]
            
            # Style for winning score
            score_style = {'backgroundColor': '#90EE90'} if score == winning_score else {}
            
            row = html.Tr([
                html.Td(tournament_uuid),
                html.Td(player),
                html.Td(score, style=score_style),
                html.Td(f"{player_stats['b_count']}"),
                html.Td(f"{player_stats['c_count']}"),
                html.Td(f"{player_stats['b_percentage']}%"),
                html.Td(f"{player_stats['c_percentage']}%"),
                html.Td(f"{player_stats['total_rounds']}"),
                # Add tournament total years - only show in first row of each tournament
                html.Td(tournament_total_years if i == 0 else "", 
                       rowSpan=2 if i == 0 else None,
                       style={'backgroundColor': '#f0f0f0'} if i == 0 else {})
            ])
            rows.append(row)
        
        # Add separator between tournaments
        rows.append(html.Tr([html.Td("", colSpan=9, style={'borderTop': '2px solid #666'})]))
    
    return [header, html.Tbody(rows)]

@app.callback(
    Output('graphs-container', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_output(n):
    """
    Update the graphs showing score progression and choice heatmaps
    """
    dfs = read_csv_files_from_directory(DATA_DIR)
    if not dfs:
        return "No CSV files found.", {}
    
    graphs = []
    for df, filename in dfs:
        a_name, b_name = df.columns
        tournament_uuid = filename[:-4]
        scores = calculate_scores(df)
        
        # Create score progression graph
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
        
        # Create choices heatmap
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

# Define custom CSS styles
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
                font-weight: bold;
            }
            .score-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .score-table tr:hover {
                background-color: #f5f5f5;
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
            
            /* Add styles for rankings */
            .rankings-row td:first-child {
                font-weight: bold;
                background-color: #f0f0f0;
            }
            
            /* Style for top 3 rankings */
            .rank-1 {
                background-color: #ffd700 !important;
            }
            .rank-2 {
                background-color: #c0c0c0 !important;
            }
            .rank-3 {
                background-color: #cd7f32 !important;
            }
            
            /* Additional responsive styles */
            @media (max-width: 768px) {
                .score-table {
                    font-size: 14px;
                }
                .score-table th, .score-table td {
                    padding: 4px;
                }
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

def validate_tournament_file(file_path):
    """
    Validate tournament file format and contents
    Returns boolean indicating if file is valid
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
            # Check if file has required headers
            if len(lines) < 3:
                return False
                
            # Validate date format in header
            if not lines[0].startswith('# 20'):
                return False
                
            # Validate participants format
            if not lines[1].startswith('# Participants:'):
                return False
                
            # If file has content, validate moves
            if len(lines) > 3:
                moves = set()
                for line in lines[3:]:
                    if line.startswith('#'):
                        continue
                    parts = line.strip().split(',')
                    if len(parts) != 2:
                        continue
                    moves.update(parts)
                
                # Check if all moves are valid
                valid_moves = {'C', 'B', 'Forfeit', ''}
                if not moves.issubset(valid_moves):
                    return False
                    
            return True
            
    except Exception:
        return False

def handle_error_gracefully(error_msg):
    """
    Handle errors gracefully and return appropriate user message
    """
    return html.Div([
        html.H3("Error", style={'color': 'red'}),
        html.P(error_msg)
    ], style={'margin': '20px', 'padding': '10px', 'border': '1px solid red'})

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tournament Dashboard Server')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-p', '--port', type=int, default=8050, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created data directory at {DATA_DIR}")
    
    # Print startup information
    print(f"Starting server in {'debug' if args.debug else 'production'} mode")
    print(f"Monitoring tournament files in: {DATA_DIR}")
    print(f"Access the dashboard at: http://{args.host}:{args.port}")
    
    try:
        # Start the server
        app.run_server(
            debug=args.debug,
            host=args.host,
            port=args.port
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        exit(1)
