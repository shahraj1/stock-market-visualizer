from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict
import random
import tkinter as tk
from tkinter import ttk
import requests
from stock_data_manager import StockDataManager

class StockReport:
    def __init__(self, root, data_manager: StockDataManager):
        self.stocks: List[Dict] = []
        self.selected_stock = 0
        self.root = root
        self.data_manager = data_manager
        self.root.title("Stock Market Visualizer")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create top frame for dropdown
        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_frame, text="Select Stock:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.stock_var = tk.StringVar()
        self.dropdown = ttk.Combobox(top_frame, textvariable=self.stock_var, state="readonly", font=("Arial", 11), width=15)
        self.dropdown.pack(side=tk.LEFT, padx=5)
        self.dropdown.bind("<<ComboboxSelected>>", self.on_stock_selected)
        
        # Close button
        close_btn = tk.Button(top_frame, text="Close", command=self.on_closing, font=("Arial", 10), bg="red", fg="white")
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Create frame for report info
        info_frame = tk.Frame(root)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.info_label = tk.Label(info_frame, text="", font=("Arial", 10), justify=tk.LEFT)
        self.info_label.pack(side=tk.LEFT)
        
        # Create frame for matplotlib
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def add_stock(self, symbol: str, price: float, change: float, 
                  volume: int, market_cap: str, historical_prices: List[float] = None):
        """Add a stock to the report"""
        self.stocks.append({
            'symbol': symbol,
            'price': price,
            'change': change,
            'volume': volume,
            'market_cap': market_cap,
            'historical_prices': historical_prices or []
        })
    
    def _format_currency(self, value: float) -> str:
        """Format as currency"""
        return f"${value:,.2f}"
    
    def _format_volume(self, volume: int) -> str:
        """Format volume with K/M notation"""
        if volume >= 1_000_000:
            return f"{volume/1_000_000:.2f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.2f}K"
        return str(volume)
    
    def on_closing(self):
        """Handle window closing"""
        self.root.quit()
        self.root.destroy()
    
    def populate_dropdown(self, available_symbols: List[str] = None):
        """Populate dropdown with stock symbols"""
        if available_symbols:
            self.dropdown['values'] = available_symbols
            if available_symbols:
                self.dropdown.set(available_symbols[0])
        else:
            symbols = [stock['symbol'] for stock in self.stocks]
            self.dropdown['values'] = symbols
            if symbols:
                self.dropdown.set(symbols[0])
                self.selected_stock = 0
                self.update_display()
    
    def on_stock_selected(self, event):
        """Handle stock selection from dropdown"""
        selected_symbol = self.stock_var.get()
        for idx, stock in enumerate(self.stocks):
            if stock['symbol'] == selected_symbol:
                self.selected_stock = idx
                self.update_display()
                return
        
        # If stock not in list, add it from memory
        print(f"Loading {selected_symbol} from memory...")
        self.load_stock_from_memory(selected_symbol)
    
    def update_display(self):
        """Update the chart and info display"""
        stock = self.stocks[self.selected_stock]
        
        # Update info label
        change_text = f"UP {stock['change']:.2f}%" if stock['change'] >= 0 else f"DOWN {abs(stock['change']):.2f}%"
        info_text = (f"Price: {self._format_currency(stock['price'])}  |  "
                    f"Change: {change_text}  |  "
                    f"Volume: {self._format_volume(stock['volume'])}  |  "
                    f"Market Cap: {stock['market_cap']}")
        self.info_label.config(text=info_text)
        
        # Clear previous canvas
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        # Create new figure
        fig, ax = plt.subplots(figsize=(10, 5))
        self.plot_stock(ax, stock)
        
        # Embed matplotlib in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def plot_stock(self, ax, stock):
        """Plot a single stock"""
        prices = stock['historical_prices']
        
        # Generate dates for x-axis (last 30 days)
        dates = [(datetime.now() - timedelta(days=30-i)).strftime('%m/%d') for i in range(30)]
        
        # Plot line
        ax.plot(range(len(prices)), prices, linewidth=2, marker='o', markersize=5, 
                color='#1f77b4', label=stock['symbol'])
        ax.fill_between(range(len(prices)), prices, alpha=0.3, color='#1f77b4')
        
        # Formatting
        ax.set_title(f"{stock['symbol']} - 30 Day Price Trend", fontweight='bold', fontsize=12)
        ax.set_ylabel('Price', fontsize=11)
        ax.set_xlabel('Days', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Show every 5th date label
        tick_positions = range(0, len(prices), 5)
        tick_labels = [dates[i] if i < len(dates) else '' for i in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, fontsize=10)
        
        # Add min/max annotations
        min_price = min(prices)
        max_price = max(prices)
        min_idx = prices.index(min_price)
        max_idx = prices.index(max_price)
        
        ax.plot(min_idx, min_price, 'ro', markersize=10, label='Lowest')
        ax.plot(max_idx, max_price, 'go', markersize=10, label='Highest')
        ax.text(min_idx, min_price - 3, f'{min_price:.2f}', ha='center', fontsize=9, fontweight='bold')
        ax.text(max_idx, max_price + 3, f'{max_price:.2f}', ha='center', fontsize=9, fontweight='bold')
        
        ax.legend(loc='upper left', fontsize=10)
        fig = ax.get_figure()
        fig.tight_layout()
    
    def display_text_report(self):
        """Display text report in console"""
        print("\n" + "="*80)
        print(f"STOCK MARKET REPORT - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        print("="*80)
        
        if not self.stocks:
            print("No stock data available.")
            print("="*80 + "\n")
            return
        
        # Header
        print(f"{'Symbol':<10} {'Price':<15} {'Change':<15} {'Volume':<15} {'Market Cap':<15}")
        print("-"*80)
        
        # Stock data
        total_value = 0
        for stock in self.stocks:
            symbol = stock['symbol']
            price = self._format_currency(stock['price'])
            change_text = f"UP {stock['change']:.2f}%" if stock['change'] >= 0 else f"DOWN {abs(stock['change']):.2f}%"
            volume = self._format_volume(stock['volume'])
            market_cap = stock['market_cap']
            
            print(f"{symbol:<10} {price:<15} {change_text:<15} {volume:<15} {market_cap:<15}")
            total_value += stock['price']
        
        print("-"*80)
        print(f"Average Price: {self._format_currency(total_value / len(self.stocks))}")
        print("="*80 + "\n")
    
    def fetch_and_add_stock(self, symbol: str, api_key: str = "{api-key}"):
        """Fetch stock data from API and add to report"""
        try:
            data = self.data_manager.fetch_stock_data(symbol)
            if data:
                price = float(data.get('close', 0))
                change = float(data.get('change_pct', 0)) * 100
                volume = int(float(data.get('volume', 0)))
                market_cap = "N/A"
                
                self.add_stock(symbol, price, change, volume, market_cap, generate_historical_data(price))
                self.selected_stock = len(self.stocks) - 1
                self.update_display()
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")


def generate_historical_data(current_price: float, days: int = 30) -> List[float]:
    """Generate realistic historical price data"""
    prices = [current_price]
    for _ in range(days - 1):
        change = random.uniform(-2, 2)
        new_price = prices[-1] * (1 + change / 100)
        prices.insert(0, new_price)
    return prices


def create_report_from_api(root, api_data: List[Dict]):
    """Create report from API data
    
    Expected format from your API:
    [
        {
            'symbol': 'AAPL',
            'close': '148.85001',
            'percent_change': '-0.16097',
            'volume': '67903927',
            ...
        },
        ...
    ]
    """
    report = StockReport(root)
    
    for stock_data in api_data:
        symbol = stock_data.get('symbol', 'N/A')
        price = float(stock_data.get('close', 0))
        change = float(stock_data.get('percent_change', 0))
        volume = int(stock_data.get('volume', 0))
        
        # Calculate market cap if available, otherwise use a placeholder
        market_cap = stock_data.get('market_cap', 'N/A')
        if market_cap == 'N/A':
            market_cap = f"${(price * volume / 1_000_000_000):.1f}B"
        
        report.add_stock(
            symbol=symbol,
            price=price,
            change=change,
            volume=volume,
            market_cap=market_cap,
            historical_prices=generate_historical_data(price)
        )
    
    report.display_text_report()
    report.populate_dropdown()
    
    return report

# Update the API URL
def fetch_stock_data(symbols: List[str], api_key: str) -> List[Dict]:
    """Fetch stock data from EODHD API for given symbols"""
    stock_data = []
    base_url = "https://eodhd.com/api/real-time/{symbol}.US"
    
    for symbol in symbols:
        try:
            url = f"{base_url.format(symbol=symbol)}?api_token={api_key}&fmt=json"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                stock_data.append(data)
                print(f"Fetched data for {symbol}")
            else:
                print(f"Error fetching {symbol}: Status {response.status_code}")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    return stock_data


def main():
    # Initialize the data manager (loads from cache or API)
    print("Initializing Stock Data Manager...")
    data_manager = StockDataManager()
    
    available_symbols = data_manager.get_symbols()
    
    if not available_symbols:
        print("No symbols available. Please check your API key.")
        return
    
    root = tk.Tk()
    report = StockReport(root, data_manager)
    report.populate_dropdown(available_symbols)
    root.mainloop()


if __name__ == "__main__":
    main()