import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import random
import openai

# Replace 'your-api-key' with your actual OpenAI API key
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

STARTING_BANKROLL = 500
DAILY_START_BANKROLL = 3000
CASHOUT_CAP = 20000
AMERICAN_ODDS = -110 
BET_PERCENTAGE = 50 
BETS_PER_DAY = 4
WIN_RATE = 90  

# Convert American odds to Decimal odds
def american_to_decimal(american_odds):
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

# Prompt for Constants
class ConfigDialog(simpledialog.Dialog):
    def body(self, master):
        ttk.Label(master, text="Starting Bankroll:").grid(row=0)
        ttk.Label(master, text="Daily Start Bankroll:").grid(row=1)
        ttk.Label(master, text="Cashout Cap:").grid(row=2)
        ttk.Label(master, text="Average Odds (American):").grid(row=3)
        ttk.Label(master, text="Bankroll Percentage:").grid(row=4)
        ttk.Label(master, text="Bets per Day:").grid(row=5)
        ttk.Label(master, text="Win Rate Percentage:").grid(row=6)

        self.starting_bankroll = tk.Entry(master)
        self.daily_start_bankroll = tk.Entry(master)
        self.cashout_cap = tk.Entry(master)
        self.american_odds = tk.Entry(master)
        self.bet_percentage = tk.Entry(master)
        self.bets_per_day = tk.Entry(master)
        self.win_rate = tk.Entry(master)

        self.starting_bankroll.insert(0, str(STARTING_BANKROLL))
        self.daily_start_bankroll.insert(0, str(DAILY_START_BANKROLL))
        self.cashout_cap.insert(0, str(CASHOUT_CAP))
        self.american_odds.insert(0, str(AMERICAN_ODDS))
        self.bet_percentage.insert(0, str(BET_PERCENTAGE))
        self.bets_per_day.insert(0, str(BETS_PER_DAY))
        self.win_rate.insert(0, str(WIN_RATE))

        self.starting_bankroll.grid(row=0, column=1)
        self.daily_start_bankroll.grid(row=1, column=1)
        self.cashout_cap.grid(row=2, column=1)
        self.american_odds.grid(row=3, column=1)
        self.bet_percentage.grid(row=4, column=1)
        self.bets_per_day.grid(row=5, column=1)
        self.win_rate.grid(row=6, column=1)
        return self.starting_bankroll

    def apply(self):
        self.result = {
            "STARTING_BANKROLL": float(self.starting_bankroll.get()),
            "DAILY_START_BANKROLL": float(self.daily_start_bankroll.get()),
            "CASHOUT_CAP": float(self.cashout_cap.get()),
            "AMERICAN_ODDS": float(self.american_odds.get()),
            "BET_PERCENTAGE": float(self.bet_percentage.get()) / 100,
            "BETS_PER_DAY": int(self.bets_per_day.get()),
            "WIN_RATE": float(self.win_rate.get()) / 100 
        }

config_root = tk.Tk()
config_root.withdraw()
config_dialog = ConfigDialog(config_root, title="Simulation Configuration")
config_root.destroy()

if config_dialog.result:
    config = config_dialog.result
else:
    exit()

STARTING_BANKROLL = config["STARTING_BANKROLL"]
DAILY_START_BANKROLL = config["DAILY_START_BANKROLL"]
CASHOUT_CAP = config["CASHOUT_CAP"]
AMERICAN_ODDS = config["AMERICAN_ODDS"]
BET_PERCENTAGE = config["BET_PERCENTAGE"]
BETS_PER_DAY = config["BETS_PER_DAY"]
WIN_RATE = config["WIN_RATE"]

# Cashout Amount Calculation
CASHOUT_AMOUNT = CASHOUT_CAP - DAILY_START_BANKROLL

# Convert American Odds to Decimal Odds (I love math)
DECIMAL_ODDS = american_to_decimal(AMERICAN_ODDS)

# Simulation Shit
class BettingSim:
    def __init__(self):
        self.total_take_home = 0
        self.backup_fund = 0
        self.day_count = 0
        self.bankroll = STARTING_BANKROLL
        self.in_growth_phase = True
        self.day_bets = []

    def simulate_bet(self, amount):
        win = random.random() < WIN_RATE  
        bet_result = {
            'bet_amount': amount,
            'win': win
        }
        if win:
            bet_result['profit'] = amount * (DECIMAL_ODDS - 1) 
        else:
            bet_result['profit'] = -amount
        return bet_result

    def run_day(self):
        self.day_count += 1
        daily_bankroll = self.bankroll if self.in_growth_phase else DAILY_START_BANKROLL
        self.day_bets = []  # Reset bets for the new day

        for _ in range(BETS_PER_DAY):
            bet_amount = BET_PERCENTAGE * daily_bankroll
            min_bet_amount = 0.15 * STARTING_BANKROLL  # 15% of the starting bankroll, Chat GPT recommendation

            if bet_amount < min_bet_amount:
                return self.day_count, daily_bankroll, self.total_take_home, self.backup_fund, self.day_bets

            bet_result = self.simulate_bet(bet_amount)
            self.day_bets.append(bet_result)
            daily_bankroll += bet_result['profit']

            if daily_bankroll >= CASHOUT_CAP:
                surplus = daily_bankroll - DAILY_START_BANKROLL
                self.total_take_home += surplus / 2
                self.backup_fund += surplus / 2
                daily_bankroll = DAILY_START_BANKROLL
                break

        if self.in_growth_phase:
            self.bankroll = daily_bankroll
            if self.bankroll >= DAILY_START_BANKROLL:
                self.in_growth_phase = False
        else:
            if daily_bankroll > DAILY_START_BANKROLL:
                surplus = daily_bankroll - DAILY_START_BANKROLL
                self.total_take_home += surplus / 2
                self.backup_fund += surplus / 2
            self.bankroll = DAILY_START_BANKROLL

        return self.day_count, self.bankroll, self.total_take_home, self.backup_fund, self.day_bets

    def analyze_simulation(self):
        total_days = self.day_count
        total_take_home = self.total_take_home
        backup_fund = self.backup_fund

        # Calculate average daily, weekly, monthly, and yearly pocket money
        avg_daily = total_take_home / total_days if total_days > 0 else 0
        avg_weekly = avg_daily * 7
        avg_monthly = avg_daily * 30
        avg_yearly = avg_daily * 365

        # Prepare the prompt for ChatGPT
        prompt = (
            f"You are an expert financial advisor. I am simulating sports bets placed. Each simulation will have varying constants, like how much I'd start with, how much bankroll I'd like to start with, and the withdrawal threshold every day. At the end of each day, there are two funds we put the profit in half and half; our take home, and our backup fund, in case we lose our bankroll one day or if something happens. All of this money will be taken out in crypto. Let's say the person lives in missouri and is filing taxes as single. Based on the following simulation results, provide an analysis of the user's financial situation, "
            f"including what they could buy, how much money they make after converting from btc and after paying income taxes daily, weekly, monthly, and yearly, and any recommendations for improvement. Make it as concise as possible while still getting the point across. The average BTC to usd rate right now is around $95,000. Also, do not use markdown rendering. Again, being not too concise is key, maybe make everything kind of into bullet points, and make sure you analyze this simulation once and once only, and to not summarize the simulation more than ONE TIME. Remember to include how much money before and after taxes daily, weekly, monthly, and yearly on average.\n\n"
            f"Simulation Results:\n"
            f"- Starting Bankroll: ${STARTING_BANKROLL:.2f}\n"
            f"- Daily Start Bankroll: ${DAILY_START_BANKROLL:.2f}\n"
            f"- Total Days Simulated: {total_days}\n"
            f"- Total Take-Home Amount: ${total_take_home:.2f}\n"
            f"- Backup Fund: ${backup_fund:.2f}\n"
            f"- Average Daily Pocket Money: ${avg_daily:.2f}\n"
            f"- Average Weekly Pocket Money: ${avg_weekly:.2f}\n"
            f"- Average Monthly Pocket Money: ${avg_monthly:.2f}\n"
            f"- Average Yearly Pocket Money: ${avg_yearly:.2f}\n"
        )

        # Call the OpenAI API
        try:
            response = openai.Completion.create(
                engine="gpt-4.1-nano",
                prompt=prompt,
                max_tokens=1250
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"Error communicating with ChatGPT: {e}"

    def run_simulation_with_analysis(self, days):
        for _ in range(days):
            self.run_day()
        return self.analyze_simulation()

# GUI
sim = BettingSim()


def run_simulation():
    for row in tree.get_children():
        tree.delete(row)
    sim = BettingSim()
    days = int(days_entry.get())
    for _ in range(days):
        day, bankroll, take_home, backup, day_bets = sim.run_day()
        tree.insert("", "end", values=(day, f"${bankroll:.2f}", f"${take_home:.2f}", f"${backup:.2f}", str(day_bets)))

    # Display analysis in the text box
    analysis = sim.analyze_simulation()
    analysis_text.config(state=tk.NORMAL)
    analysis_text.delete(1.0, tk.END)
    analysis_text.insert(tk.END, analysis)
    analysis_text.config(state=tk.DISABLED)


def open_config():
    global STARTING_BANKROLL, DAILY_START_BANKROLL, CASHOUT_CAP, AMERICAN_ODDS, BET_PERCENTAGE, BETS_PER_DAY, WIN_RATE, sim

    config_root = tk.Toplevel(root)
    config_dialog = ConfigDialog(config_root, title="Adjust Simulation Configuration")
    config_root.destroy()

    if config_dialog.result:
        config = config_dialog.result
        STARTING_BANKROLL = config["STARTING_BANKROLL"]
        DAILY_START_BANKROLL = config["DAILY_START_BANKROLL"]
        CASHOUT_CAP = config["CASHOUT_CAP"]
        AMERICAN_ODDS = config["AMERICAN_ODDS"]
        BET_PERCENTAGE = config["BET_PERCENTAGE"]
        BETS_PER_DAY = config["BETS_PER_DAY"]
        WIN_RATE = config["WIN_RATE"]
        sim = BettingSim()


def show_day_details(day_bets):
    bet_details_window = tk.Toplevel(root)
    bet_details_window.title("Day's Bet Details")

    font = ('Arial', 12)

    for i, bet in enumerate(day_bets):
        win_status = "Win" if bet['win'] else "Loss"
        ttk.Label(bet_details_window, text=f"Bet {i+1}: ${bet['bet_amount']:.2f} - {win_status} - Profit: ${bet['profit']:.2f}",
                  font=font).pack()


def on_tree_select(event):
    item = tree.selection()[0]
    day = tree.item(item, "values")[0]
    day_bets = eval(tree.item(item, "values")[4])  
    show_day_details(day_bets)


root = tk.Tk()
root.title("Sports Betting Simulation")
root.geometry("700x500")
root.minsize(600, 400)

mainframe = ttk.Frame(root, padding="10")
mainframe.pack(fill=tk.BOTH, expand=True)

controls_frame = ttk.Frame(mainframe)
controls_frame.pack(fill=tk.X)

ttk.Label(controls_frame, text="Days to Simulate:").pack(side=tk.LEFT)
days_entry = ttk.Entry(controls_frame, width=10)
days_entry.insert(0, "30")
days_entry.pack(side=tk.LEFT, padx=(5, 10))

run_button = ttk.Button(controls_frame, text="Run Simulation", command=run_simulation)
run_button.pack(side=tk.LEFT)

config_button = ttk.Button(controls_frame, text="Adjust Settings", command=open_config)
config_button.pack(side=tk.LEFT, padx=(10, 0))

columns = ("Day", "Bankroll", "Take Home", "Backup Fund")
tree = ttk.Treeview(mainframe, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor=tk.CENTER, width=150)
tree.pack(fill=tk.BOTH, expand=True, pady=10)

tree.bind("<Double-1>", on_tree_select)

# Add a frame for analysis text
analysis_frame = ttk.Frame(mainframe, padding="10")
analysis_frame.pack(fill=tk.BOTH, expand=True)

analysis_label = ttk.Label(analysis_frame, text="Analysis:", font=("Arial", 12, "bold"))
analysis_label.pack(anchor="w")

analysis_text = tk.Text(analysis_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=("Arial", 10))
analysis_text.pack(fill=tk.BOTH, expand=True)

root.mainloop()
