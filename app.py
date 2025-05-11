from flask import Flask, render_template, request
from flask import Flask, render_template, request, redirect, url_for
import random
import openai

# Replace 'your-api-key' with your actual OpenAI API key
OPENAI_API_KEY = "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 delete here to enable gpt"
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

app.secret_key = 'dev-secret-1234'  # Replace with a real secret key

# Default constants
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

# Simulation Logic
class BettingSim:
    def __init__(self, starting_bankroll, daily_start_bankroll, cashout_cap, american_odds, bet_percentage, bets_per_day, win_rate):
        self.total_take_home = 0
        self.backup_fund = 0
        self.day_count = 0
        self.bankroll = starting_bankroll
        self.in_growth_phase = True
        self.day_bets = []
        self.STARTING_BANKROLL = starting_bankroll
        self.DAILY_START_BANKROLL = daily_start_bankroll
        self.CASHOUT_CAP = cashout_cap
        self.AMERICAN_ODDS = american_odds
        self.BET_PERCENTAGE = bet_percentage
        self.BETS_PER_DAY = bets_per_day
        self.WIN_RATE = win_rate

    def simulate_bet(self, amount):
        win = random.random() < (self.WIN_RATE / 100)
        bet_result = {
            'bet_amount': amount,
            'win': win
        }
        if win:
            bet_result['profit'] = amount * (american_to_decimal(self.AMERICAN_ODDS) - 1)
        else:
            bet_result['profit'] = -amount
        return bet_result

    def run_day(self):
        self.day_count += 1
        daily_bankroll = self.bankroll if self.in_growth_phase else self.DAILY_START_BANKROLL
        self.day_bets = []

        for _ in range(self.BETS_PER_DAY):
            bet_amount = self.BET_PERCENTAGE / 100 * daily_bankroll
            min_bet_amount = 0.15 * self.STARTING_BANKROLL

            # Stop simulation if bankroll and backup fund are below 15% of starting bankroll
            if daily_bankroll + self.backup_fund < min_bet_amount:
                return self.day_count, daily_bankroll, self.total_take_home, self.backup_fund, self.day_bets

            # Skip betting if bet amount is below the minimum bet amount
            if bet_amount < min_bet_amount:
                break

            bet_result = self.simulate_bet(bet_amount)
            self.day_bets.append(bet_result)
            daily_bankroll += bet_result['profit']

            # Stop betting for the day if bankroll reaches the cashout cap
            if daily_bankroll >= self.CASHOUT_CAP:
                surplus = daily_bankroll - self.DAILY_START_BANKROLL
                self.total_take_home += surplus / 2
                self.backup_fund += surplus / 2
                daily_bankroll = self.DAILY_START_BANKROLL
                break

        # End of day adjustments
        if self.in_growth_phase:
            self.bankroll = daily_bankroll
            if self.bankroll >= self.DAILY_START_BANKROLL:
                self.in_growth_phase = False
        else:
            if daily_bankroll < self.DAILY_START_BANKROLL:
                # Replenish bankroll from backup fund if needed
                deficit = self.DAILY_START_BANKROLL - daily_bankroll
                if self.backup_fund >= deficit:
                    self.backup_fund -= deficit
                    daily_bankroll = self.DAILY_START_BANKROLL
                else:
                    daily_bankroll += self.backup_fund
                    self.backup_fund = 0

            if daily_bankroll > self.DAILY_START_BANKROLL:
                surplus = daily_bankroll - self.DAILY_START_BANKROLL
                self.total_take_home += surplus / 2
                self.backup_fund += surplus / 2

            self.bankroll = self.DAILY_START_BANKROLL

        return self.day_count, self.bankroll, self.total_take_home, self.backup_fund, self.day_bets

    def analyze_simulation(self):
        total_days = self.day_count
        total_take_home = self.total_take_home
        backup_fund = self.backup_fund

        avg_daily = total_take_home / total_days if total_days > 0 else 0
        avg_weekly = avg_daily * 7
        avg_monthly = avg_daily * 30
        avg_yearly = avg_daily * 365

        prompt = (
            f"You are an expert financial advisor. I am simulating sports bets placed. Each simulation will have varying constants, like how much I'd start with, how much bankroll I'd like to start with, and the withdrawal threshold every day. At the end of each day, there are two funds we put the profit in half and half; our take home, and our backup fund, in case we lose our bankroll one day or if something happens. All of this money will be taken out in crypto. Let's say the person lives in missouri and is filing taxes as single. Based on the following simulation results, provide an analysis of the user's financial situation, "
            f"including what they could buy, how much money they make after converting from btc and after paying income taxes daily, weekly, monthly, and yearly, and any recommendations for improvement. Make it as concise as possible while still getting the point across. Also, do not use markdown rendering. The average BTC to usd rate right now is around $95,000. Again, being not too concise is key, maybe make everything kind of into bullet points, and make sure you analyze this simulation once and once only, and to not summarize the simulation more than ONE TIME. Remember to include how much money before and after taxes daily, weekly, monthly, and yearly on average.\n\n"
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
            f"Your resposne is in a website that will be in html. Could you respond in HTML? But don't add any headersor html tags or body tags, you're already within the body tag. Also make the text centered if you can.\n"
        )

        try:
            response = openai.Completion.create(
                engine="gpt-4.1-nano",
                prompt=prompt,
                max_tokens=1250
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"Error communicating with ChatGPT: {e}"

@app.route("/", methods=["GET", "POST"])
def home():
    global STARTING_BANKROLL, DAILY_START_BANKROLL, CASHOUT_CAP, AMERICAN_ODDS, BET_PERCENTAGE, BETS_PER_DAY, WIN_RATE

    if request.method == "POST":
        # Get values from form and update constants
        STARTING_BANKROLL = float(request.form["starting_bankroll"])
        DAILY_START_BANKROLL = float(request.form["daily_start_bankroll"])
        CASHOUT_CAP = float(request.form["cashout_cap"])
        AMERICAN_ODDS = int(request.form["american_odds"])
        BET_PERCENTAGE = int(request.form["bet_percentage"])
        BETS_PER_DAY = int(request.form["bets_per_day"])
        WIN_RATE = int(request.form["win_rate"])
        days = int(request.form["days"])

        # Run simulation
        sim = BettingSim(
            STARTING_BANKROLL, DAILY_START_BANKROLL, CASHOUT_CAP,
            AMERICAN_ODDS, BET_PERCENTAGE, BETS_PER_DAY, WIN_RATE
        )
        simulation_results = []
        for _ in range(days):
            day, bankroll, take_home, backup, day_bets = sim.run_day()
            simulation_results.append((day, bankroll, take_home, backup, day_bets))

        analysis = sim.analyze_simulation()

        # Store simulation data in a session or pass it to the simulation page
        # In this case, we will redirect and pass it using Flask's session (for simplicity)
        from flask import session
        session['simulation_results'] = simulation_results
        session['analysis'] = analysis
        session['constants'] = {
            "starting_bankroll": STARTING_BANKROLL,
            "daily_start_bankroll": DAILY_START_BANKROLL,
            "cashout_cap": CASHOUT_CAP,
            "american_odds": AMERICAN_ODDS,
            "bet_percentage": BET_PERCENTAGE,
            "bets_per_day": BETS_PER_DAY,
            "win_rate": WIN_RATE
        }

        return redirect(url_for('simulation'))

    # If GET request, just show form with default constants (no simulation results)
    constants = {
        "starting_bankroll": STARTING_BANKROLL,
        "daily_start_bankroll": DAILY_START_BANKROLL,
        "cashout_cap": CASHOUT_CAP,
        "american_odds": AMERICAN_ODDS,
        "bet_percentage": BET_PERCENTAGE,
        "bets_per_day": BETS_PER_DAY,
        "win_rate": WIN_RATE
    }

    return render_template("index.html", simulation_results=None, analysis=None, constants=constants)


@app.route("/simulation", methods=["GET"])
def simulation():
    from flask import session

    # Retrieve simulation data from session
    simulation_results = session.get('simulation_results', [])
    analysis = session.get('analysis', '')
    constants = session.get('constants', {})

    return render_template("simulation.html", simulation_results=simulation_results, analysis=analysis, constants=constants)



if __name__ == "__main__":
    app.run(debug=True)
