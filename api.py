import requests

partnerize_tracking_link = "https://stubhub.prf.hn/click/camref:1100lTenp/destination:"

show_api_endpoints = [
    {"name": "Hamilton", "link": "https://api.stubhub.net/catalog/categories/35042/events?exclude_parking_passes=true&latitude=40.759033203125&longitude=-73.98674774169922&max_distance_in_meters=1000"},
    {"name": "Six", "link": "https://api.stubhub.net/catalog/categories/82392/events?exclude_parking_passes=true&latitude=40.7599414&longitude=-73.98690909999999&max_distance_in_meters=1000"},
    {"name": "& Juliet", "link": "https://api.stubhub.net/catalog/categories/127739/events?exclude_parking_passes=true&latitude=40.75594711303711&longitude=-73.98497772216797&max_distance_in_meters=1000"},
    {"name": "MJ", "link": "https://api.stubhub.net/catalog/categories/177138/events?exclude_parking_passes=true&latitude=40.7631716&longitude=-73.9845438&max_distance_in_meters=1000"},
    {"name": "The Outsiders", "link": "https://api.stubhub.net/catalog/categories/102774/events?exclude_parking_passes=true&latitude=40.75878524780273&longitude=-73.98772430419922&max_distance_in_meters=1000"},
    {"name": "The Book of Mormon", "link": "https://api.stubhub.net/catalog/categories/150057581/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Wicked", "link": "https://api.stubhub.net/catalog/categories/3682/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "The Lion King", "link": "https://api.stubhub.net/catalog/categories/1534/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Hell's Kitchen", "link": "https://api.stubhub.net/catalog/categories/150087389/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Moulin Rouge", "link": "https://api.stubhub.net/catalog/categories/11874/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "The Notebook", "link": "https://api.stubhub.net/catalog/categories/430684/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Harry Potter and the Cursed Child", "link": "https://api.stubhub.net/catalog/categories/36402/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Back to the Future", "link": "https://api.stubhub.net/catalog/categories/146928/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "The Great Gatsby", "link": "https://api.stubhub.net/catalog/categories/42838/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Oh, Mary", "link": "https://api.stubhub.net/catalog/categories/150204986/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Aladdin", "link": "https://api.stubhub.net/catalog/categories/12721/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Chicago", "link": "https://api.stubhub.net/catalog/categories/14222/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Cabaret", "link": "https://api.stubhub.net/catalog/categories/4987/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Water for Elephants", "link": "https://api.stubhub.net/catalog/categories/150043364/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Elf", "link": "https://api.stubhub.net/catalog/categories/33322/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Suffs", "link": "https://api.stubhub.net/catalog/categories/429656/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
    {"name": "Hadestown", "link": "https://api.stubhub.net/catalog/categories/101920/events?exclude_parking_passes=true&latitude=40.7610848&longitude=-73.9857178&max_distance_in_meters=1000"},
]

def get_stubhub_token(client_id, client_secret):
    url = 'https://account.stubhub.com/oauth2/token'
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials', "scope": "read:events"}
    
    response = requests.post(url, headers=headers, data=data, auth=auth)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to obtain token: {response.status_code}, {response.text}')
    
def get_broadway_tickets(token, endpoint):
    url = endpoint
    headers = {'Authorization': f'Bearer {token}'}
    # params = {'categoryId': '150028781', 'city': 'New York'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception('Failed to fetch tickets')

def find_cheapest_ticket(events):
    cheapest_ticket = None
    if not events["_embedded"]["items"]: 
        return None
    
    for event in events["_embedded"]["items"]:
        if event["min_ticket_price"] is None:
            continue
        else:
            min_ticket_price = event["min_ticket_price"]["amount"]
            if min_ticket_price is not None:
                if cheapest_ticket is None or min_ticket_price < cheapest_ticket["min_ticket_price"]["amount"]:
                    cheapest_ticket = event
    
    return cheapest_ticket if cheapest_ticket else "No tickets found"

