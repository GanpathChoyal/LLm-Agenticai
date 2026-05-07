import os
import google.generativeai as genai

# Testing the CRITIC key to see if it works
api_key = "AIzaSyDZbV3XzR1ibyaStlK7S3P2I7VHGfov91Q"

try:
    genai.configure(api_key=api_key)
    print(f"Checking status for key: {api_key[:10]}...")
    models = genai.list_models()
    print("Success! This key is ACTIVE.")
except Exception as e:
    print(f"Error for this key: {e}")
