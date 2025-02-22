import requests
from bs4 import BeautifulSoup
import re

def extract_per_game_stats(soup):
    # Extract the table from the HTML content
    table = soup.find('table', {'id': 'players_per_game'})
    if table:
        print("Extracting college per game stats...")
    else:
        table = soup.find('table', {'id': 'player-stats-per_game-all-'})
        if table:
            print("Extracting international per game stats...")
        else:
            print("Per game stats table not found.")
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

def extract_advanced_stats(soup):
    # Extract the table from the HTML content
    table = soup.find('table', {'id': 'players_advanced'})
    if table:
        print("Extracting college advanced stats...")
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
    else:
        print("Advanced stats table not found (likely an international prospect).")
        return None

def clean_metadata(metadata):
    # Clean up the name: remove " International Stats" suffix
    if 'name' in metadata:
        metadata['name'] = metadata['name'].replace(' International Stats', '')
    
    # Clean up the position: remove any digits, punctuation, or trailing words like 'Born'
    if 'position' in metadata:
        # This regex extracts only the alphabetical and space characters from the start.
        match = re.match(r'^([A-Za-z\s]+)', metadata['position'])
        if match:
            metadata['position'] = match.group(1).strip()
    
    # Clean up the born data: replace non-breaking spaces with normal space
    if 'born' in metadata:
        metadata['born'] = metadata['born'].replace('\xa0', ' ')
    
    return metadata

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
                p_text = p.get_text(" ", strip=True)
                metric_match = re.search(r'\((\d+\s*cm)\)', p_text)
                if metric_match:
                    metadata['height'] = height_text
                    metadata['height_metric'] = metric_match.group(1)
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
    
    # Clean the metadata before returning
    return clean_metadata(metadata)

def fetch_player_stats(url):
    # Set the User-Agent in the headers to avoid 403 Forbidden error
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    # Send GET request to the URL
    response = requests.get(url, headers=headers)

    # Check if request was successful
    if response.status_code != 200:
        return 'Failed to fetch data: ' + response.status_code

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract metadata (e.g. name, height, weight, etc.)
    metadata = extract_player_metadata(soup)

    # Extract the basic stats table (per game)
    per_game_stats = extract_per_game_stats(soup)

    # Extract the advanced stats table (only for college prospects)
    advanced_stats = extract_advanced_stats(soup)

    # Return a dictionary with extracted data
    return {
        'metadata': metadata,
        'per_game': per_game_stats,
        'advanced': advanced_stats
    }

if __name__ == '__main__':
    url = 'https://www.basketball-reference.com/international/players/michael-ruzic-1.html'
    player_data = fetch_player_stats(url)
    if player_data:
        print("Player Metadata:", player_data['metadata'])
        if player_data['per_game']:
            print("Per Game Table Headers:", player_data['per_game']['headers'])
            print("First Row of Per Game Stats:", player_data['per_game']['rows'][0] if player_data['per_game']['rows'] else "No rows found")
        if player_data['advanced']:
            print("Advanced Stats Table Headers:", player_data['advanced']['headers'])