import requests
import urllib3
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://byte-sql-federation-extends.trycloudflare.com/analyze-echo"

# Try with echo_video_base64
try:
    print("Testing with echo_video_base64")
    res1 = requests.post(URL, json={"echo_video_base64": "dummy_base64_string"}, timeout=10, verify=False)
    print("Status 1:", res1.status_code)
    try:
        print("Response 1:", res1.json())
    except:
        print("Response 1 string:", res1.text)
except Exception as e:
    print("Error 1:", e)

print("-" * 30)

# Try with echo_image_base64
try:
    print("Testing with echo_image_base64")
    res2 = requests.post(URL, json={"echo_image_base64": "dummy_base64_string"}, timeout=10, verify=False)
    print("Status 2:", res2.status_code)
    try:
        print("Response 2:", res2.json())
    except:
        print("Response 2 string:", res2.text)
except Exception as e:
    print("Error 2:", e)
