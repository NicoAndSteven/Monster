import os
import shutil
import uuid
try:
    from gradio_client import Client
except ImportError:
    Client = None

from ..config import settings

class ZImageGenerator:
    def __init__(self):
        self.client = None
        if Client:
            try:
                # Initialize client (might fail if network is down or SSL issues)
                self.client = Client("Tongyi-MAI/Z-Image-Turbo")
                print("Z-Image-Turbo client initialized successfully.")
            except Exception as e:
                print(f"Warning: Failed to initialize Z-Image-Turbo client: {e}")
        else:
            print("Warning: gradio_client not installed. Z-Image-Turbo will not work.")

    def generate_image(self, prompt: str) -> dict:
        if not self.client:
             if Client is None:
                 return {"error": "gradio_client module not found. Please install it: pip install gradio_client"}
             return {"error": "Z-Image-Turbo client not initialized (check network/SSL)."}

        try:
            # The API parameters based on backend/eg/imageGenerate.py
            # Note: predict() is blocking. For async, use submit() but that requires callback handling.
            # Since this is called from an async path in FastAPI, blocking call might block the event loop.
            # Ideally we should run this in a threadpool.
            
            print(f"Generating image with prompt: {prompt}")
            result = self.client.predict(
                prompt=prompt,
                resolution="1024x1024 ( 1:1 )",
                seed=42, # We might want to randomize this
                steps=8,
                shift=3,
                random_seed=True,
                gallery_images=[],
                api_name="/generate"
            )
            
            # result logic: gradio_client typically returns the file path for Image outputs
            image_path = None
            
            # Handle different return types
            if isinstance(result, str):
                image_path = result
            elif isinstance(result, (list, tuple)):
                # If multiple outputs, take the first file path
                for item in result:
                    # Case 1: item is the path string
                    if isinstance(item, str):
                        image_path = item
                        if os.path.exists(image_path):
                            break
                    # Case 2: item is a dict with file info
                    if isinstance(item, dict):
                        if 'name' in item: # sometimes it returns file info dict
                            image_path = item['name']
                            break
                        if 'image' in item: # sometimes {'image': 'path'}
                            image_path = item['image']
                            break
                    # Case 3: item is a list of dicts (e.g. Gallery output)
                    # Structure: [{'image': 'path', 'caption': None}]
                    if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
                        first_img = item[0]
                        if 'image' in first_img:
                            image_path = first_img['image']
                            break
                        if 'name' in first_img:
                            image_path = first_img['name']
                            break
            
            print(f"DEBUG: Extracted image_path: {image_path}")

            if image_path:
                # Check if path exists as-is
                if not os.path.exists(image_path):
                    print(f"DEBUG: Path not found as-is: {image_path}. Trying variations...")
                    
                    # Variation 1: Fix double backslashes
                    p1 = image_path.replace("\\\\", "\\")
                    if os.path.exists(p1):
                        image_path = p1
                        print(f"DEBUG: Found path with double backslash fix: {image_path}")
                    else:
                        # Variation 2: Replace backslashes with forward slashes
                        p2 = image_path.replace("\\", "/")
                        if os.path.exists(p2):
                            image_path = p2
                            print(f"DEBUG: Found path with forward slash fix: {image_path}")
                        else:
                            # Variation 3: Both
                            p3 = image_path.replace("\\\\", "\\").replace("\\", "/")
                            if os.path.exists(p3):
                                image_path = p3
                                print(f"DEBUG: Found path with combined fix: {image_path}")

            if not image_path or not os.path.exists(image_path):
                 print(f"DEBUG: Path does not exist: {image_path}")
                 return {"error": f"Failed to get valid image path from result: {result}"}

            # Move to storage to make it accessible via web
            filename = f"z_gen_{uuid.uuid4().hex}.png"
            dest_path = os.path.join(settings.STORAGE_PATH, filename)
            
            # Ensure storage dir exists
            os.makedirs(settings.STORAGE_PATH, exist_ok=True)
            
            shutil.move(image_path, dest_path)
            
            # Return URL relative to server root
            # FastAPI mounts /data to STORAGE_PATH
            url = f"/data/{filename}"
            
            return {"image_url": url}

        except Exception as e:
            print(f"Error generating image: {e}")
            return {"error": str(e)}

z_image_generator = ZImageGenerator()
