import requests
import base64
import urllib3

urllib3.disable_warnings()

URL = "https://byte-sql-federation-extends.trycloudflare.com/analyze-echo"

# 1x1 black pixel PNG
img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

payloads = [
    {"echo_image_base64": img_b64},
    {"echo_video_base64": img_b64},
    {"echo_base64": img_b64},
    {"image": img_b64},
    {"video": img_b64}
]

for p in payloads:
    key = list(p.keys())[0]
    print(f"Testing key: {key}")
    try:
        res = requests.post(URL, json=p, timeout=10, verify=False)
        print("Status:", res.status_code)
        try:
            print("Response:", res.json())
        except:
            pass
    except Exception as e:
        print("Error:", e)
    print("-" * 30)
