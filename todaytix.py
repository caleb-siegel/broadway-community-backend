import requests

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

        data = response.json()

        today_tix_price = data["data"]["fromPrice"]["value"]

        return today_tix_price