"""
Utility functions for image base64 encoding/decoding
"""
import base64
from pathlib import Path
from typing import Optional
import io
from PIL import Image


def image_file_to_base64(file_path: str) -> Optional[str]:
    """
    Convert image file to base64 string
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Base64 encoded string with data URI prefix, or None if file doesn't exist
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
            
        with open(path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Determine MIME type from extension
        ext = path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_types.get(ext, 'image/png')
        
        # Return as data URI
        return f"data:{mime_type};base64,{encoded}"
        
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None


def base64_to_image_file(base64_string: str, output_path: str) -> bool:
    """
    Convert base64 string to image file
    
    Args:
        base64_string: Base64 encoded string (with or without data URI prefix)
        output_path: Path where to save the image file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove data URI prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',', 1)[1]
            
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(image_data)
            
        return True
        
    except Exception as e:
        print(f"Error converting base64 to image: {e}")
        return False


def pil_image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """
    Convert PIL Image object to base64 string
    
    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Base64 encoded string with data URI prefix
    """
    try:
        buffered = io.BytesIO()
        image.save(buffered, format=format)
        encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        mime_type = f"image/{format.lower()}"
        return f"data:{mime_type};base64,{encoded}"
        
    except Exception as e:
        print(f"Error converting PIL image to base64: {e}")
        return ""


def base64_to_pil_image(base64_string: str) -> Optional[Image.Image]:
    """
    Convert base64 string to PIL Image object
    
    Args:
        base64_string: Base64 encoded string (with or without data URI prefix)
        
    Returns:
        PIL Image object or None if conversion fails
    """
    try:
        # Remove data URI prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',', 1)[1]
            
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Create PIL Image
        image = Image.open(io.BytesIO(image_data))
        return image
        
    except Exception as e:
        print(f"Error converting base64 to PIL image: {e}")
        return None


def get_image_size_kb(base64_string: str) -> float:
    """
    Get the size of base64 encoded image in KB
    
    Args:
        base64_string: Base64 encoded string
        
    Returns:
        Size in kilobytes
    """
    try:
        # Remove data URI prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',', 1)[1]
            
        # Calculate size
        size_bytes = len(base64_string) * 3 / 4  # Base64 encoding increases size by ~33%
        return size_bytes / 1024
        
    except Exception as e:
        print(f"Error calculating image size: {e}")
        return 0.0
