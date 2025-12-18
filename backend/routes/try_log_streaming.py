# vps1_backend.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import requests

app = FastAPI()

VPS2_URL = "https://l7i1ghaqgdha36-3000.proxy.runpod.net/infer"

@app.post("/run-inference")
def run_inference():
    def stream():
        with requests.post(VPS2_URL, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    yield line.decode() + "\n"

    return StreamingResponse(stream(), media_type="text/plain")
