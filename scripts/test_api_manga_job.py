import urllib.request
import json
import time

data = json.dumps({
    "image_id": "9446774f-615d-43f0-917a-436a317ba0ff",
    "mode": "upscale",
    "model": "realesrgan-x4plus-anime",
    "scale": 4,
    "preset": "manga_crisp",
    "output_format": "png"
}).encode("utf-8")

req = urllib.request.Request("http://127.0.0.1:8000/api/v1/jobs", data=data, headers={"Content-Type": "application/json"})
job_res = json.loads(urllib.request.urlopen(req).read().decode())
job_id = job_res["job_id"]
print("Job created:", job_id)

for _ in range(30):
    status_res = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8000/api/v1/jobs/{job_id}").read().decode())
    status = status_res["status"]
    print(f"Job status: {status}, progress: {status_res.get('progress')}, message: {status_res.get('message')}")
    if status in ("completed", "failed"):
        print("Final job detail:", status_res)
        break
    time.sleep(1)

