"""
Things to implement:
1. Provides user with the current price of a stock/crypto. (done)
2. Provides user with a price history graph of the specified stock/crypto according to the specified scope. (done)
3. Provides user with news related to the specified stock/crypto. (done)
4. Pings user when the stock/crypto reaches a certain price (essentially a watchlist)."""

import asyncio,io, os, platform, psycopg2, re, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from discord import File, Embed
from discord.ext import commands
from pyppeteer import launch

yahoo_fin = "https://finance.yahoo.com/quote/" 
trading_view = 'https://in.tradingview.com/chart/?symbol='
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
}

bot = commands.Bot(command_prefix = '!')
bot.remove_command("help") # Because we are making a custom help command

"""
Returns True if the provided argument is a decimal/float.
"""
def is_decimal(s):
    try:
        float(s)
    except ValueError:
        return False
    return True


"""
Gets the price of the specified stock(s). Example: !price AAPL AMZN
"""
@bot.command()
async def price(ctx, *stock_symbols):
    price_list = []
    price_message = await ctx.send(f'Fetching ``{ctx.message.content}``')
    for stock_symbol in stock_symbols:
        url = yahoo_fin+stock_symbol
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html5lib')
        try:
            stock_name = soup.find('h1', { 'class': 'D(ib) Fz(18px)' }).text
        except AttributeError:
            price_list.append(f'• {stock_symbol} is not a valid symbol.')
            continue
        # Getting 'At Close' price
        fin_streamers = soup.find('div', {'class': 'D(ib) Mend(20px)'}).findChildren('fin-streamer')
        at_close = ''
        for i in fin_streamers:
            at_close += i.text + ' '
        at_close = at_close.strip()

        # Getting 'After Hours' price
        if soup.find('div', {'class': 'Fz(12px) C($tertiaryColor) My(0px) D(ib) Va(b)'}):
            fin_streamers = soup.find('div', {'class': 'Fz(12px) C($tertiaryColor) My(0px) D(ib) Va(b)'}).findChildren('fin-streamer')
            after_hours = ''
            for i in fin_streamers[0:4]:
                after_hours += i.text + ' '
            after_hours = after_hours.strip()
            price_list.append(
                f'''• **{stock_name}**
    At Close (4:00PM EDT):
    ***{at_close}***
    After Hours (07:59PM EDT):
    ***{after_hours}***'''
                )
        else:
            price_list.append(
                f'''• **{stock_name}**
    At Close (4:00PM EDT):
    ***{at_close}***'''
            )
    
    await ctx.send(content='\n'.join(price_list))
    await price_message.delete()

"""
Gets the chart for the specified stock(s) with the provided options. Example: !chart AAPL 5h wide macd
"""
@bot.command()
async def chart(ctx, *args): 
    interval_keys = [
        '1m', '1', '3m', '3', '5m', '5', '15m', 
        '15', '30m', '30', '1h', '60', '2h', '120', 
        '3h', '180', '4h', '240', '1d', 'd',
        'day', 'daily', '1w', 'w', 'week', 'weekly', 
        '1mo', 'm', 'mo', 'month', 'monthly'
    ]
    interval_map = {
        '1m': '1', '1': '1', '3m': '3', '3': '3', '5m': '5', 
        '5': '5', '15m': '15', '15': '15', '30m': '30', '30': '30', 
        '1h': '60', '60': '60', '2h': '120', '120': '120', '3h': '180', 
        '180': '180', '4h': '240', '240': '240', '1d': 'D', 'd': 'D',
        'day': 'D', 'daily': 'D', '1w': 'W', 'w': 'W', 'week': 'W', 
        'weekly': 'W', '1mo': 'M', 'm': 'M', 'mo': 'M', 'month': 'M', 'monthly': 'M'
    }

    studies_keys = [
        'bb', 'bbr', 'bbw', 'crsi', 'ichi', 'ichimoku', 'macd', 'ma', 'ema', 'dema',
        'tema', 'moonphase', 'pphl', 'pivotshl', 'rsi', 'stoch', 'stochrsi', 'williamr'
    ]

    studies_map = {
        'bb': 'BB@tv-basicstudies',
        'bbr': 'BollingerBandsR@tv-basicstudies',
        'bbw': 'BollingerBandsWidth@tv-basicstudies',
        'crsi': 'CRSI@tv-basicstudies',
        'ichi': 'IchimokuCloud@tv-basicstudies',
        'ichimoku': 'IchimokuCloud@tv-basicstudies',
        'macd': 'MACD@tv-basicstudies',
        'ma': 'MASimple@tv-basicstudies',
        'ema': 'MAExp@tv-basicstudies',
        'dema': 'DoubleEMA@tv-basicstudies',
        'tema': 'TripleEMA@tv-basicstudies',
        'moonphase': 'MoonPhases@tv-basicstudies',
        'pphl': 'PivotPointsHighLow@tv-basicstudies',
        'pivotshl': 'PivotPointsHighLow@tv-basicstudies',
        'rsi': 'RSI@tv-basicstudies',
        'stoch': 'Stochastic@tv-basicstudies',
        'stochrsi': 'StochasticRSI@tv-basicstudies',
        'williamr': 'WilliamR@tv-basicstudies'
    }

    interval_key = '1h'
    
    selected_studies = []
    
    chart_get_attempts = 1
    
    for i in args:
        if i in interval_keys:
            interval_key = i

        # Checking if the user put something like "4hr" instead of just "4h"
        elif i[:-1] in interval_keys:
            interval_key = i[:-1]

        # Checking if the user put something like "5min" instead of just "5m" or "5"
        elif i[:-2] in interval_keys:
            interval_key = i[:-2]
        if i in studies_keys:
            selected_studies.append('"' + studies_map[i] + '"')

    # Overwriting html file to get the desired chart
    html_file = open('chart.html', 'w')
    html_file.write(f"""<div id="ccchart-container" style="width:{'1280' if 'wide' in args else '720'}px; height: 600px; position:relative; top:-50px; left:-10px;">
    <div class="tradingview-widget-container">
      <div id="tradingview_bc0b0"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": {'1280' if 'wide' in args else '720'},
        "height": 600,
        "symbol": "{args[0]}",
        "interval": "{interval_map[interval_key]}",
        "timezone": "Etc/UTC",
        "theme": "{'light' if 'moro' in args or 'light' in args else 'dark'}",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "studies": [
          {','.join(selected_studies)}
        ],
        "container_id": "tradingview_bc0b0"
      }}
      );
      </script>
    </div>
</div>""")
    html_file.close()

    while True:
        try:
            if len(args) < 2:
                await ctx.reply('Insufficient number of arguments provided. Check `!help` to see how to use the charts command.')
                return
        
            if chart_get_attempts == 1:
                chart_message = await ctx.send(f'Fetching ``{ctx.message.content}``')
            else:
                await chart_message.edit(content=f"```TradingView Widget threw error, re-attempting {chart_get_attempts} of 3 ``` Fetching ``{ctx.message.content}``")
                
            browser = await launch()
            page = await browser.newPage()
            
            html_file_path =  os.path.dirname(os.path.abspath(__file__)) + r'\chart.html'
            if platform.system != 'Windows':
                html_file_path = html_file_path.replace(r'\chart.html', '/chart.html')
            await page.goto(html_file_path)

            # Waiting for chart to load    
            iframe = await page.J('div#tradingview_bc0b0 iframe')
            frame = await iframe.contentFrame()
            await frame.waitForSelector('div[class*="noWrapWrapper-"]', { 'visible': True })
            # Checking if the chart can be loaded or not
            if not await frame.J('div[class*="invalidSymbol-"]'):
                # Checking if the values are loaded or not and if the loaders are visible or not
                values_loaded_flag = False
                loaders_visible_flag = True
                value_divs = await frame.JJ('div[class*="valueItem-"]:not([class*="blockHidden-"]) > div[class*="valueValue-"]')
                loader_spans = await frame.JJ('div[class*="valuesWrapper-"] > span[class*="loader-"]')
                while values_loaded_flag == False or loaders_visible_flag == True:
                    for i in value_divs:
                        value_div_text = await frame.evaluate('valueDiv => valueDiv.textContent', i)
                        if '%' not in value_div_text and 'K' not in value_div_text:
                            if not is_decimal(value_div_text):
                                values_loaded_flag = False
                                break
                            else:
                                #print(await frame.evaluate('''() => { var valueDivText = []; document.querySelectorAll('div[class*="valueItem-"]:not([class*="blockHidden-"]) > div[class*="valueValue-"]').forEach(a => valueDivText.push(a.textContent)); return valueDivText; }'''))
                                values_loaded_flag = True
                    for i in loader_spans:
                        loader_visible = await frame.evaluate('loaderSpan => [...loaderSpan.classList].every(class_ => !class_.includes("blockHidden-"))', i) # Even if one class in the loader span element's classList includes the string "blockHidden-", it means it is hidden
                        if loader_visible:
                            loaders_visible_flag = True
                            break
                        else:
                            #print(await frame.evaluate('''() => { var classListOfLoaders = []; document.querySelectorAll('div[class*="valuesWrapper-"] > span[class*="loader-"]').forEach(a => classListOfLoaders.push(a.classList)); return classListOfLoaders; }'''))
                            loaders_visible_flag = False

            # Checking if the chart requested is a log chart or not
            if 'log' in args:
                await page.keyboard.down('Alt')
                await page.keyboard.press('KeyL')
                await page.keyboard.up('Alt')
                
            # Setting the viewport
            await page.setViewport({
                'width': 1275 if 'wide' in args else 715,
                'height': 557
            })
            # Taking a screenshot
            chart_screenshot = io.BytesIO(await page.screenshot())

            # Freeing resources and closing the page and browser
            await page.goto('about:blank')
            await page.close()
            await browser.close()
            
            chartnotavailable_size = 12016 #os.path.getsize('chartnotavailable.png')
            invalidsymbol_size = 12545 #os.path.getsize('invalidsymbol.png')
            chart_screenshot_size = chart_screenshot.getbuffer().nbytes

            if 12000 < chart_screenshot_size < 13000:
                print('Chart not Available or Invalid Symbol')

            # Sending chart on Discord
            file_attachment = File(fp=chart_screenshot, filename='chart_screenshot.png') 
            await ctx.send(file=file_attachment)
            await chart_message.delete()
            break
            
        except Exception as err:
            if chart_get_attempts < 3:
                print(err)
                chart_get_attempts += 1
            else:
                await chart_message.edit(content='```TradingView handler threw error, all re-attempts exhausted :(```')
                break

"""
There are three ways to use this command:
1. Use it to get news related to a stock/some stocks in the past few hours, days, weeks, months, and years. Example: !news 2w AAPL AMZN
2. Use it to get news related to a stock/some stocks on a current date. Example: !news 2022-03-20 AAPL
3. Use it to get news related to a stock/some stocks on a between two dates (not including the later one). Example: !news 2022-03-20 2022-03-24 AAPL
"""
@bot.command()
async def news(ctx, *args):
    try:
        interval_validation = re.match(r'\d[hdwmy]', args[0], re.I)
        if interval_validation:
            if len(args) < 2:
                await ctx.reply('Insufficient number of arguments provided. Check `!help` to see how to use the news command.')
                return
            elif len(args[0]) < 2:
                await ctx.reply('Invalid argument provided. Check `!help` to see how to use the news command.')
                return
            else:
                interval_dict = {
                    'h': 'hour(s)',
                    'd': 'day(s)',
                    'w': 'week(s)',
                    'm': 'month(s)',
                    'y': 'year(s)'
                }
                regex_search_for_interval_letter = re.search(r'[hdwmy]', args[0], re.I)
                interval_num = args[0][:regex_search_for_interval_letter.start()]  # Input validation in case the user entered something like 1hr instead of 1h
                interval_letter = args[0][-1]
                stock_symbols = [stock_symbol for stock_symbol in args[1:]]

                browser = await launch()
                page = await browser.newPage() 

                for stock_symbol in stock_symbols:
                    news_message = await ctx.send(f'Fetching ``{ctx.message.content}``')
                    news_articles_url = "https://www.tradingview.com/symbols/{}/news/".format(stock_symbol)    
                    await page.goto(news_articles_url)

                    # Check if the stock symbol is a valid one or not
                    async def valid_symbol_detector():
                        await page.waitForSelector('article')
                    async def invalid_symbol_detector():
                        await page.waitForSelector('h1[class="tv-http-error-page__title"]')
                    tasks = [asyncio.create_task(valid_symbol_detector(), name='Symbol found'), asyncio.create_task(invalid_symbol_detector(), name='Symbol not found')]
                    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    symbol_invalid_flag = False
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                        if task.done() and task.get_name() == 'Symbol not found':
                            await ctx.reply(f'{stock_symbol} is not a valid stock symbol.')
                            await news_message.delete()
                            symbol_invalid_flag = True
                    if symbol_invalid_flag:
                        continue

                    news_articles_soup = BeautifulSoup(await page.content(), 'html5lib')
                    news_containers = news_articles_soup.find_all('a', class_ = re.compile('^card-'))
                    await ctx.send(f'**News related to {stock_symbol} in the past {interval_num} {interval_dict[interval_letter]}:**')
                    await news_message.delete()

                    no_results = True

                    for i in news_containers:
                        if i.find('relative-time'):                          
                            news_report_datetime_str = i.find('relative-time')['event-time']
                        else:
                            news_report_datetime_str = i.find('time')['datetime']
                        news_report_datetime = datetime.strptime(news_report_datetime_str, '%a, %d %b %Y %X GMT')
                        news_report_datetime = news_report_datetime.replace(tzinfo=timezone.utc)
                        datetime_limit = datetime.now(timezone.utc)
                        match interval_letter:
                            case 'h':
                                datetime_limit = datetime_limit - relativedelta(hours=int(interval_num))
                            case 'd':
                                datetime_limit = datetime_limit - relativedelta(days=int(interval_num))
                            case 'w':
                                datetime_limit = datetime_limit - relativedelta(weeks=int(interval_num))
                            case 'm':
                                datetime_limit = datetime_limit - relativedelta(months=int(interval_num))
                            case 'y':
                                datetime_limit = datetime_limit - relativedelta(years=int(interval_num))
                        if news_report_datetime >= datetime_limit:
                            url = 'https://www.tradingview.com'+i['href']
                            author = i.find('span', class_ = re.compile('^breadcrumbs-')).span.text
                            title = i.find('span', class_ = re.compile('^title-')).text
                            await page.goto(url)
                            news_article_soup = BeautifulSoup(await page.content(), 'html5lib')
                            desc = news_article_soup.find('p').text

                            embed = Embed(title=title, url=url, description=desc, color=15548997)
                            embed.set_author(name=author)
                            embed.set_footer(text=datetime.strftime(news_report_datetime, '%a, %d %b %Y %H:%M GMT'))
                            await ctx.send(embed=embed)
                            no_results = False
                    if no_results:
                        await ctx.reply(f'Oops! No news articles were found for {stock_symbol} in the provided interval.')
                    else:
                        await ctx.reply(f'Woop! Those were all the news articles we could get for {stock_symbol} in the provided interval.')
                    
                await page.goto('about:blank')
                await page.close()
                await browser.close()

        else:
            second_date_validation = re.match('\d{4}-\d{2}-\d{2}', args[1])

            if second_date_validation:

                first_date = datetime.strptime(args[0], '%Y-%m-%d')
                second_date = datetime.strptime(args[1], '%Y-%m-%d')

                if first_date > second_date:
                    await ctx.reply('The first date must come chronologically before the second date. Check `!help` to see how to use the news command.')
                    return

                first_date = first_date.replace(tzinfo=timezone.utc)
                second_date = second_date.replace(tzinfo=timezone.utc)

                stock_symbols = [stock_symbol for stock_symbol in args[2:]]
                
                browser = await launch()
                page = await browser.newPage() 
                
                for stock_symbol in stock_symbols:
                    news_message = await ctx.send(f'Fetching ``{ctx.message.content}``')
                    news_articles_url = "https://www.tradingview.com/symbols/{}/news/".format(stock_symbol)    
                    await page.goto(news_articles_url)

                    # Check if the stock symbol is a valid one or not
                    async def valid_symbol_detector():
                        await page.waitForSelector('article')
                    async def invalid_symbol_detector():
                        await page.waitForSelector('h1[class="tv-http-error-page__title"]')
                    tasks = [asyncio.create_task(valid_symbol_detector(), name='Symbol found'), asyncio.create_task(invalid_symbol_detector(), name='Symbol not found')]
                    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    symbol_invalid_flag = False
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                        if task.done() and task.get_name() == 'Symbol not found':
                            await ctx.reply(f'{stock_symbol} is not a valid stock symbol.')
                            await news_message.delete()
                            symbol_invalid_flag = True
                    if symbol_invalid_flag:
                        continue

                    news_articles_soup = BeautifulSoup(await page.content(), 'html5lib')
                    news_containers = news_articles_soup.find_all('a', class_ = re.compile('^card-'))
                    await ctx.send(f'**News related to {stock_symbol} between {first_date.strftime("%e %B %Y")} and {second_date.strftime("%e %B %Y")}:**')
                    await news_message.delete()

                    no_results = True

                    for i in news_containers:
                        if i.find('relative-time'):                          
                            news_report_datetime_str = i.find('relative-time')['event-time']
                        else:
                            news_report_datetime_str = i.find('time')['datetime']
                        news_report_datetime = datetime.strptime(news_report_datetime_str, '%a, %d %b %Y %X GMT')
                        news_report_datetime = news_report_datetime.replace(tzinfo=timezone.utc)

                        if first_date <= news_report_datetime < second_date:
                            url = 'https://www.tradingview.com'+i['href']
                            author = i.find('span', class_ = re.compile('^breadcrumbs-')).span.text
                            title = i.find('span', class_ = re.compile('^title-')).text
                            await page.goto(url)
                            news_article_soup = BeautifulSoup(await page.content(), 'html5lib')
                            desc = news_article_soup.find('p').text

                            embed = Embed(title=title, url=url, description=desc, color=15548997)
                            embed.set_author(name=author)
                            embed.set_footer(text=datetime.strftime(news_report_datetime, '%a, %d %b %Y %H:%M GMT'))
                            await ctx.send(embed=embed)
                            no_results = False
                    if no_results:
                        await ctx.reply(f'Oops! No news articles were found for {stock_symbol} in the provided interval.')
                    else:
                        await ctx.reply(f'Woop! Those were all the news articles we could get for {stock_symbol} in the provided interval.')
                await page.goto('about:blank')
                await page.close()
                await browser.close()

            else:
                day_date = datetime.strptime(args[0], '%Y-%m-%d')
                day_date = day_date.replace(tzinfo=timezone.utc)

                stock_symbols = [stock_symbol for stock_symbol in args[1:]]
                
                browser = await launch()
                page = await browser.newPage()

                for stock_symbol in stock_symbols:
                    news_message = await ctx.send(f'Fetching ``{ctx.message.content}``')
                    news_articles_url = "https://www.tradingview.com/symbols/{}/news/".format(stock_symbol)    
                    await page.goto(news_articles_url)

                    # Check if the stock symbol is a valid one or not
                    async def valid_symbol_detector():
                        await page.waitForSelector('article')
                    async def invalid_symbol_detector():
                        await page.waitForSelector('h1[class="tv-http-error-page__title"]')
                    tasks = [asyncio.create_task(valid_symbol_detector(), name='Symbol found'), asyncio.create_task(invalid_symbol_detector(), name='Symbol not found')]
                    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    symbol_invalid_flag = False
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                        if task.done() and task.get_name() == 'Symbol not found':
                            await ctx.reply(f'{stock_symbol} is not a valid stock symbol.')
                            await news_message.delete()
                            symbol_invalid_flag = True
                    if symbol_invalid_flag:
                        continue

                    news_articles_soup = BeautifulSoup(await page.content(), 'html5lib')
                    news_containers = news_articles_soup.find_all('a', class_ = re.compile('^card-'))
                    await ctx.send(f'**News related to {stock_symbol} on {day_date.strftime("%e %B %Y")}:**')
                    await news_message.delete()

                    no_results = True

                    for i in news_containers:
                        if i.find('relative-time'):                          
                            news_report_datetime_str = i.find('relative-time')['event-time']
                        else:
                            news_report_datetime_str = i.find('time')['datetime']
                        news_report_datetime = datetime.strptime(news_report_datetime_str, '%a, %d %b %Y %X GMT')
                        news_report_datetime = news_report_datetime.replace(tzinfo=timezone.utc)

                        if news_report_datetime.date() == day_date.date():
                            url = 'https://www.tradingview.com'+i['href']
                            author = i.find('span', class_ = re.compile('^breadcrumbs-')).span.text
                            title = i.find('span', class_ = re.compile('^title-')).text
                            await page.goto(url)
                            news_article_soup = BeautifulSoup(await page.content(), 'html5lib')
                            desc = news_article_soup.find('p').text

                            embed = Embed(title=title, url=url, description=desc, color=15548997)
                            embed.set_author(name=author)
                            embed.set_footer(text=datetime.strftime(news_report_datetime, '%a, %d %b %Y %H:%M GMT'))
                            await ctx.send(embed=embed)
                            no_results = False
                    if no_results:
                        await ctx.reply(f'Oops! No news articles were found for {stock_symbol} in the provided interval.')
                    else:
                        await ctx.reply(f'Woop! Those were all the news articles we could get for {stock_symbol} in the provided interval.')
                await page.goto('about:blank')
                await page.close()
                await browser.close()
    except Exception as err:
        print(err)
        await ctx.reply('Invalid argument(s). Check `!help` to see how to use the news command.')        

"""
You can use this command in four ways:
1. Use it to create a new watchlist. Example: !wlist new AAPL AMZN
2. Use it to add symbols to a pre-existing watchlist (if they aren't already present). Example: !wlist edit+ TSLA GOOGL
3. Use it to remove symbols from a pre-existing watchlist (if they are present). Example: !wlist edit- TSLA GOOGL
4. Use it to get the price of all the symbols in the watchlist. Example: !wlist call 
"""
@bot.command()
async def wlist(ctx, *args):
    conn = psycopg2.connect(
        database="bot_db", 
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PW'),
        host='127.0.0.1', 
        port= '5432'
    )
    cursor = conn.cursor()

    match args[0]:

        case 'new':

            # Create table if it doesn't exist already 
            cursor.execute('''CREATE TABLE IF NOT EXISTS WATCHLIST(
                PK BIGSERIAL PRIMARY KEY,
                USER_ID VARCHAR(45) UNIQUE,
                SYMBOLS VARCHAR(1000)
            );''')
            user_id = ctx.message.author.id
            stock_symbols = args[1:]
            watchlist = []
            invalid_symbols = []

            for stock_symbol in stock_symbols:

                # Check if symbol is already in the watchlist
                if stock_symbol in watchlist:
                    continue

                # Check if the symbols are valid
                url = yahoo_fin+stock_symbol
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html5lib')
                try:
                    soup.find('h1', { 'class': 'D(ib) Fz(18px)' })
                    watchlist.append(stock_symbol.strip().upper())
                except AttributeError:
                    invalid_symbols.append(stock_symbol)

            watchlist_str = ' '.join(watchlist).strip()
            invalid_symbols_str = " ".join(invalid_symbols)
            
            cursor.execute("INSERT INTO WATCHLIST(USER_ID, SYMBOLS) VALUES('%s', %s) ON CONFLICT (USER_ID) DO UPDATE SET SYMBOLS = %s;", (user_id, watchlist_str, watchlist_str))
            
            if len(invalid_symbols) > 0:
                await ctx.send(f'''Watchlist set: `{watchlist_str}` for {ctx.message.author.mention}.
*The following symbols will not be added to your watchlist because they are invalid*: {invalid_symbols_str}'''      
                )
            else:
                await ctx.send(f'Watchlist set: `{watchlist_str}` for {ctx.message.author.mention}.')
            
            conn.commit()
            conn.close()

        case 'edit+':

            # Check if table exists 
            cursor.execute("SELECT EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s)", ('watchlist',))
            if cursor.fetchone()[0]:
                user_id = ctx.message.author.id
                stock_symbols = args[1:]
                invalid_symbols = []
                cursor.execute("SELECT SYMBOLS FROM WATCHLIST WHERE USER_ID='%s';", (user_id,))

                # Check if user had previously made a watchlist
                try:

                    old_watchlist_str = cursor.fetchone()[0]
                    new_watchlist = old_watchlist_str.split(' ')

                    for stock_symbol in stock_symbols:

                        # Check if symbol is already in the watchlist
                        if stock_symbol in new_watchlist:
                            continue

                        # Check if the symbols are valid
                        url = yahoo_fin+stock_symbol
                        response = requests.get(url, headers=headers)
                        soup = BeautifulSoup(response.content, 'html5lib')
                        try:
                            soup.find('h1', { 'class': 'D(ib) Fz(18px)' })
                            new_watchlist.append(stock_symbol.upper())
                        except AttributeError:
                            invalid_symbols.append(stock_symbol)

                    new_watchlist_str = ' '.join(new_watchlist).strip()
                    invalid_symbols_str = " ".join(invalid_symbols)

                    cursor.execute("UPDATE WATCHLIST SET SYMBOLS=%s WHERE USER_ID='%s';", (new_watchlist_str, user_id))
                    
                    if len(invalid_symbols) > 0:
                        await ctx.send(f'''Watchlist set: `{new_watchlist_str}` for {ctx.message.author.mention}.
        *The following symbols will not be added to your watchlist because they are invalid*: {invalid_symbols_str}'''      
                        )
                    else:
                        await ctx.send(f'Watchlist set: `{new_watchlist_str}` for {ctx.message.author.mention}.')
                    
                    conn.commit()
                
                except TypeError:
                    await ctx.send("Your watchlist doesn't exist yet! Create one using the `!wlist new <symbol_list>` command.")
            
            else:
                await ctx.send("Your watchlist doesn't exist yet! Create one using the `!wlist new <symbol_list>` command.")
            
            conn.close()

        case 'edit-':

            # Check if table exists 
            cursor.execute("SELECT EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s)", ('watchlist',))
            if cursor.fetchone()[0]:

                user_id = ctx.message.author.id
                symbols_to_remove = args[1:]
                cursor.execute("SELECT SYMBOLS FROM WATCHLIST WHERE USER_ID='%s';", (user_id,))

                # Check if user had previously made a watchlist
                try:
                    watchlist = cursor.fetchone()[0].split(' ')
                    new_watchlist = []
                    for symbol in watchlist:
                        if symbol not in symbols_to_remove:
                            new_watchlist.append(symbol.upper())

                    new_watchlist_str = ' '.join(new_watchlist).strip()
                    
                    cursor.execute("UPDATE WATCHLIST SET SYMBOLS=%s WHERE USER_ID='%s';", (new_watchlist_str, user_id))
                    
                    await ctx.send(f'Watchlist set: `{new_watchlist_str}` for {ctx.message.author.mention}.')
                    
                    conn.commit()
                
                except TypeError:
                    await ctx.send("Your watchlist doesn't exist yet! Create one using the `!wlist new <symbol_list>` command.")
            
            else:
                await ctx.send("Your watchlist doesn't exist yet! Create one using the `!wlist new <symbol_list>` command.")
            
            conn.close()

        case 'call':

            # Check if table exists
            cursor.execute("SELECT EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s)", ('watchlist',))
            if cursor.fetchone()[0]:
                user_id = ctx.message.author.id
                cursor.execute("SELECT SYMBOLS FROM WATCHLIST WHERE USER_ID = '%s';", (user_id,))
                
                # Check if table exists
                try:
                    watchlist = cursor.fetchone()[0].split(' ')
                    price_list = []
                    price_message = await ctx.send(f'Fetching your watchlist...')
                    for stock_symbol in watchlist:
                        url = yahoo_fin+stock_symbol
                        response = requests.get(url, headers=headers)
                        soup = BeautifulSoup(response.content, 'html5lib')
                        stock_name = soup.find('h1', { 'class': 'D(ib) Fz(18px)' }).text

                        # Getting 'At Close' price
                        fin_streamers = soup.find('div', {'class': 'D(ib) Mend(20px)'}).findChildren('fin-streamer')
                        at_close = ''
                        for i in fin_streamers:
                            at_close += i.text + ' '
                        at_close = at_close.strip()

                        # Getting 'After Hours' price
                        if soup.find('div', {'class': 'Fz(12px) C($tertiaryColor) My(0px) D(ib) Va(b)'}):
                            fin_streamers = soup.find('div', {'class': 'Fz(12px) C($tertiaryColor) My(0px) D(ib) Va(b)'}).findChildren('fin-streamer')
                            after_hours = ''
                            for i in fin_streamers[0:4]:
                                after_hours += i.text + ' '
                            after_hours = after_hours.strip()
                            price_list.append(
    f'''• **{stock_name}**
    At Close (4:00PM EDT):
    ***{at_close}***
    After Hours (07:59PM EDT):
    ***{after_hours}***'''
                             )
                        else:
                            price_list.append(
    f'''• **{stock_name}**
    At Close (4:00PM EDT):
    ***{at_close}***'''
                            )
                    await ctx.send(content='\n'.join(price_list))
                    await price_message.delete()
                except TypeError:
                    await ctx.send("Your watchlist doesn't exist yet! Create one using the `!wlist new <symbol_list>` command.")
            else:
                await ctx.send("Your watchlist doesn't exist yet! Create one using the `!wlist new <symbol_list>` command.")
            conn.close()

        case _:
            await ctx.reply('Invalid argument(s). Check `!help` to see how to use the wlist command.')
            conn.close()

@bot.command()
async def help(ctx, *args):
    await ctx.reply("Here's a link to a document that lists every command and how to use it: https://github.com/DSS3113/EquityBot/blob/master/readme.md")

bot.run(os.getenv('BOT_TOKEN'))