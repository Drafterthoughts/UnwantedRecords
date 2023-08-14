# imports
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os

# Set up the options for the Chrome driver
chrome_driver_path = os.environ.get('CHROME_DRIVER_PATH')
chrome_options = Options()
chrome_options.add_argument("--headless")

# Create a new instance of the Chrome driver with the options
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Define the URLs and table IDs to scrape
pages = [
    {
        "url": "https://fbref.com/en/comps/9/stats/Premier-League-Stats",
        "table_id": "stats_standard",
        "csv_name": "standard_stats.csv",
    },
    {
        "url": "https://fbref.com/en/comps/9/shooting/Premier-League-Stats",
        "table_id": "stats_shooting",
        "csv_name": "shooting_stats.csv",
    },
    {
        "url": "https://fbref.com/en/comps/9/passing/Premier-League-Stats",
        "table_id": "stats_passing",
        "csv_name": "passing_stats.csv",
    },
    {
        "url": "https://fbref.com/en/comps/9/defense/Premier-League-Stats",
        "table_id": "stats_defense",
        "csv_name": "defensive_actions_stats.csv",
    },
    {
        "url": "https://fbref.com/en/comps/9/playingtime/Premier-League-Stats",
        "table_id": "stats_playing_time",
        "csv_name": "playing_time_stats.csv",
    },
    {
        "url": "https://fbref.com/en/comps/9/misc/Premier-League-Stats",
        "table_id": "stats_misc",
        "csv_name": "miscellaneous_stats.csv",
    },
]


# define scraper function
def scrape_table(url, table_id):
    """
    Scrape a table from a given URL using its table_id and return the table as a pandas DataFrame.

    Parameters:
    - url (str): The URL of the webpage containing the table.
    - table_id (str): The HTML ID attribute of the table to scrape.

    Returns:
    - pd.DataFrame: A DataFrame containing the scraped table data.

    Note:
    This function assumes the use of a globally available WebDriver object named 'driver'.
    Ensure that 'driver' is properly initialized and operational before calling this function.
    """
    # Navigate to the URL
    driver.get(url)

    # Get the page source
    html_content = driver.page_source

    # Parse the content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the table with the stats
    table = soup.find("table", {"id": table_id})

    # Extract the table headers
    header_cells = table.thead.find_all("th", {"scope": "col"})
    headers = [header["data-stat"] for header in header_cells]
    headers = headers[1:]  # Skip the first header (rank)

    # Extract the rows from the table
    rows = table.find("tbody").find_all("tr")

    # Extract the data from each row
    data = []
    for row in rows:
        row_data = []
        for header in headers:
            cell = row.find("td", {"data-stat": header})
            if cell:
                row_data.append(cell.text.strip())
            else:
                row_data.append(None)
        data.append(row_data)

    # Create a pandas DataFrame with the data and headers
    df = pd.DataFrame(data, columns=headers)

    # Remove rows with missing data
    df = df.dropna()

    return df


# function to make sure data types are correct
def convert_columns_to_numeric(df):
    """
    Convert all appropriate columns in a dataframe to numeric.

    Parameters:
    - df (pd.DataFrame): The input DataFrame whose columns are to be converted.

    Returns:
    - pd.DataFrame: A DataFrame with columns converted to numeric where possible.

    Note:
    Columns that can't be converted to numeric will be left unchanged.
    """
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')
    return df


# function to extract player surnames
def extract_surname(full_name):
    """
    Extract and return the surname from a given full name.

    Parameters:
    - full_name (str): The full name from which the surname is to be extracted.

    Returns:
    - str: The extracted surname.

    Note:
    Assumes the surname is the last word in the full name. If the full name is a single word,
    it will be returned as is.
    """

    return full_name.split()[-1]


# Loop through the pages and scrape the tables
dataframes = {}
for page in pages:
    print(f"Scraping table from {page['url']}")
    df = scrape_table(page['url'], page['table_id'])
    df = convert_columns_to_numeric(df)
    dataframes[page['table_id']] = df

# Close the browser window
driver.quit()

# Access the DataFrames using the table IDs
standard_stats = dataframes['stats_standard']
shooting_stats = dataframes['stats_shooting']
passing_stats = dataframes['stats_passing']
defensive_actions_stats = dataframes['stats_defense']
playing_time_stats = dataframes['stats_playing_time']
miscellaneous_stats = dataframes['stats_misc']

# Get the current GW
GW = max(standard_stats['games'])

# 1. Players with the highest number of shots without a goal
highest_shots_no_goal = shooting_stats[shooting_stats['goals'] == 0].nlargest(1, 'shots')['shots'].values[0]
players_highest_shots_no_goal = shooting_stats[(shooting_stats['goals'] == 0) & (shooting_stats['shots'] == highest_shots_no_goal)]['player'].apply(extract_surname)

# 2. Players with highest xG without a goal
highest_xg_no_goal = standard_stats[standard_stats['goals'] == 0].nlargest(1, 'xg')['xg'].values[0]
players_highest_xg_no_goal = standard_stats[(standard_stats['goals'] == 0) & (standard_stats['xg'] == highest_xg_no_goal)]['player'].apply(extract_surname)

# 3. Players with the highest number xAG without an assist
highest_xag_no_assist = standard_stats[standard_stats['assists'] == 0].nlargest(1, 'xg_assist')['xg_assist'].values[0]
players_highest_xag_no_assist = standard_stats[(standard_stats['assists'] == 0) & (standard_stats['xg_assist'] == highest_xag_no_assist)]['player'].apply(extract_surname)

# 4. Players with the highest number of key passes (assisted_shots) without an assist
highest_kp_no_assist = passing_stats[passing_stats['assists'] == 0].nlargest(1, 'assisted_shots')['assisted_shots'].values[0]
players_highest_kp_no_assist = passing_stats[(passing_stats['assists'] == 0) & (passing_stats['assisted_shots'] == highest_kp_no_assist)]['player'].apply(extract_surname)

# 5. Players with the most passes into the penalty area (passes_into_penalty_area) without an assist
most_ppa_no_assist = passing_stats[passing_stats['assists'] == 0].nlargest(1, 'passes_into_penalty_area')['passes_into_penalty_area'].values[0]
players_most_ppa_no_assist = passing_stats[(passing_stats['assists'] == 0) & (passing_stats['passes_into_penalty_area'] == most_ppa_no_assist)]['player'].apply(extract_surname)

print(
    f"""
#DraftPL Unwanted Records: GW{GW}

Most:
⚽️Shots without a goal: {', '.join(players_highest_shots_no_goal)} ({highest_shots_no_goal})
⚽️xG without a goal: {', '.join(players_highest_xg_no_goal)} ({highest_xg_no_goal})
🗝️KPs without an assist: {', '.join(players_highest_kp_no_assist)} ({highest_kp_no_assist})
🗝️xAG without an assist: {', '.join(players_highest_xag_no_assist)} ({highest_xag_no_assist})
🗝️Accurate passes into the penalty area w/o an assist: {', '.join(players_most_ppa_no_assist)} ({most_ppa_no_assist})   
"""
)
