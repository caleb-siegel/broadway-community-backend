import requests
from db import db
from models import Event

ids = [23379, 37219, 41018, 38749, 26018, 13709, 34895, 31936, 14748, 37579, 384, 1]

def todaytix_loop():
    for num in ids:
        if num:

            url = f"https://content-service.tixuk.io/api/v3/products/{num}"

            headers = {"accept": "application/json"}

            response = requests.get(url, headers=headers)

            data = response.json()

            print(f'{data["data"]["name"]}: ${data["data"]["fromPrice"]["value"]}')

def todaytix_fetch(id):
    
    if id:

        url = f"https://content-service.tixuk.io/api/v3/products/{id}"

        headers = {"accept": "application/json"}

        response = requests.get(url, headers=headers)

        # today_tix_price = data["data"]["fromPrice"]["value"]
        print(response.json()["data"]["runTimeAndIntermission"])
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Failed to fetch tickets from {url}: {response.status_code}, {response.text}')
            return None

# todaytix_fetch(384)