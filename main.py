import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_NAME = "Breemarh Intelligent Bot"
DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/tokens/"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        f"Welcome to {BOT_NAME}! 🚀\n\n"
        "Your Solana token research assistant.\n\n"
        "Commands:\n"
        "/start - Show welcome message\n"
        "/help - Show available commands\n"
        "/analyze ADDRESS - Analyze a Solana token\n"
    )
    await update.effective_message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Use /analyze followed by a Solana token address.\n\n"
        "Example:\n"
        "/analyze YOUR_TOKEN_ADDRESS\n\n"
        "This version checks basic market data only."
    )
    await update.effective_message.reply_text(message)


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not context.args:
        await message.reply_text(
            "Please provide a token address.\n"
            "Example: /analyze YOUR_TOKEN_ADDRESS"
        )
        return

    address = context.args[0].strip()
    await message.reply_text("🔎 Checking token market data...")

    try:
        response = requests.get(
            DEXSCREENER_URL + address,
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        pairs = data.get("pairs") or []
        solana_pairs = [
            pair for pair in pairs
            if pair.get("chainId") == "solana"
        ]

        if not solana_pairs:
            await message.reply_text(
                "No Solana trading pairs were found for this address."
            )
            return

        pair = max(
            solana_pairs,
            key=lambda item: (
                (item.get("liquidity") or {}).get("usd") or 0
            )
        )

        token = pair.get("baseToken") or {}
        liquidity = (pair.get("liquidity") or {}).get("usd") or 0
        volume = (pair.get("volume") or {}).get("h24") or 0
        price = pair.get("priceUsd", "Unknown")

        ratio = volume / liquidity if liquidity > 0 else None

        if ratio is None:
            ratio_text = "Unavailable"
            ratio_status = "UNVERIFIED"
        else:
            ratio_text = f"{ratio:.2f}x"
            if 2 <= ratio <= 3:
                ratio_status = "PASS"
            else:
                ratio_status = "OUTSIDE PREFERRED RANGE"

        pair_created = pair.get("pairCreatedAt")
        if pair_created:
            pair_age_text = (
                "Pair creation timestamp: "
                + str(pair_created)
                + " (milliseconds)"
            )
        else:
            pair_age_text = "Pair creation time: unavailable"

        report = (
            "📊 SOLANA TOKEN REPORT\n\n"
            f"Name: {token.get('name', 'Unknown')}\n"
            f"Symbol: {token.get('symbol', 'Unknown')}\n"
            f"Price: ${price}\n"
            f"Liquidity: ${liquidity:,.2f}\n"
            f"24H Volume: ${volume:,.2f}\n"
            f"Volume/Liquidity: {ratio_text}\n"
            f"Ratio Check: {ratio_status}\n"
            f"{pair_age_text}\n"
            f"Chart: {pair.get('url', 'Unavailable')}\n\n"
            "⚠️ Preliminary market-data report only.\n"
            "Historical drawdown, 4H reversal, retest, "
            "and holder quality are not yet verified."
        )

        await message.reply_text(report)

    except requests.RequestException:
        await message.reply_text(
            "Market-data request failed. Please try again later."
        )
    except (ValueError, TypeError, KeyError):
        await message.reply_text(
            "The market-data response could not be processed."
        )


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing from Railway Variables."
        )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze))

    print(f"{BOT_NAME} is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
