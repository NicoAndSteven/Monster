import requests
from ..config import settings
from ..models.novel import GenerationMode
from fastapi import HTTPException
import time

def clean_ai_response(text: str) -> str:
    return text.replace("【", "").replace("】", "")

def _generate_via_api(prompt: str, context: str = "") -> str:
    """
    Simulate generating content via API (e.g., Qwen, Claude).
    """
    # In a real scenario, make the actual HTTP request here.
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    return clean_ai_response(f"[API Mode] Generated chapter content based on context and prompt.\n\nPROMPT:\n{full_prompt}")

def _generate_via_rpa(prompt: str, context: str = "") -> str:
    """
    Simulate generating content via RPA (Robotic Process Automation).
    In a real scenario, this would use Playwright or Selenium to:
    1. Open a browser
    2. Navigate to an AI chat interface (e.g., ChatGPT, Claude web)
    3. Input the prompt
    4. Scrape the response
    """
    # Simulation delay to mimic browser interaction
    time.sleep(2)
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    return clean_ai_response(f"[RPA Mode] Scraped chapter content based on context and prompt.\n\n(Note: To enable real RPA, implement Playwright/Selenium logic here.)\n\nPROMPT:\n{full_prompt}")

def generate_chapter_text(prompt: str, mode: GenerationMode = GenerationMode.API, context: str = "") -> str:
    if mode == GenerationMode.RPA:
        return _generate_via_rpa(prompt, context)
    else:
        return _generate_via_api(prompt, context)
