import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_x402 import init_x402, pay, PaymentMiddleware

from screenshot import take_screenshot

load_dotenv()

app = FastAPI(
    title="Screenshot API",
    description="API for taking screenshots of web pages with x402 micropayments",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize x402 payment configuration
init_x402(
    pay_to=os.getenv("PAY_TO_ADDRESS", "0x6b21227Ca9Bb3590BB62ff60BA0EFbBf9Ba22ACC"),
    network=os.getenv("X402_NETWORK", "base"),
)

# Add payment middleware
app.add_middleware(PaymentMiddleware)


@app.get("/")
async def root():
    """Serve the landing page."""
    return FileResponse('static/index.html')


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@pay("$0.01")
@app.post("/screenshot")
async def screenshot(payload: dict = Body(...)):
    """Take a screenshot of a URL."""
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        image_bytes = await take_screenshot(url)
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/screenshot")
async def test_screenshot(url: str):
    """Take a test screenshot of a URL with a watermark."""
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        image_bytes = await take_screenshot(url, width=800, watermark=True)
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
