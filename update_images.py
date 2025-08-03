from models import Event, db
import requests
from app import app

def update_event_images():
    with app.app_context():
        # Get all events with todaytix_category_id
        events = Event.query.filter(
            Event.todaytix_category_id.isnot(None),
            Event.image.is_(None)
        ).all()
        
        for event in events:
            if event.todaytix_category_id:
                url = f"https://content-service.tixuk.io/api/v3/products/{event.todaytix_category_id}"
                headers = {"accept": "application/json"}
                
                try:
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        image_url = data["data"]["heroImage"]["file"]["url"]
                        
                        # Update event image
                        event.image = image_url
                        print(f"Updated image for {event.name}: {image_url}")
                    else:
                        print(f"Failed to fetch image for {event.name}: {response.status_code}")
                except Exception as e:
                    print(f"Error updating image for {event.name}: {str(e)}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("Successfully committed all image updates")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes: {str(e)}")

if __name__ == "__main__":
    update_event_images() 