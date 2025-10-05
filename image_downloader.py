import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path

# This function sanitizes (cleans) a filename by removing unsafe characters.
# It ensures the file name is safe to use in all operating systems.
def safe_filename(name:str) -> str:
    # Extract only the name part (remove any folder paths)
    name = Path(name).name
    # Replace any characters that are not letters, digits, dots, underscores, or hyphens with "_"
    return re.sub(r'[^A-Za-z0-9._-]','_',name)

# This function extracts the file extension (like .jpg or .png) from a given image URL.
def get_extension_from_url(image_url:str) -> str:
    # Parse the URL to get its path part (the part after the domain)
    path = urlparse(image_url).path
    # Split the path into the main part and the extension
    _, ext = os.path.splitext(path)
    # Return the extension in lowercase (e.g. ".JPG" → ".jpg")
    return ext.lower()

# This function downloads an image using streaming (chunk by chunk) to avoid memory overload.
def download_image_stream(image_url:str,
                          name:str,
                          folder:str = 'images',
                          timeout:int = 10) -> bytes:
    # Get the extension from the URL
    ext = get_extension_from_url(image_url)
    # Make the file name safe
    safe_name = safe_filename(name)
    # Create the folder (if it doesn't exist)
    os.makedirs(folder,exist_ok=True)
    # Build the full path where the image will be saved
    image_path = os.path.join(folder,f'{safe_name}.{ext}')
    if os.path.exists(image_path):
        raise FileExistsError(f'File {safe_name} already exists')

    # Send a GET request with streaming enabled and a simple User-Agent
    headers = {'User-Agent': 'python-requests/1.0'}
    try:
        # Send the GET request with streaming enabled
        with requests.get(image_url, stream=True,timeout= timeout) as r:
            # Raise an error if the request failed (e.g. 404 or 403)
            r.raise_for_status()
            # Get the Content-Type header (e.g. 'image/jpeg')
            content_type = r.headers.get('content-type') or r.headers.get('content-type')

            # Check if the file already exists to prevent overwriting
            if not ext and content_type.startswith('image/'):
                guessed = '.' + content_type.split('/')[-1].lower()
                image_path = os.path.join(folder,f'{safe_name}{guessed}')

            # Open the file in binary write mode and save the data chunk by chunk
            with open(image_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
        # Return the saved image path
        return image_path

    # Handle network-related errors
    except requests.RequestException as e:
        print(f'Failed to download {safe_name} from {image_url}: {e}')
        # If partial file exists, remove it
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass
        return None
    # Handle any other unexpected errors
    except Exception as e :
        print(f'Failed to download {safe_name} from {image_url}: {e}')
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass
        return None

# Main program entry point
if __name__ == '__main__':
    # Ask user for the image URL and name
    image_url = input("Enter image URL: ")
    image_name = input("Enter image name: ")

    try:
        print("Downloading image...")
        # Try to download the image using the function above
        saved_path = download_image_stream(image_url, image_name)
        print(f"Image saved at: {saved_path}")
    except Exception as e:
        print(f"Error: {e}")