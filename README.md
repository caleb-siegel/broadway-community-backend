## How to add a new show
- go to stubhub
- find a specific show
- look for the event URL and at the end there should be an event ID
- Go to postman and, using the proper credentials, replace the number at the end of the below url with the event ID (https://api.stubhub.net/catalog/events/153152376/)
- find the categories key in the returned value and get the id's value
- Paste the ID in the show_api_endpoints array as a new object with a name key and a link key. the link will be this copied id.

## Acitvate the backend
- run pipenv shell to activate the local environment
- run python app.py to run the app.py file

## to run a migration
- run flask db migrate
- run flask db upgrade

## to add images
- run pipenv shell to activate the local environment
- run python update_images.py