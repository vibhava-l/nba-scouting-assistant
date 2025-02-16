import requests
from bs4 import BeautifulSoup
import re

def extract_table(soup, table_id):
    # Extract the table from the HTML content
    table = soup.find('table', {'id': table_id})
    if not table:
        print(f"Table with id '{table_id}' not found.")
        return None
    
    # Extract headers from the table
    headers = [header.text.strip() for header in table.find('thead').find_all('th')]

    # Extract rows from the table
    rows = []
    for row in table.find('tbody').find_all('tr'):
        # Ensure the row has data cells
        cells = row.find_all('td')
        if not cells:
            continue
        row_data = [cell.text.strip() for cell in cells]
        rows.append(row_data)

    return {'headers': headers, 'rows': rows}

def extract_player_metadata(soup):
    metadata = {}
    meta_div = soup.find('div', id='meta')
    if meta_div:
        # Extract player name
        name = meta_div.find('h1')
        if name:
            metadata['name'] = name.text.strip()

        # Extract other details by searching for specific labels
        # Note: The exact extraction depends on the page structure
        paragraphs = meta_div.find_all('p')
        for p in paragraphs:
            text = p.get_text(separator='', strip=True)
            if 'Position' in text:
                metadata['position'] = text.split(':')[1].strip()
            spans = p.find_all('span')
            if len(spans) >= 2:  # Check if this paragraph contains height and weight info
                height_text = spans[0].get_text(strip=True)
                weight_text = spans[1].get_text(strip=True)
                if '-' in height_text and weight_text.endswith('lb'):
                    metadata['height'] = height_text
                    metadata['weight'] = weight_text
                    continue
            elif len(spans) == 1:
                height_text = spans[0].get_text(strip=True)
                p_text = p.get_text(strip=True)
                metric_match = re.search(r'\d+\s*cm', p_text)
                if metric_match:
                    metadata['height'] = metric_match.group(1)
                    metadata['weight'] = height_text
                    continue
            if 'Hometown' in text:
                metadata['hometown'] = text.split(':')[1].strip()
            if 'High School' in text:
                metadata['high_school'] = text.split(':')[1].strip()
            if 'RSCI Top 100' in text:
                metadata['rsci_top_100'] = text.split(':')[1].strip()
            if 'School' in text:
                metadata['school'] = text.split(':')[1].strip()
            if 'Born' in text:
                metadata['born'] = text.split(':')[1].strip()
    else:
        print("Metadata div not found.")
    return metadata

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

    # Extract metadata (e.g. name, height, weight, etc.)
    metadata = extract_player_metadata(soup)

    # Extract the basic stats table (per game)
    per_game_stats = extract_table(soup, 'per_game')  # TODO: Continue here ...

    # Return a dictionary with extracted data
    return {
        'name': player_name,
        'headers': headers,
        'rows': rows
    }

if __name__ == '__main__':
    url = 'https://www.sports-reference.com/cbb/players/cooper-flagg-1.html'
    player_data = fetch_player_stats(url)
    if player_data:
        print("Player Name:", player_data['name'])
        print("Stats Headers:", player_data['headers'])
        print("First 3 Rows of Stats:")
        for row in player_data['rows'][:3]:
            print(row)