from flask import Flask, render_template_string, redirect, url_for, request, jsonify
from google.oauth2.service_account import Credentials
import gspread
import plotly.express as px
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt

# Create Flask app
app = Flask(__name__)
app.secret_key = '21!nov1996'

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# In-memory user store with hashed passwords (replace with a database for production)
users = {
    'prashanthgm3': bcrypt.hashpw('21!nov1996'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
    'praveenmanoharg': bcrypt.hashpw('14Oct1989'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None

# Add new user route
@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    new_username = request.form.get("username")
    new_password = request.form.get("password")
    if new_username and new_password:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users[new_username] = hashed_password
        return "User added successfully!", 200
    return "Invalid input", 400

# Google Sheets authentication and data fetching
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("/home/rpi/myenv/plenary-utility-444815-g1-08f401bc6c68.json", scopes=scope)
client = gspread.authorize(creds)
spreadsheet_id = "1AccUH_X1SSLCtIFv9pUHxfq4CQhTpsumIokUZfL87bY"
spreadsheet = client.open_by_key(spreadsheet_id)
sheet = spreadsheet.worksheet("Expenses")
data = sheet.get_all_records()

# Formatting data into a DataFrame
formatted_data = pd.DataFrame(data)
formatted_data['Amount'] = pd.to_numeric(formatted_data['Amount'], errors='coerce')
formatted_data['Date'] = pd.to_datetime(formatted_data['Date'], errors='coerce')

# Extract Month, Year, and Year-Month from Date
formatted_data['Year'] = formatted_data['Date'].dt.year
formatted_data['Month'] = formatted_data['Date'].dt.month
formatted_data['Year-Month'] = formatted_data['Date'].dt.to_period('M').astype(str)

# Grouping data by Year-Month and summing the Amount for monthly data
monthly_data = formatted_data.groupby('Year-Month').agg({'Amount': 'sum'}).reset_index()

# Grouping data by Year-Month and Category for category-wise spending
category_monthly_data = formatted_data.groupby(['Year-Month', 'Category']).agg({'Amount': 'sum'}).reset_index()

# Grouping data by Year and summing the Amount for yearly data
yearly_data = formatted_data.groupby('Year').agg({'Amount': 'sum'}).reset_index()

# Grouping data by Date for daily total spending
daily_total_data = formatted_data.groupby('Date').agg({'Amount': 'sum'}).reset_index()


# Function to create a Plotly bar chart for monthly expenses
def create_expenses_chart():
    fig = px.bar(monthly_data, 
                 x="Year-Month", 
                 y="Amount", 
                 title="Monthly Expenses",
                 labels={"Year-Month": "Month-Year", "Amount": "Total Amount"})
    fig.update_layout(xaxis_tickangle=-45)
    return fig.to_html(full_html=False)

# Function to create a Plotly bar chart for category-wise monthly spending
def create_category_chart():
    fig = px.bar(category_monthly_data, 
                 x="Year-Month", 
                 y="Amount", 
                 color="Category", 
                 title="Category-wise Monthly Spending",
                 labels={"Year-Month": "Month-Year", "Amount": "Total Amount", "Category": "Expense Category"})
    fig.update_layout(xaxis_tickangle=-45, barmode='stack')
    return fig.to_html(full_html=False)

# Function to create a Plotly bar chart for yearly expenses
def create_yearly_expenses_chart():
    fig = px.bar(yearly_data, 
                 x="Year", 
                 y="Amount", 
                 title="Total Yearly Expenses",
                 labels={"Year": "Year", "Amount": "Total Expenses"})
    fig.update_layout(xaxis_tickangle=-45)
    return fig.to_html(full_html=False)

# Function to create a Plotly bar chart for daily total spending
def create_daily_total_chart():
    fig = px.bar(
        daily_total_data,
        x="Date",
        y="Amount",
        title="Daily Total Spending",
        labels={"Date": "Date", "Amount": "Total Amount"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig.to_html(full_html=False)

@app.route("/")
@login_required
def main():
    page_content_dash = """
   <html>
<head>
    <title>Home Application</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #ADD8E6;
            color: #333;
        }
        .header {
            text-align: center;
            padding: 20px;
            background-color: #4CAF50;
            color: white;
        }
        .container {
            margin: 20px auto;
            text-align: center;
            max-width: 800px;
        }
        .btn-container {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>MN152 Application</h1>
    </div>
    <div class="container">
        <h2>Welcome, {{ current_user.id }}!</h2>
        <br><br>
        <h1>Prashanth Expense and Investment Tracker</h1>
        <div class="btn-container">
            <a href="https://docs.google.com/spreadsheets/d/1AccUH_X1SSLCtIFv9pUHxfq4CQhTpsumIokUZfL87bY/edit?gid=182432802#gid=182432802" 
               class="btn btn-primary" target="_blank">Google Sheet Tracker</a>
        </div>
        <div class="btn-container">
            <a href="/plot" class="btn btn-success">Expense Visualization</a>
        </div>
        <div class="btn-container">
            <a href="/investments" class="btn btn-warning">View Mutual and Stock Investment</a>
        </div>
        <div class="btn-container">
            <a href="/logout" class="btn btn-danger">Logout</a>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(page_content_dash)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and bcrypt.checkpw(password.encode('utf-8'), users[username].encode('utf-8')):
            login_user(User(username))
            return redirect(url_for("main"))
        else:
            return "Invalid credentials", 401
    page_content = """
   <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Expense Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea, #764ba2);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .login-container {
            background: rgba(0, 0, 0, 0.8);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        .btn-primary {
            background-color: #ff7eb3;
            border: none;
        }
        .btn-primary:hover {
            background-color: #ff4a86;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Welcome to MN152 Application</h2>
        <form method="POST">
            <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input type="text" class="form-control" id="username" name="username" required>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
    </div>
</body>
</html>

    """
    return render_template_string(page_content)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/plot")
def home():
    expenses_chart_html = create_expenses_chart()
    category_chart_html = create_category_chart()
    yearly_expenses_chart_html = create_yearly_expenses_chart()
    daily_total_chart_html = create_daily_total_chart()

    page_content = """
    <html>
    <head>
        <title>Expense Visualization</title>
        """ + common_styles + """
        <script>
            function refreshData() {
                fetch('/refresh_data')
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        if (data.status === "success") {
                            location.reload();
                        }
                    });
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Expense Visualization</h1>
            <button onclick="refreshData()">Refresh Data</button>
            <button onclick="window.history.back()">Back</button>
            <h2>Monthly Expenses</h2>
            {{ expenses_chart_html | safe }}
            <h2>Category-wise Monthly Spending</h2>
            {{ category_chart_html | safe }}
            <h2>Total Yearly Expenses</h2>
            {{ yearly_expenses_chart_html | safe }}
            <h2>Daily Total Spending</h2>
            {{ daily_total_chart_html | safe }}
        </div>
    </body>
    </html>
    """
    return render_template_string(page_content, 
                                  expenses_chart_html=expenses_chart_html, 
                                  category_chart_html=category_chart_html,
                                  yearly_expenses_chart_html=yearly_expenses_chart_html,
                                  daily_total_chart_html=daily_total_chart_html)


def fetch_investment_data():
    # Fetch Mutual Funds and Investments data from the sheet
    investment_data = spreadsheet.worksheet("Mutual Funds and Investments").get_all_records()
    df = pd.DataFrame(investment_data)

    # Convert Amount to numeric and Date to datetime
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Extract Year and Year-Month from Date
    df['Year'] = df['Date'].dt.year
    df['Year-Month'] = df['Date'].dt.to_period('M').astype(str)

    return df

def create_monthly_investment_chart():
    df = fetch_investment_data()

    # Group by Year-Month and Investment Type
    monthly_data = df.groupby(['Year-Month', 'Investment Type'])['Amount'].sum().reset_index()

    # Create a stacked bar chart
    fig = px.bar(
        monthly_data,
        x="Year-Month",
        y="Amount",
        color="Investment Type",
        title="Monthly Investments by Type",
        labels={"Year-Month": "Month-Year", "Amount": "Investment Amount", "Investment Type": "Type"}
    )
    fig.update_layout(xaxis_tickangle=-45, barmode="stack")
    return fig.to_html(full_html=False)


def create_yearly_investment_chart():
    df = fetch_investment_data()

    # Group by Year and Investment Type
    yearly_data = df.groupby(['Year', 'Investment Type'])['Amount'].sum().reset_index()

    # Create a stacked bar chart
    fig = px.bar(
        yearly_data,
        x="Year",
        y="Amount",
        color="Investment Type",
        title="Yearly Investments by Type",
        labels={"Year": "Year", "Amount": "Investment Amount", "Investment Type": "Type"}
    )
    fig.update_layout(barmode="stack")
    return fig.to_html(full_html=False)


@app.route("/refresh_data")
@login_required
def refresh_data():
    global formatted_data, monthly_data, category_monthly_data, yearly_data, daily_total_data
    
    # Fetch latest data from Google Sheets
    data = sheet.get_all_records()
    formatted_data = pd.DataFrame(data)
    formatted_data['Amount'] = pd.to_numeric(formatted_data['Amount'], errors='coerce')
    formatted_data['Date'] = pd.to_datetime(formatted_data['Date'], errors='coerce')

    formatted_data['Year'] = formatted_data['Date'].dt.year
    formatted_data['Month'] = formatted_data['Date'].dt.month
    formatted_data['Year-Month'] = formatted_data['Date'].dt.to_period('M').astype(str)

    monthly_data = formatted_data.groupby('Year-Month').agg({'Amount': 'sum'}).reset_index()
    category_monthly_data = formatted_data.groupby(['Year-Month', 'Category']).agg({'Amount': 'sum'}).reset_index()
    yearly_data = formatted_data.groupby('Year').agg({'Amount': 'sum'}).reset_index()
    daily_total_data = formatted_data.groupby('Date').agg({'Amount': 'sum'}).reset_index()

    return jsonify({"status": "success", "message": "Data refreshed successfully"})

common_styles = """
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f4f4;
            margin: 0;
            padding: 20px;
            text-align: center;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            max-width: 900px;
            margin: auto;
        }
        button {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            margin: 10px;
        }
        button:hover {
            background: #218838;
        }
    </style>
"""

@app.route("/plot")
@app.route("/investments")
def investments():
    investments_chart_html = create_monthly_investment_chart()
    yearly_investments_chart_html = create_yearly_investment_chart()

    page_content = """
    <html>
    <head>
        <title>Investments Visualization</title>
        """ + common_styles + """
        <script>
            function refreshData() {
                fetch('/refresh_data')
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        if (data.status === "success") {
                            location.reload();
                        }
                    });
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>View Mutual and Stock Investments</h1>
            <button onclick="refreshData()">Refresh Data</button>
            <button onclick="window.history.back()">Back</button>
            <h2>Monthly Investments</h2>
            {{ investments_chart_html | safe }}
            <h2>Yearly Investments</h2>
            {{ yearly_investments_chart_html | safe }}
        </div>
    </body>
    </html>
    """
    return render_template_string(page_content, 
                                  investments_chart_html=investments_chart_html, 
                                  yearly_investments_chart_html=yearly_investments_chart_html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
