import os

from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi_x402 import init_x402, pay, PaymentMiddleware

from sentiment import analyze_sentiment, analyze_market_sentiment, fetch_crypto_data

load_dotenv()

app = FastAPI(
    title="Crypto Sentiment API",
    description="AI-powered cryptocurrency sentiment analysis with x402 micropayments",
    version="1.0.0",
)

# Initialize x402 payment configuration
init_x402(
    pay_to=os.getenv("PAY_TO_ADDRESS", "0x0000000000000000000000000000000000000000"),
    network=os.getenv("X402_NETWORK", "base-sepolia"),
)

# Add payment middleware
app.add_middleware(PaymentMiddleware)


@app.get("/")
async def root():
    """Health check and API information (free)."""
    return {
        "name": "Crypto Sentiment API",
        "version": "1.0.0",
        "description": "AI-powered cryptocurrency sentiment analysis",
        "endpoints": {
            "/": {"price": "free", "description": "This endpoint"},
            "/sentiment/{symbol}": {"price": "$0.01", "description": "Sentiment for a specific coin"},
            "/sentiment/market": {"price": "$0.05", "description": "Overall market sentiment"},
        },
        "payment": {
            "protocol": "x402",
            "network": os.getenv("X402_NETWORK", "base-sepolia"),
            "currency": "USDC",
        },
    }


@app.get("/test/sentiment/{symbol}")
async def test_coin_sentiment(symbol: str):
    """Test endpoint - returns mock sentiment with real market data (no API key needed)."""
    symbol = symbol.upper()
    valid_symbols = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "AVAX", "LINK"]

    if symbol not in valid_symbols:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid symbol. Supported: {', '.join(valid_symbols)}",
        )

    # Fetch real market data from CoinGecko
    market_data = await fetch_crypto_data(symbol)

    # Generate mock sentiment based on price change
    price_change = market_data.get("price_change_24h", 0) or 0
    if price_change > 3:
        sentiment, confidence = "bullish", 0.82
    elif price_change > 0:
        sentiment, confidence = "bullish", 0.65
    elif price_change > -3:
        sentiment, confidence = "bearish", 0.58
    else:
        sentiment, confidence = "bearish", 0.75

    return {
        "symbol": symbol,
        "sentiment": sentiment,
        "confidence": confidence,
        "factors": [
            f"24h price change: {price_change:.1f}%",
            f"Market cap rank: #{market_data.get('market_cap_rank', 'N/A')}",
            f"Community sentiment: {market_data.get('sentiment_votes_up', 50):.0f}% positive",
        ],
        "summary": f"{symbol} is showing {sentiment} signals based on recent price action and market data.",
        "market_data": market_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "_note": "This is mock sentiment data for testing. Real endpoints use AI analysis.",
    }


@pay("$0.05")
@app.get("/sentiment/market")
async def get_market_sentiment():
    """Get overall crypto market sentiment analysis ($0.05)."""
    try:
        result = await analyze_market_sentiment()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@pay("$0.01")
@app.get("/sentiment/{symbol}")
async def get_coin_sentiment(symbol: str):
    """Get sentiment analysis for a specific cryptocurrency ($0.01)."""
    symbol = symbol.upper()
    valid_symbols = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "AVAX", "LINK"]

    if symbol not in valid_symbols:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid symbol. Supported: {', '.join(valid_symbols)}",
        )

    try:
        result = await analyze_sentiment(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
