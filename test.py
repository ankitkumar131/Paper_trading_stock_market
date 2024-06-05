import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import yfinance as yf
import csv
import json
from datetime import datetime

class StockMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Market App")
        
        self.stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "MRF.NS"]
        self.portfolio = {}
        self.watchlist = set()
        self.transactions = []
        self.balance = 500000  # Starting with 500000 rupees fake money
        self.data_file = "stock_data.json"

        self.load_data()
        self.create_widgets()

    def load_data(self):
        try:
            with open(self.data_file, 'r') as file:
                data = json.load(file)
                self.portfolio = data.get('portfolio', {})
                self.transactions = data.get('transactions', [])
                self.balance = data.get('balance', 500000)
        except FileNotFoundError:
            self.portfolio = {}
            self.transactions = []
            self.balance = 500000
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Data file is corrupted. Loading default values.")
            self.portfolio = {}
            self.transactions = []
            self.balance = 1000000

    def save_data(self):
        data = {
            'portfolio': self.portfolio,
            'transactions': self.transactions,
            'balance': self.balance
        }
        with open(self.data_file, 'w') as file:
            json.dump(data, file)

    def create_widgets(self):
        self.balance_label = tk.Label(self.root, text=f"Balance: {self.balance} rupees")
        self.balance_label.pack()

        self.search_frame = tk.Frame(self.root)
        self.search_frame.pack()

        self.stock_label = tk.Label(self.search_frame, text="Stock Symbol:")
        self.stock_label.pack(side=tk.LEFT)
        self.stock_entry = tk.Entry(self.search_frame)
        self.stock_entry.pack(side=tk.LEFT)

        self.search_button = tk.Button(self.search_frame, text="Search", command=self.search_stock)
        self.search_button.pack(side=tk.LEFT)

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack()

        self.buy_button = tk.Button(self.root, text="Buy Stock", command=self.buy_stock)
        self.buy_button.pack()

        self.sell_button = tk.Button(self.root, text="Sell Stock", command=self.sell_stock)
        self.sell_button.pack()

        self.watchlist_button = tk.Button(self.root, text="Add to Watchlist", command=self.add_to_watchlist)
        self.watchlist_button.pack()

        self.show_portfolio_button = tk.Button(self.root, text="Show Portfolio", command=self.show_portfolio)
        self.show_portfolio_button.pack()

        self.show_watchlist_button = tk.Button(self.root, text="Show Watchlist", command=self.show_watchlist)
        self.show_watchlist_button.pack()

        self.generate_csv_button = tk.Button(self.root, text="Generate CSV", command=self.generate_csv)
        self.generate_csv_button.pack()

    def fetch_live_price(self, stock):
        stock_data = yf.Ticker(stock)
        live_price = stock_data.history(period="1d")["Close"].iloc[-1]
        return live_price

    def search_stock(self):
        stock = self.stock_entry.get().upper()
        if stock not in self.stocks:
            messagebox.showerror("Error", f"{stock} is not available in our stock list.")
            return

        live_price = self.fetch_live_price(stock)
        self.result_label.config(text=f"{stock} current price: {live_price:.2f} rupees")
        self.current_stock = stock
        self.current_price = live_price

    def add_to_watchlist(self):
        stock = self.stock_entry.get().upper()
        if stock in self.stocks:
            self.watchlist.add(stock)
            messagebox.showinfo("Watchlist", f"Added {stock} to watchlist.")
        else:
            messagebox.showerror("Error", f"{stock} is not available in our stock list.")

    def buy_stock(self):
        if not hasattr(self, 'current_price'):
            messagebox.showerror("Error", "Please search for a stock first.")
            return
        stock = self.current_stock
        quantity = simpledialog.askinteger("Quantity", "Enter quantity to buy:")
        if quantity is None:
            return
        cost = self.current_price * quantity

        if cost > self.balance:
            messagebox.showerror("Error", "Insufficient balance to buy the stocks.")
            return

        self.balance -= cost
        if stock in self.portfolio:
            self.portfolio[stock].append({"quantity": quantity, "purchase_price": self.current_price})
        else:
            self.portfolio[stock] = [{"quantity": quantity, "purchase_price": self.current_price}]

        self.balance_label.config(text=f"Balance: {self.balance} rupees")
        self.add_to_watchlist()  # Add to watchlist if bought
        self.transactions.append({"action": "buy", "stock": stock, "quantity": quantity, "price": self.current_price, "time": datetime.now().isoformat()})
        self.save_data()
        messagebox.showinfo("Trade", f"Bought {quantity} shares of {stock} at {self.current_price:.2f} rupees each.")

    def sell_stock(self):
        stock = self.stock_entry.get().upper()
        if stock not in self.portfolio:
            messagebox.showerror("Error", f"You do not own any shares of {stock}.")
            return

        total_quantity = sum([entry['quantity'] for entry in self.portfolio[stock]])
        quantity = simpledialog.askinteger("Quantity", "Enter quantity to sell:")
        if quantity is None:
            return
        if quantity > total_quantity:
            messagebox.showerror("Error", f"You do not have enough shares to sell. You own {total_quantity} shares.")
            return

        current_price = self.fetch_live_price(stock)
        quantity_to_sell = quantity
        profit_loss = 0

        for entry in self.portfolio[stock]:
            if quantity_to_sell <= 0:
                break
            if entry["quantity"] <= quantity_to_sell:
                quantity_to_sell -= entry["quantity"]
                profit_loss += (current_price - entry["purchase_price"]) * entry["quantity"]
            else:
                profit_loss += (current_price - entry["purchase_price"]) * quantity_to_sell
                entry["quantity"] -= quantity_to_sell
                quantity_to_sell = 0

        self.portfolio[stock] = [entry for entry in self.portfolio[stock] if entry["quantity"] > 0]

        if not self.portfolio[stock]:
            del self.portfolio[stock]

        self.balance += current_price * quantity
        self.balance_label.config(text=f"Balance: {self.balance} rupees")
        self.transactions.append({"action": "sell", "stock": stock, "quantity": quantity, "price": current_price, "profit_loss": profit_loss, "time": datetime.now().isoformat()})
        self.save_data()
        messagebox.showinfo("Trade", f"Sold {quantity} shares of {stock} at {current_price:.2f} rupees each.\nProfit/Loss: {profit_loss:.2f} rupees.")

    def show_portfolio(self):
        live_prices = {stock: self.fetch_live_price(stock) for stock in self.portfolio.keys()}
        portfolio_str = "Portfolio:\n"
        for stock, details in self.portfolio.items():
            for entry in details:
                current_price = live_prices[stock]
                purchase_price = entry["purchase_price"]
                quantity = entry["quantity"]
                profit_loss = (current_price - purchase_price) * quantity
                portfolio_str += f"{stock}: {quantity} shares at {purchase_price:.2f} (current: {current_price:.2f}), Profit/Loss: {profit_loss:.2f} rupees\n"
        messagebox.showinfo("Portfolio", portfolio_str)

    def show_watchlist(self):
        live_prices = {stock: self.fetch_live_price(stock) for stock in self.watchlist}
        watchlist_str = "Watchlist:\n"
        for stock, price in live_prices.items():
            watchlist_str += f"{stock}: {price:.2f} rupees\n"
        messagebox.showinfo("Watchlist", watchlist_str)

    def generate_csv(self):
        filename = "stock_transactions.csv"
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Action", "Stock", "Quantity", "Price", "Profit/Loss", "Time"])
            for transaction in self.transactions:
                if transaction["action"] == "sell":
                    writer.writerow([transaction["action"], transaction["stock"], transaction["quantity"], transaction["price"], transaction["profit_loss"], transaction["time"]])
                else:
                    writer.writerow([transaction["action"], transaction["stock"], transaction["quantity"], transaction["price"], "", transaction["time"]])
        messagebox.showinfo("CSV", f"Transactions saved to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMarketApp(root)
    root.mainloop()
