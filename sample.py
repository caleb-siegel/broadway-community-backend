# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

tollfree_verification = client.messaging.v1.tollfree_verifications.create(
    business_name="Broadway Community",
    business_street_address="600 W 239th St",
    business_street_address2="Apt 3B",
    business_city="Bronx",
    business_state_province_region="AA",
    business_postal_code="10463",
    business_country="US",
    business_website="https://broadwaycommunity.vercel.app",
    business_contact_first_name="Caleb",
    business_contact_last_name="Siegel",
    business_contact_email="broadway.comms@gmail.com",
    business_contact_phone="+15514867067",
    notification_email="broadway.comms@gmail.com",
    use_case_categories=["TWO_FACTOR_AUTHENTICATION", "MARKETING"],
    use_case_summary="This number is used to send out price alerts for broadway show tickets to people who sign up for the alerts.",
    production_message_sample="Hamilton: $56; Monday, January 13, 2024",
    opt_in_image_urls=[
        "https://zipwhiptestbusiness.com/images/image1.jpg",
        "https://zipwhiptestbusiness.com/images/image2.jpg",
    ],
    opt_in_type="VERBAL",
    message_volume="10",
    additional_information="",
    tollfree_phone_number_sid="+18557291366",
    external_reference_id="",
)

print(tollfree_verification.sid)