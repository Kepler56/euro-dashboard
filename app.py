import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

##################################################################
### Configure App
##################################################################

st.set_page_config(
    page_title="The UEFA Euro", 
    layout="wide", 
    page_icon="./public/euro_trophy_icon.png",
    initial_sidebar_state="collapsed"
)

##################################################################
### Variables
##################################################################
DATA_FILE_PATH = "./data/"
IMAGES_FILE_PATH = "./public/"

rounds = [
    'Group stage', 
    'Round of 16', 
    'Quarter-finals', 
    'Semi-finals', 
    'Final'
]

euro_year = {
    2000: '#7697C2',
    2004: '#F37121',
    2008: '#196C23',
    2012: '#401236',
    2016: '#002054',
    2020: '#00AEC3'
}

##################################################################
### Data
##################################################################

@st.cache_data
def fetchData(file_path):
    df = pd.read_csv(file_path)
    return df

df_euro_seasons = fetchData(DATA_FILE_PATH + "euro_seasons.csv")

##################################################################
### Methods
##################################################################

def getGeneralInformation(df, year, field):
    return df[df['Year'] == year][field].iloc[0]

def getTimeline(year, data_file_path):
    df_group_stage = fetchData(f"{data_file_path}EURO {year}/euro_season_{year}_group_stage.csv")
    start_date = df_group_stage.loc[0, 'Date']
    df_ko_stage = fetchData(f"{data_file_path}EURO {year}/euro_season_{year}_ko_stage.csv")
    end_date = df_ko_stage.iloc[-1]['Date']
    timeline = f"{start_date} - {end_date}"
    return timeline

def getLeagueTableTotalInformation(year, data_file_path, field):
    df_total = fetchData(f"{data_file_path}EURO {year}/euro_season_{year}_league_table.csv")
    return df_total.loc[df_total['Nation'] == 'Total', field].loc[0]

def getLeagueTableInformation(selected_year, field, field_text, field_color, image_path):
    script = """<div id = 'chat_outer'></div>"""
    st.markdown(script, unsafe_allow_html=True)
    with st.container():
        script = """<div id = 'chat_inner'></div>"""
        st.markdown(script, unsafe_allow_html=True)
        st.markdown(f'<h5 style="color:{field_color};">Country with most {field_text}</h5>', unsafe_allow_html=True)
        right, left = st.columns(2)
        with right:
            df_league_table = fetchData(f"{DATA_FILE_PATH}EURO {selected_year}/euro_season_{selected_year}_league_table.csv")
            df_league_table = df_league_table[df_league_table['Nation'] != 'Total']
            max_element = df_league_table.loc[df_league_table[field].idxmax()]
            st.subheader(max_element.loc[field])
        with left:
            st.markdown(f'<h5 style="color:black;">{max_element.loc['Nation']}</h5>', unsafe_allow_html=True)
            if image_path != 'None':    
                st.image(f"{IMAGES_FILE_PATH}{image_path}", width=50)

def getFinalResult(year, data_file_path):
    df_ko_stage = fetchData(f"{data_file_path}EURO {year}/euro_season_{year}_ko_stage.csv")
    final_result = df_ko_stage.loc[df_ko_stage['Round'] == 'Final', 'Score'].iloc[0]
    home_team = df_ko_stage.loc[df_ko_stage['Round'] == 'Final', 'Home'].iloc[0]
    away_team = df_ko_stage.loc[df_ko_stage['Round'] == 'Final', 'Away'].iloc[0]
    return home_team, final_result, away_team

def getResultsByRound(selected_round, selected_year):
    if selected_round == "Group stage":
        df = fetchData(f"{DATA_FILE_PATH}EURO {selected_year}/euro_season_{selected_year}_group_stage.csv")[['Day', 'Date', 'Time', 'Home', 'Score', 'Away', 'Attendance', 'Venue', 'Referee']]
    else:
        df = fetchData(f"{DATA_FILE_PATH}EURO {selected_year}/euro_season_{selected_year}_ko_stage.csv")
        df = df[df['Round'] == selected_round][['Day', 'Date', 'Time', 'Home', 'Score', 'Away', 'Attendance', 'Venue', 'Referee']]
    max_attendance = df['Attendance'].max()
    styled_df = df.style.apply(highlightWinnersAndLosers, axis=1).apply(lambda row: highlightMostAttended(row, max_attendance), axis=1)
    st.dataframe(styled_df) 

def displaySimpleMetricsCards(df, method, year, field, text, icon_name):
    script = """<div id = 'chat_outer'></div>"""
    st.markdown(script, unsafe_allow_html=True)
    with st.container():
        script = """<div id = 'chat_inner'></div>"""
        st.markdown(script, unsafe_allow_html=True)
        right, left = st.columns(2)
        with right:
            if method == 'General Info':
                metric = getGeneralInformation(df, year, field)
            elif method == "League Table Info":
                metric = getLeagueTableTotalInformation(year, DATA_FILE_PATH, field)
            st.subheader(metric)
            st.markdown(text)
        with left:
            st.image(f"{IMAGES_FILE_PATH}{icon_name}")

def parseScore(score):
    pattern = r'\((\d+)\) (\d+)–(\d+) \((\d+)\)'
    match = re.match(pattern, score)
    if match:
        home_pen, home_goals, away_goals, away_pen = map(int, match.groups())
    else:
        home_pen, away_pen = 0, 0
        home_goals, away_goals = map(int, score.split('–'))
    return home_goals, away_goals, home_pen, away_pen

def highlightWinnersAndLosers(row):
    home, score, away = row['Home'], row['Score'], row['Away']
    home_goals, away_goals, home_pen, away_pen = parseScore(score)
    
    if home_goals > away_goals or (home_goals == away_goals and home_pen > away_pen):
        return ['', '', '', 'background-color: green', '', 'background-color: red', '', '', '']
    elif home_goals < away_goals or (home_goals == away_goals and away_pen > home_pen):
        return ['', '', '', 'background-color: red', '', 'background-color: green', '', '', '']
    else:
        return ['', '', '', 'background-color: grey', '', 'background-color: grey', '', '', '']

def highlightMostAttended(row, max_attendance):
    if row['Attendance'] == max_attendance:
        return ['', '', '', '', '', '', 'background-color: yellow', 'background-color: yellow', '']
    else:
        return [''] * 9

def plotBarChart(df):
    fig = go.Figure(
        data=[
            go.Bar(x=df.Nation, y=df.W, name="Win"),
            go.Bar(x=df.Nation, y=df.L, name="Loss"),
            go.Bar(x=df.Nation, y=df.D, name="Draw"),
        ],
        layout=dict(
            bargap=0.2,
            barmode='group',
        ),
    )

    fig.update_layout(
        xaxis_title="Nations",
        yaxis_title="Number of Matches",
        legend_title="Result",
        bargroupgap=0.1,
    )

    return fig
    
##################################################################
### Sidebar
##################################################################
with st.sidebar:
    st.title(':date: EURO year')
    
    year_list = list()
    selected_year = st.selectbox('Select a year', list(euro_year.keys()))
    background_color = euro_year[selected_year]


##################################################################
### Main App
##################################################################
st.title(f"EURO {selected_year}")
css_styles = f"""
        <style>
            .stApp {{
                background-color: {background_color};
            }}
            div[data-testid='stVerticalBlock']:has(div#chat_inner):not(:has(div#chat_outer)){{
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                padding: 1em 0.5em;
                border-radius: 10px;
                box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
            }}
            div[data-testid='stVerticalBlock']:has(div#chat_inner):not(:has(div#chat_outer)) p, h3{{
                color: #000000;
            }}
        </style>
        """

st.markdown(
        css_styles,
        unsafe_allow_html=True
    )

########## First line - 3 columns - General info | Winner | Individual results ##########
first_row_cols = st.columns([0.5,0.25,0.25])

# GENERAL INFO
with first_row_cols[0]:
    general_info_container = st.container()
    script = """<div id = 'chat_outer'></div>"""
    st.markdown(script, unsafe_allow_html=True)
    with general_info_container:
        script = """<div id = 'chat_inner'></div>"""
        st.markdown(script, unsafe_allow_html=True)
        right, left = st.columns(2)
        with right:
            image_url = getGeneralInformation(df_euro_seasons, selected_year, 'Logos URL')
            st.image(image_url, use_column_width=True)
        with left:
            host_countries = getGeneralInformation(df_euro_seasons, selected_year, 'Host Country')
            total_revenue = getGeneralInformation(df_euro_seasons, selected_year, 'Total revenue (in million euros)')
            number_of_squads = getGeneralInformation(df_euro_seasons, selected_year, "# Squads")
            timeline = getTimeline(selected_year, DATA_FILE_PATH)
            st.markdown(f'Host Countries: **{host_countries}**')
            st.markdown(f'Total Revenue (in million): **{total_revenue}€**')
            st.markdown(f'Number of squads: **{number_of_squads}**')
            st.markdown(f'Timeline: **{timeline}**')
            
# WINNER 
with first_row_cols[1]:
    winner_info_container = st.container()
    script = """<div id = 'chat_outer'></div>"""
    st.markdown(script, unsafe_allow_html=True)
    with winner_info_container:
        script = """<div id = 'chat_inner'></div>"""
        st.markdown(script, unsafe_allow_html=True)
        right, left = st.columns(2)
        with right:
            winner = getGeneralInformation(df_euro_seasons, selected_year, 'Champion') 
            winner_flag = getGeneralInformation(df_euro_seasons, selected_year, 'Champion Flag') 
            st.image(winner_flag, width=30)
            st.markdown(f'<h3 style="color: gold;">{winner}</h3>', unsafe_allow_html=True)
        with left:
            st.image(f"{IMAGES_FILE_PATH}euro_trophy_icon.png", width=70)   
        winner_coach = getGeneralInformation(df_euro_seasons, selected_year, 'Winning coach')
        home, result, away = getFinalResult(selected_year, DATA_FILE_PATH)
        st.markdown(f'Final Result:', unsafe_allow_html=True)
        st.markdown(f'{home} (**{result}**) {away}', unsafe_allow_html=True)
        st.markdown(f"Coach: **{winner_coach}**") 
            
# INDIVIDUAL RESULTS
with first_row_cols[2]:
    winner_info_container = st.container()
    script = """<div id = 'chat_outer'></div>"""
    st.markdown(script, unsafe_allow_html=True)
    with winner_info_container:
        script = """<div id = 'chat_inner'></div>"""
        st.markdown(script, unsafe_allow_html=True)
        right, left = st.columns(2)
        with right:
            player_of_the_tournament = getGeneralInformation(df_euro_seasons, selected_year, 'Player of the Tournament') 
            st.markdown(f'Best player: **{player_of_the_tournament}**', unsafe_allow_html=True)
            st.image(f'{IMAGES_FILE_PATH}golden_boot.png', width=50)
        with left:
            player_of_the_tournament_flag = getGeneralInformation(df_euro_seasons, selected_year, 'Player of the tournament flag') 
            top_scorers_goals_scored = getGeneralInformation(df_euro_seasons, selected_year, 'Top Scorer Number of Goals')
            st.image(winner_flag, width=80) 
            st.markdown(f'<h4 style="color: green;">Goals: {top_scorers_goals_scored}</h4>',  unsafe_allow_html=True)
        goal_scorers = getGeneralInformation(df_euro_seasons, selected_year, 'Top Scorer Names') 
        st.markdown(f'**{goal_scorers}**', unsafe_allow_html=True)
            
########## Second line - 4 columns - Matches | Goals | Yellow Cards | Red cards ##########
second_row_cols = st.columns(4)

# MATCHES
with second_row_cols[0]:
    displaySimpleMetricsCards(df_euro_seasons, 'General Info', selected_year, 'Matches', "Total games played", "football_pitch.png")
    
# GOALS
with second_row_cols[1]:
    displaySimpleMetricsCards(df_euro_seasons, 'League Table Info',  selected_year, 'GF', "Total goals scored", "football.png")

# YELLOW CARDS
with second_row_cols[2]:
    displaySimpleMetricsCards(df_euro_seasons, 'League Table Info',  selected_year, 'YC', "Yellow cards given", "yellow_card.png")
    
# RED CARDS
with second_row_cols[3]:
    displaySimpleMetricsCards(df_euro_seasons, 'League Table Info',  selected_year, 'RC', "Red cards given", "red_card.png")
    
########## Third line - 2 columns - Euro Results | Most (yellow cards, red cards) ##########
third_row_cols = st.columns([0.2, 0.8])

# EURO RESULTS
with third_row_cols[0]:
    with st.container():
        selected_round = st.selectbox('Select a round', rounds)

third_row_cols_bis = st.columns([0.8, 0.2])
with third_row_cols_bis[0]:
    getResultsByRound(selected_round, selected_year)
        
# TEAM RESULTS (goals scored, goals conceded, clean sheets)
with third_row_cols_bis[1]:
    # Yellow cards
    getLeagueTableInformation(selected_year, 'YC', 'yellow cards', 'yellow', 'None')
    
    # Red cards
    getLeagueTableInformation(selected_year, 'RC', 'red cards', 'red', 'None')

########## Fourth line - 2 columns - Team results (win, loss, draw) |   Team results (goals scored, goals conceded, clean sheets)##########
fourth_row_cols = st.columns([0.6, 0.3])
with fourth_row_cols[0]:
    loss_win_draw_plot = st.container()
    with loss_win_draw_plot:
        st.header("Country results 📊")
        df_league_table = fetchData(f"{DATA_FILE_PATH}EURO {selected_year}/euro_season_{selected_year}_league_table.csv")
        fig = plotBarChart(df_league_table[df_league_table['Nation'] != 'Total'])
        st.plotly_chart(fig)

with fourth_row_cols[1]:
    # Goals scored
    getLeagueTableInformation(selected_year, 'GF', 'goals scored', 'green', 'goal_scored.webp')
    
    # Goals conceded
    getLeagueTableInformation(selected_year, 'GA', 'goals conceded', 'red', 'goal_conceded.jpg')
    
    # Clean sheets
    getLeagueTableInformation(selected_year, 'CS', 'clean sheets', 'black', 'goal_gloves.jpg')
    