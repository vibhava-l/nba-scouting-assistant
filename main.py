import requests
from bs4 import BeautifulSoup, Comment
import re
from datetime import datetime
import string
import time

def extract_per_game_stats(soup):
    """
    Extracts per game stats from the given BeautifulSoup object.
    """
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
    """
    Extracts advanced stats from the given BeautifulSoup object.
    """
    # Extract the table from the HTML content
    table = soup.find('table', {'id': 'players_advanced'})
    
    # If table is not found, it may be inside an HTML comment
    if table is None:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'players_advanced' in comment:
                # Parse the comment as HTML content
                comment_soup = BeautifulSoup(comment, 'html.parser')
                table = comment_soup.find('table', id='players_advanced')
                if table:
                    break
    
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
    """
    Cleans up the player metadata by removing unwanted characters and fields.
    """
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
    """
    Extracts player metadata from the given BeautifulSoup object.
    """
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
    """
    Fetches player stats from a given URL.
    """
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

    # Extract player metadata
    metadata = extract_player_metadata(soup)

    # Extract per game stats
    per_game = extract_per_game_stats(soup)

    # Extract advanced stats
    advanced = extract_advanced_stats(soup)

    return {'metadata': metadata, 'per_game': per_game, 'advanced': advanced}

def calculate_age(born_str, reference_date=None):
    """
    Calculate age from a birth date string in the metadata and a reference date (defaults to today).
    """
    try:
        born_date = datetime.strptime(born_str, '%B %d, %Y')
    except ValueError:
        print("Failed to parse birth date:", born_str)
        return None

    if reference_date is None:
        reference_date = datetime.today()

    age = reference_date.year - born_date.year - ((reference_date.month, reference_date.day) < (born_date.month, born_date.day))
    return age

def is_player_draft_eligible(metadata, draft_year=None):
    """
    Determines draft eligibility:
    - College players (no 'born' field) are assumed eligible
    - International playesr (with a 'born' field) must be at least 19 years old as of January 1 in the draft year.
    """
    if draft_year is None:
        draft_year = datetime.today().year
    reference_date = datetime(draft_year, 1, 1)  # January 1 of the draft year

    born = metadata.get('born')
    if born:
        # International player: check age
        age = calculate_age(born, reference_date)
        return age is not None and age >= 19
    else:
        # College player: assumed eligible
        return True

def is_current_and_young(metadata, draft_year=None, max_age=25):
    """
    Determines if the player is currently active and young enough to be considered a prospect:
    - For international players (with a 'born' field), the age must be <= max_age.
    - For college players (without 'born'), we check if a 'school' field exists.
    
    Additionally, filters out female players by checking if the 'school' field mentions "women".
    """
    if draft_year is None:
        draft_year = datetime.today().year

    # Filter out female players based on 'school' field
    school = metadata.get('school', '')
    if school and 'women' in school.lower():
        return False
    
    if 'born' in metadata:
        # International player: check age
        age = calculate_age(metadata['born'], datetime(draft_year, 1, 1))
        return age is not None and age <= max_age
    else:
        # Assume a college player is current if they have a school listed.
        return bool(school)

def filter_draft_eligible_players(all_player_data, draft_year=None, max_age=25):
    """
    Combines draft eligibility and current/young filtering.
    Returns players who are:
    - Draft-eligible (per is_player_draft_eligible)'
    - Considered current and young prospects (per is_current_and_young)
    """
    eligible_players = []
    for player in all_player_data:
        metadata = player.get('metadata', {})
        if is_player_draft_eligible(metadata, draft_year) and is_current_and_young(metadata, draft_year, max_age):
            eligible_players.append(player)
    return eligible_players

def extract_college_player_urls(letter, base_url='https://www.sports-reference.com/cbb/players/'):
    """
    Given a letter (A-Z), fetches the list of player URLs for that letter from Sports Reference college players index page.
    """
    # Construct the URL for the given letter
    index_url = f"{base_url}{letter}-index.html"
    
    # Set the User-Agent in the headers to avoid 403 Forbidden error
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    # Send GET request to the URL
    response = requests.get(index_url, headers=headers)

    # Check if request was successful
    if response.status_code != 200:
        return 'Failed to fetch data: ' + response.status_code

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    player_links = []
    # Find all links to player pages
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/cbb/players/' in href and '-index' not in href:
            full_url = f"https://www.sports-reference.com{href}"
            player_links.append(full_url)

    return list(set(player_links))

def extract_international_player_urls(letter, base_url='https://www.basketball-reference.com/international/players/'):
    """
    Given a letter (A-Z), fetches the list of player URLs for that letter from Basketball Reference international players index page.
    """
    # Construct the URL for the given letter
    index_url = f"{base_url}{letter}-index.html"
    
    # Set the User-Agent in the headers to avoid 403 Forbidden error
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    # Send GET request to the URL
    response = requests.get(index_url, headers=headers)

    # Check if request was successful
    if response.status_code != 200:
        return 'Failed to fetch data: ' + response.status_code

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    player_links = []
    # Find all links to player pages
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/international/players/' in href and '-index' not in href:
            full_url = f"https://www.basketball-reference.com{href}"
            player_links.append(full_url)

    return list(set(player_links))

def crawl_all_player_urls():
    """
    Crawls all player URLs from Sports Reference and Basketball Reference.
    """
    all_urls = []
    # Extract college player URLs from Sports Reference
    for letter in string.ascii_uppercase:
        college_urls = extract_college_player_urls(letter)
        print(f"College letter {letter.upper()}: found {len(college_urls)} player URLs.")
        all_urls.extend(college_urls)
    
    # Extract international player URLs from Basketball Reference
    for letter in string.ascii_uppercase:
        international_urls = extract_international_player_urls(letter)
        print(f"International letter {letter.upper()}: found {len(international_urls)} player URLs.")
        all_urls.extend(international_urls)
    
    # Remove duplicates if any
    all_urls = list(set(all_urls))
    print(f"Total unique player URLs found: {len(all_urls)}")
    return all_urls

def process_all_players(player_urls):
    """
    Processes all player URLs to extract their stats.
    """
    all_player_data = []
    for url in player_urls:
        player_data = fetch_player_stats(url)
        if player_data:
            all_player_data.append(player_data)
        time.sleep(1)  # Add a delay to avoid overwhelming the server
    return all_player_data

if __name__ == '__main__':
    # Crawl all player URLs from both college and international sources
    all_urls = crawl_all_player_urls()
    print(f"Total unique player URLs found: {len(all_urls)}")

    # Process each player URL to extract their stats and metadata
    all_player_data = process_all_players(all_urls)
    print(f"Total player data extracted: {len(all_player_data)}")

    # Filter for players who are draft-eligible and current,young, male prospects
    eligible_players = filter_draft_eligible_players(all_player_data)
    print(f"Eligible players count: {len(eligible_players)}")

    # Print details for a few eligible players
    for player in eligible_players[:5]:
        print(f"Player Metadata", player.get('metadata'))