
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Fantasy Football Analytics",
    page_icon="🏈",
    layout="wide"
)

# Title
st.title("🏈 Fantasy Football Analytics Dashboard")

# Load data
@st.cache_data
def load_data():
    try:
        rosters_df = pd.read_csv('rosters_csv/master_rosters.csv')
        scoreboard_df = pd.read_csv('weekly_scoreboard_csv/master_scoreboard.csv')
        return rosters_df, scoreboard_df
    except FileNotFoundError as e:
        st.error(f"Could not load data files: {e}")
        return None, None

rosters_df, scoreboard_df = load_data()

if rosters_df is not None and scoreboard_df is not None:
    # Sidebar for filtering
    st.sidebar.header("Filters")
    
    # Get unique teams for filtering
    teams = sorted(scoreboard_df['manager_nickname'].unique())
    selected_teams = st.sidebar.multiselect(
        "Select Teams",
        teams,
        default=teams[:5] if len(teams) > 5 else teams
    )
    
    # Week range filter
    max_week = int(scoreboard_df['week'].max())
    week_range = st.sidebar.slider(
        "Week Range",
        1, max_week,
        (1, max_week)
    )
    
    # Filter data
    filtered_scoreboard = scoreboard_df[
        (scoreboard_df['manager_nickname'].isin(selected_teams)) &
        (scoreboard_df['week'].between(week_range[0], week_range[1]))
    ]
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["Team Performance", "Position Analysis", "Player Usage", "Head-to-Head"])
    
    with tab1:
        st.header("Team Performance Over Time")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Points scored per week
            st.subheader("Points Scored by Week")
            fig_points = px.line(
                filtered_scoreboard,
                x='week',
                y='team_points',
                color='manager_nickname',
                title="Team Points by Week",
                markers=True
            )
            fig_points.update_layout(height=400)
            st.plotly_chart(fig_points, use_container_width=True)
        
        with col2:
            # Win percentage over time
            st.subheader("Cumulative Win Percentage")
            
            # Calculate cumulative wins
            win_data = []
            for team in selected_teams:
                team_data = filtered_scoreboard[filtered_scoreboard['manager_nickname'] == team].sort_values('week')
                team_data['wins'] = (team_data['winner_team_key'] == team_data['team_key']).astype(int)
                team_data['cumulative_wins'] = team_data['wins'].cumsum()
                team_data['games_played'] = range(1, len(team_data) + 1)
                team_data['win_percentage'] = (team_data['cumulative_wins'] / team_data['games_played']) * 100
                win_data.append(team_data[['week', 'manager_nickname', 'win_percentage']])
            
            if win_data:
                win_df = pd.concat(win_data)
                fig_wins = px.line(
                    win_df,
                    x='week',
                    y='win_percentage',
                    color='manager_nickname',
                    title="Cumulative Win Percentage",
                    markers=True
                )
                fig_wins.update_layout(height=400, yaxis_title="Win Percentage (%)")
                st.plotly_chart(fig_wins, use_container_width=True)
        
        # Points distribution
        st.subheader("Points Distribution")
        fig_box = px.box(
            filtered_scoreboard,
            x='manager_nickname',
            y='team_points',
            title="Points Distribution by Team"
        )
        fig_box.update_xaxes(tickangle=45)
        st.plotly_chart(fig_box, use_container_width=True)
    
    with tab2:
        st.header("Position Analysis")
        
        if rosters_df is not None:
            # Filter rosters data
            filtered_rosters = rosters_df[
                (rosters_df['manager_name'].isin(selected_teams)) &
                (rosters_df['week'].between(week_range[0], week_range[1]))
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Position usage by team
                st.subheader("Position Usage by Team")
                position_counts = filtered_rosters.groupby(['manager_name', 'roster_position']).size().reset_index(name='count')
                
                fig_pos = px.bar(
                    position_counts,
                    x='manager_name',
                    y='count',
                    color='roster_position',
                    title="Position Usage by Team",
                    barmode='stack'
                )
                fig_pos.update_xaxes(tickangle=45)
                st.plotly_chart(fig_pos, use_container_width=True)
            
            with col2:
                # Position distribution pie chart
                st.subheader("Overall Position Distribution")
                overall_positions = filtered_rosters['roster_position'].value_counts()
                
                fig_pie = px.pie(
                    values=overall_positions.values,
                    names=overall_positions.index,
                    title="Position Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab3:
        st.header("Player Usage Analysis")
        
        if rosters_df is not None:
            # Most used players
            st.subheader("Most Frequently Rostered Players")
            player_usage = filtered_rosters['full_name'].value_counts().head(20)
            
            fig_usage = px.bar(
                x=player_usage.index,
                y=player_usage.values,
                title="Top 20 Most Rostered Players",
                labels={'x': 'Player', 'y': 'Times Rostered'}
            )
            fig_usage.update_xaxes(tickangle=45)
            st.plotly_chart(fig_usage, use_container_width=True)
            
            # Team usage over time
            st.subheader("Team Representation")
            if 'team_abbr' in filtered_rosters.columns:
                team_usage = filtered_rosters['team_abbr'].value_counts().head(15)
                
                fig_teams = px.bar(
                    x=team_usage.index,
                    y=team_usage.values,
                    title="Most Represented NFL Teams",
                    labels={'x': 'NFL Team', 'y': 'Players Rostered'}
                )
                st.plotly_chart(fig_teams, use_container_width=True)
    
    with tab4:
        st.header("Head-to-Head Analysis")
        
        # Create matchup matrix
        st.subheader("Head-to-Head Win Matrix")
        
        # Create win matrix
        matchups = filtered_scoreboard.copy()
        win_matrix = pd.DataFrame(index=selected_teams, columns=selected_teams, data=0)
        
        for _, row in matchups.iterrows():
            week_matchups = matchups[
                (matchups['week'] == row['week']) & 
                (matchups['matchup_id'] == row['matchup_id'])
            ]
            
            if len(week_matchups) == 2:
                team1 = week_matchups.iloc[0]
                team2 = week_matchups.iloc[1]
                
                if team1['manager_nickname'] in selected_teams and team2['manager_nickname'] in selected_teams:
                    winner = team1['manager_nickname'] if team1['team_points'] > team2['team_points'] else team2['manager_nickname']
                    loser = team2['manager_nickname'] if winner == team1['manager_nickname'] else team1['manager_nickname']
                    
                    win_matrix.loc[winner, loser] += 1
        
        # Convert to numeric and create heatmap
        win_matrix = win_matrix.astype(int)
        
        fig_heatmap = px.imshow(
            win_matrix.values,
            x=win_matrix.columns,
            y=win_matrix.index,
            color_continuous_scale='RdYlBu_r',
            title="Head-to-Head Wins (Row beats Column)",
            text_auto=True
        )
        fig_heatmap.update_xaxes(tickangle=45)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Average points against each opponent
        st.subheader("Average Points in Head-to-Head Matchups")
        h2h_points = []
        
        for _, row in matchups.iterrows():
            week_matchups = matchups[
                (matchups['week'] == row['week']) & 
                (matchups['matchup_id'] == row['matchup_id'])
            ]
            
            if len(week_matchups) == 2:
                team1 = week_matchups.iloc[0]
                team2 = week_matchups.iloc[1]
                
                if team1['manager_nickname'] in selected_teams and team2['manager_nickname'] in selected_teams:
                    h2h_points.append({
                        'team': team1['manager_nickname'],
                        'opponent': team2['manager_nickname'],
                        'points': team1['team_points']
                    })
                    h2h_points.append({
                        'team': team2['manager_nickname'],
                        'opponent': team1['manager_nickname'],
                        'points': team2['team_points']
                    })
        
        if h2h_points:
            h2h_df = pd.DataFrame(h2h_points)
            avg_h2h = h2h_df.groupby(['team', 'opponent'])['points'].mean().reset_index()
            
            fig_h2h = px.bar(
                avg_h2h,
                x='opponent',
                y='points',
                color='team',
                title="Average Points Against Each Opponent",
                barmode='group'
            )
            fig_h2h.update_xaxes(tickangle=45)
            st.plotly_chart(fig_h2h, use_container_width=True)

    # Summary stats
    st.header("📊 Season Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_points = filtered_scoreboard['team_points'].mean()
        st.metric("Average Points", f"{avg_points:.1f}")
    
    with col2:
        max_points = filtered_scoreboard['team_points'].max()
        top_scorer = filtered_scoreboard[filtered_scoreboard['team_points'] == max_points]['manager_nickname'].iloc[0]
        st.metric("Highest Score", f"{max_points:.1f}", f"by {top_scorer}")
    
    with col3:
        total_games = len(filtered_scoreboard) // 2
        st.metric("Total Games", total_games)
    
    with col4:
        weeks_played = filtered_scoreboard['week'].nunique()
        st.metric("Weeks Played", weeks_played)

else:
    st.error("Could not load the required CSV files. Please make sure 'rosters_csv/master_rosters.csv' and 'weekly_scoreboard_csv/master_scoreboard.csv' exist.")
    st.info("Run the CSV conversion scripts first to generate the required files.")
