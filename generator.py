import os
import requests
from config import REPLICATE_API_TOKEN

def generate_coloring_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "a9758cb4b27f4c8b8533f6c8efb8d72f6924ba63e188b2cf14d59c6d3ed18078",
        "input": {
            "prompt": f"{prompt}, coloring page, black and white, line art, for kids, no color, high contrast",
            "num_outputs": 1
        }
    }
    response = requests.post(url, json=data, headers=headers)
    prediction = response.json()
    get_url = prediction["urls"]["get"]
    while True:
        result = requests.get(get_url, headers=headers).json()
        if result["status"] == "succeeded":
            return result["output"][0]
        elif result["status"] == "failed":
            raise Exception("Image generation failed")
