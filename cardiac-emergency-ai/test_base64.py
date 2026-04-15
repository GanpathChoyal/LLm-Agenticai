import cv2
import numpy as np
import base64

try:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    ret, buffer = cv2.imencode('.jpg', frame)
    # the issue:
    encoded = base64.b64encode(buffer).decode('utf-8')
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
