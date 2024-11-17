import mysql.connector
from mysql.connector import Error
import requests
import os
from colorama import Fore, Style


# Database connection details
host = "localhost"  # Or your host (e.g., IP address or domain)
user = "root"       # Your MySQL username
password = "Example123!" # Your MySQL password
db_name = "examens_krypto"  # Name of the database you want to check/create

# Function to get the current price (used for sorting)
def get_current_price(coin):
    return coin['current_price']

# Fetch data from the API
url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
response = requests.get(url)
# SQL queries to create the tables if they do not exist
create_tables_queries = [
    """
    CREATE TABLE IF NOT EXISTS Cryptocurrencies (
        cryptocurrency_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        symbol VARCHAR(10) NOT NULL,
        max_supply BIGINT,
        circulating_supply BIGINT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS MarketData (
        marketdata_id INT AUTO_INCREMENT PRIMARY KEY,
        cryptocurrency_id INT,
        date DATETIME,
        current_price DECIMAL(18,8),
        price_change_24h DECIMAL(18,8),
        price_change_percentage_24h DECIMAL(5,2),
        total_volume BIGINT,
        FOREIGN KEY (cryptocurrency_id) REFERENCES Cryptocurrencies(cryptocurrency_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS HistoricalPrices (
        historicalprices_id INT AUTO_INCREMENT PRIMARY KEY,
        cryptocurrency_id INT,
        date DATETIME,
        price DECIMAL(18,8),
        volume BIGINT,
        FOREIGN KEY (cryptocurrency_id) REFERENCES Cryptocurrencies(cryptocurrency_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Tradepair (
        tradepair_ID INT AUTO_INCREMENT PRIMARY KEY,
        base_currency_id INT,
        quote_currency_id INT,
        current_price DECIMAL(18,8),
        volume_24h BIGINT,
        FOREIGN KEY (base_currency_id) REFERENCES Cryptocurrencies(cryptocurrency_id),
        FOREIGN KEY (quote_currency_id) REFERENCES Cryptocurrencies(cryptocurrency_id)
    );
    """
]

# Connect to MySQL
try:
    # Establish the connection
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password
    )
    cursor = connection.cursor()

    # Check if the database exists
    cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
    result = cursor.fetchone()

    if result:
        print(f"Database '{db_name}' already exists.")
    else:
        print(f"Database '{db_name}' does not exist. Creating it...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully.")

    # Use the database
    cursor.execute(f"USE {db_name}")

    # Create tables if they do not exist
    for query in create_tables_queries:
        cursor.execute(query)
        print(f"Table created or already exists.")

except Error as e:
    print(f"Error: {e}")

finally:
    # Close the connection if it's open
    if connection.is_connected():
        cursor.close()
        connection.close()

# Process the API response and insert data into MySQL
if response.status_code == 200:
    coins = response.json()
    # Sort coins in descending order
    sorted_coins = sorted(coins, key=get_current_price, reverse=True)

    # # Clear the screen (for Unix/Linux or Windows)
    # os.system('cls' if os.name == 'nt' else 'clear')
    #print("Cryptocurrencies sorted by current price (descending):")

    for index, coin in enumerate(sorted_coins, start=1):
        name = coin['name']
        symbol = coin['symbol']
        max_supply = coin.get('max_supply', 'N/A')
        circulating_supply = coin.get('circulating_supply', 'N/A')
        current_price = coin['current_price']
        price_change_percentage_24h = coin['price_change_percentage_24h']
        total_volume = coin['total_volume']
        circulating_supply = circulating_supply if circulating_supply is not None else None
        max_supply = max_supply if max_supply is not None else None
        price_change_24h = coin['price_change_24h']
        # Insert into Cryptocurrencies table
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            cursor = connection.cursor()

            # Insert into Cryptocurrencies table
            cursor.execute("""
                INSERT INTO Cryptocurrencies (name, symbol, max_supply, circulating_supply)
                VALUES (%s, %s, %s, %s)
            """, (name, symbol, max_supply, circulating_supply))

            # Get the ID of the newly inserted cryptocurrency
            cryptocurrency_id = cursor.lastrowid

            # Insert into Tradepair table - assuming the same cryptocurrency is used for both base and quote currencies (for simplicity)
            cursor.execute("""
                INSERT INTO Tradepair (base_currency_id, quote_currency_id, current_price, volume_24h)
                VALUES (%s, %s, %s, %s)
            """, (cryptocurrency_id, cryptocurrency_id, current_price, total_volume))

            # Insert into HistoricalPrices table
            cursor.execute("""
                INSERT INTO HistoricalPrices (cryptocurrency_id, price, volume)
                VALUES (%s, %s, %s)
            """, (cryptocurrency_id, current_price, total_volume))

            # Insert into MarketData table
            cursor.execute("""
                INSERT INTO MarketData (cryptocurrency_id, date, current_price, price_change_24h, price_change_percentage_24h, total_volume)
                VALUES (%s, NOW(), %s, %s, %s, %s)
            """, (cryptocurrency_id, current_price, price_change_24h, price_change_percentage_24h, total_volume))

            # Commit the changes
            connection.commit()


            print(f"{index}. Name:{Style.BRIGHT} {name}{Style.RESET_ALL}, Symbol: {symbol}, Price: ${current_price} USD, 24h Change: {price_change_percentage_24h}%, {price_change_24h} {total_volume}")

        except Error as e:
            print(f"Error inserting data: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

else:
    print(f"Error: {response.status_code}")
