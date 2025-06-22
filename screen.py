from PIL import ImageGrab
from io import BytesIO
def capture_screenshot() -> bytes:
    """
    Grabs the full screen and returns it as PNG bytes.
    """
    # take screenshot
    img = ImageGrab.grab()
    # write into in-memory buffer as PNG
    buf = BytesIO()
    img.save(buf, format="PNG")
    # return raw bytes
    return buf.getvalue()