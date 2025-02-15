import requests
from bs4 import BeautifulSoup

def fetch_player_stats(url):
    # Send GET request to the URL
    response = requests.get(url)

    # Check if request was successful
    if response.status_code != 200:
        return 'Failed to fetch data: ' + response.status_code

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the player's name
    player_name = soup.find('h1')
    player_name = player_name.text.strip() if player_name else 'N/A'

    # Extract per game stats table
    stats_table = soup.find('table', {'id': 'per_game_stats'})
    if stats_table:
        # Extract headers from the table
        headers = [header.text for header in stats_table.find('thead').find_all('th')]

        # Extract rows from the table
        rows = []
        for row in stats_table.find('tbody').find_all('tr'):
            # Ensure the row has data cells
            cells = row.find_all('td')
            if cells:
                row_data = [cell.text for cell in cells]
                rows.append(row_data)
    else:
        headers = []
        rows = []

    # Return a dictionary with extracted data
    return {
        'name': player_name,
        'headers': headers,
        'rows': rows
    }

if __name__ == '__main__':
    url = 'https://www.basketball-reference.com/players/j/jamesle01.html'
    player_data = fetch_player_stats(url)
    if player_data:
        print("Player Name:", player_data['name'])
        print("Stats Headers:", player_data['headers'])
        print("First 3 Rows of Stats:")
        for row in player_data['rows'][:3]:
            print(row)