import requests
import os
from time import sleep
from colorama import Fore, Style

# Function to get the current price (used for sorting)
def get_current_price(coin):
    return coin['current_price']

# Fetch data from the API
url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
response = requests.get(url)


if response.status_code == 200:
    coins = response.json()
    # Sort coins in descending order
    sorted_coins = sorted(coins, key=get_current_price, reverse=True)
        # Clear the screen (for Unix/Linux or Windows)
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Cryptocurrencies sorted by current price (descending):")

    for index, coin in enumerate(sorted_coins, start=1):
        name = coin['name']
        market_cap = coin['market_cap']
        high_24h = coin['high_24h']
        low_24h = coin['low_24h']
        symbol = coin['symbol']
        total_volume = coin['total_volume']
        current_price = coin['current_price']
        max_supply = coin.get('max_supply', 'N/A')  # Handle None value for max_supply
        circulating_supply = coin.get('circulating_supply', 'N/A')  # Handle None value for circulating_supply
        price_change_procentage_24h = coin['price_change_percentage_24h']
        prince_change_USD_24h = coin ['price_change_24h']
        # Colorize percentage change (positive = green, negative = red)
        if price_change_procentage_24h > 0:
            price_change_procentage_24h = f"{Fore.GREEN}{price_change_procentage_24h}%{Style.RESET_ALL}"
        else:
            price_change_procentage_24h = f"{Fore.RED}{price_change_procentage_24h}%{Style.RESET_ALL}"

        print(f"{index}. Name:{Style.BRIGHT} {name}{Style.RESET_ALL}, Price: ${current_price} USD, Volume: {total_volume}, Max Available: {max_supply}, Circulating Supply: {circulating_supply}, 24h Change: {price_change_procentage_24h}, 24h change in USD: {prince_change_USD_24h,} {symbol}, {market_cap} USD ")
        
else:
    print(f"Error: {response.status_code}")
