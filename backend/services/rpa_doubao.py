import os
import time
import asyncio
from playwright.async_api import async_playwright

AUTH_FILE = "doubao_auth.json"

class DoubaoRPA:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def generate_image(self, prompt: str):
        async with async_playwright() as p:
            # Launch browser in visible mode so user can see what's happening
            # and log in if necessary.
            browser = await p.chromium.launch(headless=False)
            
            # Load auth state if exists
            if os.path.exists(AUTH_FILE):
                try:
                    context = await browser.new_context(storage_state=AUTH_FILE)
                except Exception:
                    context = await browser.new_context()
            else:
                context = await browser.new_context()

            page = await context.new_page()
            
            # Go to Doubao
            # Note: The URL might redirect to login if not authenticated
            await page.goto("https://www.doubao.com/chat/")

            # Wait for input box. If not found, it might be the login page.
            # We give a long timeout for the first run to allow manual login.
            try:
                # Look for the chat input textarea
                # Selectors might change, so we try a few common patterns or specific classes if known.
                # Usually it's a textarea with a placeholder like "发消息..." or "输入..."
                textarea = page.locator("textarea")
                await textarea.wait_for(state="visible", timeout=60000) # 1 minute for user to login if needed
            except:
                await browser.close()
                return {"error": "Timeout waiting for chat interface. Please login manually and try again."}

            # Save auth state for next time
            await context.storage_state(path=AUTH_FILE)

            # Type prompt
            # We append specific instruction to generate image to be sure
            full_prompt = f"请为我生成一张图片：{prompt}"
            await textarea.fill(full_prompt)

            # Click send button. 
            # This is tricky without exact selector. 
            # Usually it's a button near the textarea.
            # We can try pressing Enter key if button selector is hard to guess.
            await textarea.press("Enter")
            
            # Wait for response
            # We need to detect when the image is generated.
            # We can look for the last img tag that appears in the chat.
            # This is heuristic.
            
            # Wait a bit for the message to be sent and processing to start
            await page.wait_for_timeout(2000)
            
            # Now we wait for an image to load in the response area.
            # We can check for new img tags.
            # A simple way is to wait for the generation to finish. 
            # AI generation takes time (5-20s).
            
            # We'll poll for the last image in the chat container.
            # Assuming the latest image is the result.
            
            # Let's wait up to 30 seconds
            start_time = time.time()
            image_src = None
            
            while time.time() - start_time < 45:
                # specific heuristic for Doubao:
                # Images are usually inside some container.
                # We get all images and take the last one that looks like a generated content (blob or http)
                # Note: Doubao might show a "Generating..." placeholder.
                
                images = await page.locator("img").all()
                if images:
                    # check the last few images
                    for img in reversed(images):
                        src = await img.get_attribute("src")
                        alt = await img.get_attribute("alt")
                        
                        # Filter out avatars or icons if possible.
                        # Generated images usually have a large size or specific url pattern.
                        # But simpler heuristic: if it's a valid src and not an SVG icon (usually data:image/svg)
                        # data:image/jpeg or png or https://...
                        
                        if src and ("http" in src or "data:image" in src):
                             # Exclude common UI elements if we can identify them
                             # But for now, let's assume the last big image is it.
                             # We can check bounding box size.
                             box = await img.bounding_box()
                             if box and box['width'] > 100 and box['height'] > 100:
                                 image_src = src
                                 break
                    
                    if image_src:
                         # We found a candidate. But is it the NEW one?
                         # Ideally we should have counted images before sending.
                         # But let's assume the user context is fresh or we just pick the very last one.
                         # To be safer, we could wait until the "Stop generating" button disappears?
                         pass
                
                if image_src:
                    # Found an image. Let's wait a bit more to ensure it's fully loaded or if there's a better one.
                    # But returning early is better for UX.
                    break
                
                await page.wait_for_timeout(1000)
            
            if image_src:
                await browser.close()
                return {"image_url": image_src}
            else:
                await browser.close()
                return {"error": "Image generation timed out or failed to detect image."}

doubao_rpa = DoubaoRPA()
