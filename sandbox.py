from models import Event, Venue, Region, db
import requests
from app import app
from stubhub import get_stubhub_token, get_broadway_tickets, find_cheapest_ticket, partnerize_tracking_link
from datetime import datetime, timedelta

def prices_by_region(region):
    with app.app_context():
        # Get all events with todaytix_category_id
        venues = Venue.query.filter(
            Venue.region.has(Region.name == region),
        ).all()
        
        for venue in venues:
            token = get_stubhub_token("4XWc10UmncVBoHo3lT8b", "sfwKjMe6h1cApxw1Ca7ZKTsaoa2gSRov5ECYkM2pVXEvAUW0Ux0KViQZwWfI")
            if not venues:
                return {"error": f"Couldn't fetch venues"}, 404

            res = []
            # current_time = datetime.now() - timedelta(hours=5)
            endpoint = "https://api.stubhub.net/catalog/events/search?exclude_parking_passes=true&q=" + venue.name
            events_data = get_broadway_tickets(token, endpoint)
            
            if not events_data["_embedded"]["items"]:
                continue
            else:
                cheapest_ticket = find_cheapest_ticket(events_data)
                
                if cheapest_ticket is not None:
                    start_date_var = cheapest_ticket["start_date"]
                    non_formatted_datetime = datetime.strptime(start_date_var, "%Y-%m-%dT%H:%M:%S%z")
                    formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
                    complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()
                    
                    # Calculate current price
                    current_price = round(cheapest_ticket["min_ticket_price"]["amount"])
                    
                    cheapest_event_info = {
                        # "event_info": [
                        #     {
                        #         "name": cheapest_ticket["name"],
                        #         "price": current_price,
                        #         "formatted_date": complete_formatted_date,
                        #         "link": partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                        #         "event_date": non_formatted_datetime.strftime("%Y-%m-%d")
                        #     }
                        # ],
                        # "id": event.id,
                        "name": cheapest_ticket["name"],
                        "price": current_price,
                        # "category_id": event.category_id,
                        # "image": event.image,
                        "venue": venue.name,
                        # "link": partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                        # "venue": venue.to_dict() if venue else None
                        }            
                    print(cheapest_event_info)
                    res.append(cheapest_event_info)
        return res
        
        # Commit all changes
        try:
            db.session.commit()
            print("Successfully committed all image updates")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes: {str(e)}")

if __name__ == "__main__":
    prices_by_region("Los Angeles")