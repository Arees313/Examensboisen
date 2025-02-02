import mysql.connector
from mysql.connector import Error
import requests
import os
from colorama import Fore, Style
import time

# Database connection details
host = "localhost"  # Or your host (e.g., IP address or domain)
user = "root"       # Your MySQL username
password = "Example123!" # Your MySQL password
db_name = "examens_db"  # Name of the database you want to check/create

# Function to get the current price (used for sorting)
def get_current_price(coin):
    return coin['current_price']

# Function to fetch data and store it in the database
def fetch_and_store_data():
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
            current_price_change_24h DECIMAL(18,8),
            current_price_change_percentage_24h DECIMAL(5,2),
            total_volume BIGINT,
            market_cap BIGINT,
            market_cap_change_24h DECIMAL(18,2),
            market_cap_change_percentage_24h DECIMAL(5,2),
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
            price_change DECIMAL(18,8),
            percentage_change DECIMAL(5,2),
            market_cap BIGINT,
            market_cap_change_24h DECIMAL(18,2),
            market_cap_change_percentage_24h DECIMAL(5,2),
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

        for index, coin in enumerate(sorted_coins, start=1):
            name = coin['name']
            symbol = coin['symbol']
            max_supply = coin.get('max_supply', 'N/A')
            circulating_supply = coin.get('circulating_supply', 'N/A')
            current_price = coin['current_price']
            current_price_change_percentage_24h = coin['price_change_percentage_24h']
            total_volume = coin['total_volume']
            circulating_supply = circulating_supply if circulating_supply is not None else None
            max_supply = max_supply if max_supply is not None else None
            current_price_change_24h = coin['price_change_24h']
            market_cap_change_24h = coin['market_cap_change_24h']
            market_cap_change_percentage_24h = coin['market_cap_change_percentage_24h']
            market_cap = coin['market_cap'] 
            try:
                connection = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                cursor = connection.cursor()

                # Check if cryptocurrency already exists
                cursor.execute("""
                    SELECT cryptocurrency_id FROM Cryptocurrencies
                    WHERE name = %s AND symbol = %s
                """, (name, symbol))
                existing_cryptocurrency = cursor.fetchone()

                if existing_cryptocurrency:
                    # Update existing cryptocurrency
                    cryptocurrency_id = existing_cryptocurrency[0]
                    cursor.execute("""
                        UPDATE Cryptocurrencies
                        SET max_supply = %s, circulating_supply = %s
                        WHERE cryptocurrency_id = %s
                    """, (max_supply, circulating_supply, cryptocurrency_id))
                else:
                    # Insert new cryptocurrency
                    cursor.execute("""
                        INSERT INTO Cryptocurrencies (name, symbol, max_supply, circulating_supply)
                        VALUES (%s, %s, %s, %s)
                    """, (name, symbol, max_supply, circulating_supply))
                    cryptocurrency_id = cursor.lastrowid



                # Check if any data exists for the cryptocurrency_id
                cursor.execute("""
                    SELECT marketdata_id FROM MarketData
                    WHERE cryptocurrency_id = %s
                """, (cryptocurrency_id,))
                existing_data = cursor.fetchone()

                if existing_data:
                    # If data exists, update the existing record
                    print("Updating existing data for marketdata...")
                    cursor.execute("""
                        UPDATE MarketData
                        SET 
                            date = NOW(),
                            current_price = %s, 
                            current_price_change_24h = %s,
                            current_price_change_percentage_24h = %s,
                            total_volume = %s,
                            market_cap = %s,
                            market_cap_change_24h = %s,
                            market_cap_change_percentage_24h = %s
                        WHERE marketdata_id = %s
                    """, (current_price, current_price_change_24h, current_price_change_percentage_24h, total_volume, 
                        market_cap, market_cap_change_24h, market_cap_change_percentage_24h, existing_data[0]))

                else:
                    # If no data exists at all for this cryptocurrency_id, insert a new row
                    print("Inserting new data into marketdata...")
                    cursor.execute("""
                        INSERT INTO MarketData (cryptocurrency_id, date, current_price, 
                        current_price_change_24h, current_price_change_percentage_24h, total_volume, market_cap, market_cap_change_24h, market_cap_change_percentage_24h)
                        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s)
                    """, (cryptocurrency_id, current_price, current_price_change_24h, current_price_change_percentage_24h, total_volume, market_cap, market_cap_change_24h, market_cap_change_percentage_24h))


                # Insert new data into HistoricalPrices without checking for existing records.
                try:
                    cursor.execute("""
                        INSERT INTO HistoricalPrices (
                            cryptocurrency_id, date, price, volume, price_change, 
                            percentage_change, market_cap, market_cap_change_24h, market_cap_change_percentage_24h
                        ) VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        cryptocurrency_id, current_price, total_volume, 
                        current_price_change_24h, current_price_change_percentage_24h, 
                        market_cap, market_cap_change_24h, market_cap_change_percentage_24h
                    ))
                    print("New data inserted into HistoricalPrices.")
                except Error as e:
                    print(f"Error inserting data into HistoricalPrices: {e}")



                # Insert or update Tradepair
                cursor.execute("""
                    SELECT tradepair_ID FROM Tradepair
                    WHERE base_currency_id = %s AND quote_currency_id = %s
                """, (cryptocurrency_id, cryptocurrency_id))
                existing_tradepair = cursor.fetchone()

                if existing_tradepair:
                    # Update existing tradepair
                    cursor.execute("""
                        UPDATE Tradepair
                        SET current_price = %s, volume_24h = %s
                        WHERE tradepair_ID = %s
                    """, (current_price, total_volume, existing_tradepair[0]))
                else:
                    # Insert new tradepair
                    cursor.execute("""
                        INSERT INTO Tradepair (base_currency_id, quote_currency_id, current_price, volume_24h)
                        VALUES (%s, %s, %s, %s)
                    """, (cryptocurrency_id, cryptocurrency_id, current_price, total_volume))

                # Commit the changes
                connection.commit()

            except Error as e:
                print(f"Error inserting data: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()

    else:
        print(f"Error: {response.status_code}")

# Oändlig loop för att köra koden var 30:e minut
while True:
    fetch_and_store_data()  #funktion för att hämta och lagra data
    print("Waiting for the next data collection...")
    
    # Pausa i 30 minuter (1800 sekunder)
    time.sleep(900)
