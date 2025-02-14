import requests
from bs4 import BeautifulSoup

def fetch_player_stats(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    player_stats = soup.find_all('div', class_='stats')
    for stat in player_stats:
        print(stat.text)

if __name__ == '__main__':
    url = 'https://www.basketball-reference.com/players/j/jamesle01.html'
    print(fetch_player_stats(url))