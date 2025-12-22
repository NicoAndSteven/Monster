import os

STORAGE_PATH = "./storage"
# In a real app, use environment variables
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "your_key_here")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "your_key_here")

# Create storage directory if it doesn't exist
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)
