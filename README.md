# EquityBot
Welcome! EquityBot is a Discord bot written in Python for equity analysts and finance enthusiasts.

# What does it do?
This bot allows you to do the following:<br />
1. Check the price of stocks real-time from Yahoo Finance by providing their symbols.<br />
2. Get charts of stocks from TradingView with provided specifications.<br />
3. Get news related to the provided stocks from TradingView in the specified interval.<br />
4. Create, edit, and call a watchlist of stocks. Here, call means to check the prices of the stocks in the watchlist.<br />

# Commands
## Check price
#### Usage: `!price <tickers>`
#### Example: `!price AMZN AAPL`
Scrapes the price of the provided stock from Yahoo Finance.<p>

## Get charts
#### Usage: `!chart <TradingView ticker(s)> <timeframe> <indicators> <other options>`
#### Example: `!chart AMZN 5h rsi macd wide`
<p>Gets charts with provided specifications from TradingView. Although it does work with cryptocurrency pairs to an extent, it is meant only for equity stocks listed on TradingView.</p>
<p>Providing a timeframe, indicator, exchange, or other options are all completely optional and you can call this command with just a market/TradingView pair and it will default to the other options to TradingView's chart defaults (such as one hour timeframe, no indicators, and so on).</p>
+ Tickers: Whatever tickers that TradingView supports.<br />
+ Timeframes: 1m, 1, 3m, 3, 5m, 5, 15m, 15, 30m, 30, 1h, 60, 2h, 120, 3h, 180, 4h, 240, 1d, d, day, daily, 1w, w, week, weekly, 1mo, m, mo, month, monthly<br />
+ Indicators: bb, bbr, bbw, crsi, ichi, ichimoku, macd, ma, ema, dema, tema, moonphase, pphl, pivotshl, rsi, stoch, stochrsi, williamr<br />
+ Other Options: wide (widens the image to show more history), bera, blul (I won't tell you what these do, go ahead and try them yourself)<p>

## Get news
Scrapes news from TradingView.
### Get news from a specified number of hours, days, weeks, months, and years ago
#### Usage: `!news <interval> <tickers>`
#### Example: `!news 2w AAPL AMZN`
For intervals, `h` corresponds to hours, `d` corresponds to days, `w` corresponds to weeks, `m` corresponds to months, and `y` corresponds to years.
### Get news from a particular date
#### Usage: `!news <date> <tickers>`
#### Example: `!news 2022-03-20 AAPL TSLA`
The provided date must be in the format `YYYY:MM:DD`.
### Get news between two dates (including first and excluding the second)
#### Usage: `!news <date1> <date2> <tickers>`
#### Example: `!news 2022-03-20 2022-03-24 AAPL`
The provided dates must be in the format YYYY:MM:DD. Also, `date1` must be that date which comes first chronologically.


## Watchlist
### Create a watchlist
#### Usage: `!wlist new <tickers>`
#### Example: `!wlist new AAPL AMZN`
Creates a new watchlist or overwrites an existing one. <br />
### Add ticker(s) to an existing watchlist
#### Usage: `!wlist edit+ <tickers>`
#### Example: `!wlist edit+ TSLA GOOGL`
Adds tickers to a pre-existing watchlist (if they aren't already present). <br />
### Remove ticker(s) from an existing watchlist
#### Usage: `!wlist edit- <tickers>`
#### Example: `!wlist edit- TSLA GOOGL`
Removes tickers from a pre-existing watchlist (if they are present). <br />
#### Usage: `!wlist call`
Gets the price of all the tickers in the watchlist from Yahoo Finance.

## Help
#### Usage: `!help`
Returns a link to this README.md.

# Demonstration
Have a look at <a href='https://github.com/DSS3113/EquityBot/tree/main/demo'>these pictures</a>.

 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/1.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/2.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/3.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/4.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/5.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/6.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/7.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/8.jpg"></picture>
 <picture><img src="https://github.com/DSS3113/EquityBot/blob/main/demo/9.jpg"></picture>
 
# How to run
Create a `.env` file in the project's root directory in the following format:<br/>
```
BOT_TOKEN="<Discord bot token>"
DB_USER="<Database username>" 
DB_PW="<Password for the entered database username>"
```
You would also need to create a PostgreSQL database by the name of `bot_db`.<p>
Next, `cd` into the directory of the local repo and run the following command:<p>
`pip install -r requirements.txt`<p>
 Finally, run the script:<p>
 For Unix:&nbsp;`python3 main.py`<p>
 For Windows:&nbsp;`python main.py`
 
# Future plans
+ Making the `!help` command return command documentation in the Discord channel itself instead of returning a link to this README.md file.
+ Breaking up the code into helper functions and different files to make it more loosely coupled.
 
# Credits
A part of this bot's source code (specifically, the charts function) has been inspired by that of <a href="https://github.com/EthyMoney/TsukiBot/tree/master">TsukiBot</a> (which is written in JavaScript), so I would like to thank its creator(s).
