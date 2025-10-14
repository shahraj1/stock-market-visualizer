import requests
import json
import os
from datetime import datetime
from typing import List, Dict

class StockDataManager:
    """Manages stock data - fetches symbol list once and stores in memory"""
    
    API_KEY = "{Api-key}"
    EXCHANGE_CODE = "US"  # can use any Exchange Code but US is for all the tickers in US
    
    def __init__(self, force_refresh=False):
        """Initialize and load stock symbols into memory"""
        self.stocks = {}  # Dictionary: {symbol: {Code, Name, Country, Exchange, Currency, Type, Isin}}
        self.symbols = []  # List of all symbols for dropdown
        self.load_symbols(force_refresh)
    
    def load_symbols(self, force_refresh=False):
        """Load symbols from cache or API"""
        if not force_refresh and os.path.exists(self.CACHE_FILE):
            print(f"Loading symbols from cache: {self.CACHE_FILE}")
            self._load_from_cache()
        else:
            print("Fetching symbols from API (one time only)...")
            self._fetch_from_api()
            self._save_to_cache()
        
        print(f"Ready! Loaded {len(self.symbols)} symbols in memory")
    
    def _fetch_from_api(self):
        """Fetch symbols from API (ONE TIME ONLY)"""
        try:
            url = f'https://eodhd.com/api/exchange-symbol-list/{self.EXCHANGE_CODE}?api_token={self.API_KEY}&fmt=json'
            response = requests.get(url)
            
            if response.status_code == 200:
                symbols_data = response.json()
                
                # Extract only the fields we need
                for item in symbols_data:
                    code = item.get('Code')
                    self.stocks[code] = {
                        'Code': item.get('Code'),
                        'Name': item.get('Name'),
                        'Country': item.get('Country'),
                        'Exchange': item.get('Exchange'),
                        'Currency': item.get('Currency'),
                        'Type': item.get('Type'),
                        'Isin': item.get('Isin')
                    }
                
                self.symbols = list(self.stocks.keys())
                print(f"Fetched {len(self.symbols)} symbols from API")
            else:
                print(f"Error fetching symbols: Status {response.status_code}")
        except Exception as e:
            print(f"Error fetching from API: {e}")
    
    def get_symbols(self) -> List[str]:
        """Get list of all symbols from memory"""
        return self.symbols
    
    def get_stock_info(self, symbol: str) -> Dict:
        """Get stock info from memory (no API call)"""
        return self.stocks.get(symbol, {})
    
    def get_all_stocks(self) -> Dict:
        """Get all stocks info"""
        return self.stocks
    
    def refresh_symbols(self):
        """Force refresh symbols from API"""
        print("Refreshing symbols from API...")
        self.load_symbols(force_refresh=True)

# Example usage
if __name__ == "__main__":
    # First time: fetches symbols from API and caches (ONE TIME ONLY)
    manager = StockDataManager()
    print(f"\nAvailable symbols: {manager.get_symbols()[:10]}")  # Show first 10
    
    # Get info from memory (no API call)
    stock_info = manager.get_stock_info("AAPL")
    print(f"\nAAPL Info (from memory): {stock_info}")