import sys
try:
    import cv2
    print("cv2 imported successfully!")
    print(cv2.__version__)
except Exception as e:
    print(f"Error importing cv2: {e}")
