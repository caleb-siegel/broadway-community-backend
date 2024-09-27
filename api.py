import requests
import time

partnerize_tracking_link = "https://stubhub.prf.hn/click/camref:1100lTenp/destination:"

token_cache = {
    "token": None,
    "expires_at": None
}

show_api_endpoints = {
    "broadway": [
        {"name": "Hamilton", "category_id": "35042", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Six", "category_id": "82392", "latitude": "40.7599414", "longitude": "-73.98690909999999"},
        {"name": "& Juliet", "category_id": "127739", "latitude": "40.75594711303711", "longitude": "-73.98497772216797"},
        {"name": "MJ", "category_id": "177138", "latitude": "40.7631716", "longitude": "-73.9845438"},
        {"name": "The Outsiders", "category_id": "102774", "latitude": "40.75878524780273", "longitude": "-73.98772430419922"},
        {"name": "The Book of Mormon", "category_id": "150057581", "latitude": "40.7610848", "longitude": "-73.9857178"},
        {"name": "Wicked", "category_id": "3682", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "The Lion King", "category_id": "1534", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Hell's Kitchen", "category_id": "150087389", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Moulin Rouge", "category_id": "11874", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "The Notebook", "category_id": "430684", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Harry Potter and the Cursed Child", "category_id": "36402", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Back to the Future", "category_id": "146928", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "The Great Gatsby", "category_id": "42838", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Oh, Mary", "category_id": "150204986", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Aladdin", "category_id": "12721", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Chicago", "category_id": "14222", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Cabaret", "category_id": "4987", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Water for Elephants", "category_id": "150043364", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Elf", "category_id": "33322", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Suffs", "category_id": "429656", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
        {"name": "Hadestown", "category_id": "101920", "latitude": "40.759033203125", "longitude": "-73.98674774169922"},
    ],
    "taylor swift": [
        {"name": "Taylor Swift", "category_id": "11113", "latitude": "", "longitude": ""},
    ],
    "yankees playoffs": [
        {"name": "All Yankees", "category_id": "6017", "latitude": "", "longitude": ""},
        {"name": "Yankees at Home", "category_id": "6017", "latitude": "40.8352765", "longitude": "-73.921855"},
        {"name": "Yankees Spring Training", "category_id": "150366110", "latitude": "27.9792251", "longitude": "-82.5078734", "max_distance": 40000},
        {"name": "AL Wild Card", "category_id": "150366110", "latitude": "", "longitude": ""},
        {"name": "ALDS", "category_id": "263022", "latitude": "", "longitude": ""},
        {"name": "ALCS", "category_id": "262850", "latitude": "", "longitude": ""},
        {"name": "World Series", "category_id": "6601", "latitude": "", "longitude": ""},
        {"name": "Yankees Wild Card", "category_id": "150366110", "latitude": "40.8352765", "longitude": "-73.921855"},
        {"name": "Yankees ALDS", "category_id": "263022", "latitude": "40.8352765", "longitude": "-73.921855"},
        {"name": "Yankees ALCS", "category_id": "262850", "latitude": "40.8352765", "longitude": "-73.921855"},
        {"name": "Yankees World Series", "category_id": "6601", "latitude": "40.8352765", "longitude": "-73.921855"},
    ],
    "world cup 2026": [
        {"name": "All World Cup", "category_id": "278322", "latitude": "", "longitude": ""},
        {"name": "World Cup Metlife", "category_id": "278322", "latitude": "40.8241653442383", "longitude": "-74.0868377685547"},
    ],
}


def get_link(category_id, latitude=None, longitude=None, max_distance=1000):
    # add starting point
    link = "https://api.stubhub.net/catalog/categories/"
    
    # add categoryId
    link = link + category_id + "/events"
    
    # add parking pass filter
    link = link + "?exclude_parking_passes=true"
    
    # add lat/long/distance
    if latitude and longitude:
        link = link + f"&latitude={latitude}&longitude={longitude}&max_distance_in_meters={max_distance}"

    return link

def get_stubhub_token(client_id, client_secret):
    if token_cache['token'] and token_cache['expires_at'] > time.time():
        print("The token has been cached and used without calling a new token")
        return token_cache['token']
    
    print("The old token has expired, so we are generating a new token now.")
    url = 'https://account.stubhub.com/oauth2/token'
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials', "scope": "read:events"}
    
    response = requests.post(url, headers=headers, data=data, auth=auth)
    
    if response.status_code == 200:
        token_data = response.json()
        token_cache['token'] = token_data['access_token']
        token_cache['expires_at'] = time.time() + token_data['expires_in']
        return token_cache['token']
    else:
        raise Exception(f'Failed to obtain token: {response.status_code}, {response.text}')
    
def get_broadway_tickets(token, endpoint):
    url = endpoint
    headers = {'Authorization': f'Bearer {token}'}
    
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

