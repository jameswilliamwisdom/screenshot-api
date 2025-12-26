import asyncio
from playwright.async_api import async_playwright

async def take_screenshot(url: str, width: int = 1200, watermark: bool = False):
    """
    Takes a screenshot of a given URL using Playwright.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=30000)
            await page.set_viewport_size({"width": width, "height": 800})
            screenshot_bytes = await page.screenshot(type="png")

            if watermark:
                # Add watermark
                from PIL import Image, ImageDraw, ImageFont
                import io

                image = Image.open(io.BytesIO(screenshot_bytes))
                draw = ImageDraw.Draw(image)
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except IOError:
                    font = ImageFont.load_default()
                draw.text((10, 10), "Test Screenshot", font=font, fill=(0, 0, 0, 128))

                buf = io.BytesIO()
                image.save(buf, format="PNG")
                screenshot_bytes = buf.getvalue()

            return screenshot_bytes
        except Exception as e:
            raise Exception(f"Error taking screenshot: {e}")
        finally:
            await browser.close()
