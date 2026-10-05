import html
import json
import logging
import os
import time
import traceback
from datetime import datetime

import yfinance as yf
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler)

load_dotenv()

logging.basicConfig(
    filename=os.getenv("LOG_FILE"),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

y, BUTTONS = range(2)
x, ABOUT, DVD, MOMENTUM, NEWS, DONE = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("---------------/start COMMAND------------------")
    logging.info("User %s started the conversation.", update)
    await update.message.reply_text("Type /symbol [ticker] to get info")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Use /start to test this bot.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(
        chat_id=os.getenv("MY_ID"), text=message, parse_mode=ParseMode.HTML
    )


def build_keybord(symbol) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(f"About ${symbol.upper()}", callback_data=str(ABOUT)),
            InlineKeyboardButton(f"DVD ${symbol.upper()}", callback_data=str(DVD)),
        ],
        [
            InlineKeyboardButton(f"News ${symbol.upper()}", callback_data=str(NEWS)),
            InlineKeyboardButton(
                f"Momentum ${symbol.upper()}", callback_data=str(MOMENTUM)
            ),
        ],
        [InlineKeyboardButton("Done", callback_data=str(DONE))],
    ]

    return InlineKeyboardMarkup(keyboard)


async def about_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("---------------ABOUT COMPANY----------------")
    logging.info("User %s pressed ABOUT COMPANY.", update)
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(
        text=f"About {symbol}\n\n{ticker.info['longBusinessSummary']}",
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=query.message.message_thread_id,
        text="About. Pick another one",
        reply_markup=reply_markup,
    )
    return BUTTONS


async def dvd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("---------------DVD----------------")
    logging.info("User %s pressed DVD.", update)
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)
    try:
        dvd_value = ticker.info["lastDividendValue"]
        now = datetime.fromtimestamp(ticker.info["lastDividendDate"])
        formatted = now.strftime("%Y-%m-%d")

        await query.answer()

        await query.edit_message_text(
            text=f"Last dvd: ${dvd_value}, {formatted}",
        )
    except:
        await query.edit_message_text(
            text="No DVD",
        )

    reply_markup = build_keybord(symbol)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=query.message.message_thread_id,
        text="Last DVD. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def news_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("---------------news_company----------------")
    logging.info("User %s pressed NEWS COMPANY.", update)
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    news = yf.Search(ticker.ticker, news_count=3).news
    datepublished0 = datetime.fromtimestamp(news[0]['providerPublishTime']).strftime('%Y-%m-%d %H:%M')
    datepublished1 = datetime.fromtimestamp(news[1]['providerPublishTime']).strftime('%Y-%m-%d %H:%M')
    datepublished2 = datetime.fromtimestamp(news[2]['providerPublishTime']).strftime('%Y-%m-%d %H:%M')
   
    # hardcoded 3 newest news
    msg = (
        f"News for {ticker.info['longName']}:\n\n"
        f"Title: {news[0]['title']}\n\n"
        f"Time published: {datepublished0}\n"
        f"Related tickers: {news[0].get("relatedTickers", "")}\n"
        f"News Type: {news[0].get("type", "")}\n"
        f"Link: {news[0].get('link',"")}\n"
        "----------------------------------------\n\n"
        f"Title: {news[1]['title']}\n\n"
        f"Time published: {datepublished1}\n"
        f"Related tickers: {news[1].get("relatedTickers", "")}\n"
        f"News Type: {news[1].get("type", "")}\n"
        f"Link: {news[1].get('link',"")}\n"
        "----------------------------------------\n\n"
        f"Title: {news[2]['title']}\n\n"
        f"Time published: {datepublished2}\n"
        f"Related tickers: {news[2].get("relatedTickers", "")}\n"
        f"News Type: {news[2].get("type", "")}\n"
        f"Link: {news[2].get('link',"")}\n"
        "----------------------------------------\n"
    )
    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(text=msg)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=query.message.message_thread_id,
        text="Company news. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def momentum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("---------------momentum------------------")
    logging.info("User %s pressed MOMENTUM.", update)
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    hist_1mo = ticker.history(period="1mo").iloc[0]["Open"].round(2)
    hist_3mo = ticker.history(period="3mo").iloc[0]["Open"].round(2)
    hist_6mo = ticker.history(period="6mo").iloc[0]["Open"].round(2)
    hist_12mo = ticker.history(period="1y").iloc[0]["Open"].round(2)
    hist_YTD = ticker.history(period="ytd").iloc[0]["Open"].round(2)
    current_price = ticker.info["currentPrice"]
    msg = f"""{ticker.info['longName']} ${current_price}\nMomentum\n
        1 month return: {((current_price / hist_1mo - 1) * 100).round(2)}%\n
        3 months return: {((current_price / hist_3mo - 1) * 100).round(2)}%\n
        6 months return: {((current_price / hist_6mo - 1) * 100).round(2)}%\n
        12 months return: {((current_price / hist_12mo - 1) * 100).round(2)}%\n
        YTD return: {((current_price / hist_YTD - 1) * 100).round(2)}%\n
        50 day MA: ${ticker.info['fiftyDayAverage']}\n
        200 day MA: ${ticker.info['twoHundredDayAverage']}\n
        """
    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(text=msg)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=query.message.message_thread_id,
        text="Momentum. Pick another one",
        reply_markup=reply_markup,
    )
    return BUTTONS


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("---------------DONE------------------")
    logging.info("User %s pressed DONE", update)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")

    return ConversationHandler.END


# prints buttons /symbol
async def ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    start_time = time.perf_counter()
    await update.message.reply_text(f"Working on {context.args[0]}")
    logging.info("---------------/symbol COMMAND------------------")
    logging.info("User %s started the conversation.", update)
    chat_type = update.message.chat.type
    chat_id = update.message.chat.id
    thread_id = update.message.message_thread_id

    """
    A not very good implementation of number of calls
    with open("counter.txt", "r") as f:
        count = f.read()

    with open("counter.txt", "w") as f:
        new_count = int(count) + 1
        f.write(str(new_count))
    """

    """
        selected_room is for supergroups.
        In my case i deployed this bot to a group
        and it was allowed to only in a given room
    """
    with open("selected_room.json", "r+") as f:
        data = json.load(f)
    if (
        chat_type == "private"
        or str(chat_id) in data
        and thread_id == data[str(chat_id)]
    ):
        symbol = context.args[0]
        end_time = time.perf_counter()
        logging.info(f"Took {end_time - start_time} seconds before calling YF")
        start_time = time.perf_counter()
        ticker = yf.Ticker(symbol.upper())

        try:
            daily_prec_change = (
                (ticker.info["currentPrice"] - ticker.info["previousClose"])
                / ticker.info["previousClose"]
                * 100
            )
            basic_info = f"""${symbol.upper()} {ticker.info['longName']}\n
            Current Price: ${ticker.info['currentPrice']}, {round(daily_prec_change, 2)}%\n
            Market Cap: ${ticker.info['marketCap']:_}\n
            52 Week High: ${ticker.info['fiftyTwoWeekHigh']}\n
            52 Week Low: ${ticker.info['fiftyTwoWeekLow']}\n
            52 Change: ${round(ticker.info['52WeekChange']*100,2)}\n
            Volume: {ticker.info['volume']:_}\n
            Average Volume: {ticker.info['averageVolume']:_}"""

            reply_markup = build_keybord(symbol)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.message.message_thread_id,
                text=basic_info,
            )

            await update.message.reply_text(
                text="Basic info. Pick one", reply_markup=reply_markup
            )

            end_time = time.perf_counter()
            logging.info(f"Took {end_time - start_time} seconds after calling YF")
            return BUTTONS

        except KeyError:
            await update.message.reply_text("Bad ticker. Try again")
        except IndexError:
            await update.message.reply_text("Bad ticker. Try again")


def main() -> None:
    application = Application.builder().token(os.getenv("TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help_command),
            CommandHandler("symbol", ticker_command),
        ],
        states={
            BUTTONS: [
                CallbackQueryHandler(about_company, pattern="^" + str(ABOUT) + "$"),
                CallbackQueryHandler(dvd, pattern="^" + str(DVD) + "$"),
                CallbackQueryHandler(news_company, pattern="^" + str(NEWS) + "$"),
                CallbackQueryHandler(momentum, pattern="^" + str(MOMENTUM) + "$"),
                CallbackQueryHandler(done, pattern="^" + str(DONE) + "$"),
            ]
        },
        fallbacks=[
            CommandHandler("symbol", ticker_command),
            CommandHandler("start", start),
        ],
        conversation_timeout=40,
        per_chat=True,
        per_user=True,
        per_message=False,
    )
    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("symbol", ticker_command))

    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
