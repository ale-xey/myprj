import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Query user cash
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = cash[0]["cash"]

    # Query current stock
    stocks = db.execute("SELECT symbol, shares FROM current_stocks WHERE user_id = ?", session["user_id"])
    # TODO
    return render_template("index.html", cash=cash, stocks=stocks)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Ensure symbol or shares was submited
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("missing symbol or shares", 400)

        # Ensure symbol is valid
        elif not lookup(request.form.get("symbol")):
            return apology("must provide valid symbol", 400)

        else:

            # Check is shares positive integer
            try:
                shares = int(request.form.get("shares"))
            except ValueError:
                return apology("must provide positive integer", 400)
            if shares < 1:
                return apology("must provide positive integer", 400)

            # Query user remaining cash
            cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            cash = cash[0]["cash"]

            # Lookup stock price
            quote = lookup(request.form.get("symbol"))
            price = quote["price"]

            # Check is enough cash for stock buying
            if cash < price * shares:
                return apology("not enough cash", 400)

            # Update stocks databases
            db.execute("INSERT INTO stocks (symbol, user_id, shares, price, transactions) VALUES (?, ?, ?, ?, ?)", quote["symbol"], session["user_id"], shares, price, "buy")
            current_shares = db.execute("SELECT shares FROM current_stocks WHERE user_id = ? AND symbol = ?", session["user_id"], quote["symbol"])
            if len(current_shares) > 0:
                current_shares = current_shares[0]["shares"]
                db.execute("UPDATE current_stocks SET shares = ? WHERE id = ? AND symbol = ?", current_shares + shares, session["user_id"], quote["symbol"])
            else:
                db.execute("INSERT INTO current_stocks (symbol, user_id, shares) VALUES (?, ?, ?)", quote["symbol"], session["user_id"], shares)

            # Update user cash
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - price * shares, session["user_id"])

            return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Query transaction history
    stocks = db.execute("SELECT symbol, shares, price, transactions FROM stocks WHERE user_id = ?", session["user_id"])
    return render_template("history.html", stocks=stocks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        # Ensure symbols was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        # Check is symbol is valid
        elif not lookup(request.form.get("symbol")):
            return apology("must provide valid symbol", 400)

        # Lookup requested stock price
        else:
            quote = lookup(request.form.get("symbol"))
            return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation password submited
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Check is password and confirmation password match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords does not match", 400)

        # Check is username exist
        elif len(db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))) > 0:
            return apology("user allready exist", 400)

        # If everything correct register new user
        else:
            username = request.form.get("username")
            password = request.form.get("password")
            hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
            return render_template("login.html")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # Ensure symbol or shares was submited
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("missing symbol or shares", 400)

        # Ensure symbol is valid
        elif len(db.execute("SELECT * FROM current_stocks WHERE user_id = ? AND symbol = ?", session["user_id"], request.form.get("symbol"))) == 0:
            return apology("must provide valid stock symbol", 400)

        else:

            # Check is shares positive integer
            try:
                shares = int(request.form.get("shares"))
            except ValueError:
                return apology("must provide positive integer", 400)
            if shares < 1:
                return apology("must provide positive integer", 400)

            current_shares = db.execute("SELECT shares FROM current_stocks WHERE user_id = ? AND symbol = ?", session["user_id"], request.form.get("symbol"))
            current_shares = current_shares[0]["shares"]

            # Update current stock
            if current_shares < shares:
                return apology("not enough stock shares", 400)
            elif current_shares > shares:
                shares = current_shares - shares
                db.execute("UPDATE current_stocks SET shares = ? WHERE user_id = ? AND symbol = ?", shares, session["user_id"], request.form.get("symbol"))
            else:
                db.execute("DELETE FROM current_stocks WHERE user_id = ? AND symbol = ?", session["user_id"], request.form.get("symbol"))

            # Lookup stock price
            quote = lookup(request.form.get("symbol"))
            price = quote["price"]

            # Update stocks history
            db.execute("INSERT INTO stocks (symbol, user_id, shares, price, transactions) VALUES (?, ?, ?, ?, ?)", request.form.get("symbol"), session["user_id"], shares, price, "sell")

            # Update user cash
            cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            cash = cash[0]["cash"]
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + price * shares, session["user_id"])

            return redirect("/")

    else:
        return render_template("sell.html")
