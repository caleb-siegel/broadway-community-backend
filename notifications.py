def alert_notification_new(old_price, current_price, name, alerts, event_info):
    for alert in alerts:
        # check if alert conditions are met
        send_notification = check_alert_conditions(alert, current_price, event_info)

        if send_notification:
            discount = round(((current_price / event_info.average_lowest_price) - 1) * 100)

            if alert.notification_method == 'email':
                print(f"Sending email")
                # send_email(alert, name, current_price, old_price, discount, event_info)

            elif alert.notification_method == 'sms':
                print(f"Sending SMS")
            #     print(f"Sending SMS for {name} to {alert.user.phone_number}")
            #     # send sms
            #     account_sid = twilio_account_sid
            #     auth_token = twilio_auth_token
            #     client = Client(account_sid, auth_token)

            #     message = client.messages.create(
            #         from_='+18557291366',
            #         to = f'+1{alert.user.phone_number}',
            #         body=(
            #             f"{name}: {current_price}\n"
            #             f"{event_info.formatted_date}\n"
            #             f"Buy the tickets here: {event_info.link}"
            #         ),
            #     )
            #     print(f"Message sent with SID: {message.sid}")
                
            # if user is xxx, send whatsapp message to caleb through callmebot
            # if alert.user.id == 31: #broadway comms user
            #     discount_message = "" if discount >= 0 else f"({abs(discount)}% discount)"
            #     whatsapp_msg = (
            #         f"🎭 {name}\n"
            #         f"${current_price}\n"
            #         f"Generally sells as low as ${round(event_info.average_lowest_price)} {discount_message}\n"
            #         f"{event_info.formatted_date}\n"
            #         f"{event_info.link}"
            #     )
            #     send_whatsapp_message(
            #         phone_number="+15514867067",  # your number
            #         api_key=os.getenv('CALL_ME_BOT_API_KEY'),
            #         message=whatsapp_msg
            #     )
            

def send_whatsapp_message(phone_number, api_key, message):
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={requests.utils.quote(message)}&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ WhatsApp message sent!")
        else:
            print(f"❌ Failed to send message. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print("❌ Error sending message:", e)

def check_alert_conditions(alert, current_price, event_info):
    if alert.price_number and (current_price > alert.price_number):
        print("Price not low enough")
        return False
    discount = round(((current_price / event_info.average_lowest_price) - 1) * 100)
    if alert.price_percent and (discount > (alert.price_percent * -1)):
        print("Discount not enough")
        return False
    if alert.start_date and (event_info.event_date < alert.start_date):
        print("Event date is before alert start date")
        return False
    if alert.end_date and (event_info.event_date > alert.end_date):
        print("Event date is after alert end date")
        return False
    if alert.show_time == 'Matinee' and not (event_info.event_time >= '12:00:00' and event_info.event_time < '16:00:00'):
        print("Event time is not during Matinee")
        return False
    if alert.show_time == 'Evening' and not (event_info.event_time >= '16:00:00'):
        print("Event time is not during Evening")
        return False
    if alert.weekday and event_info.event_weekday is not None and event_info.event_weekday not in alert.weekday:
        print("Event weekday is not in alert weekday list")
        return False
    return True

def send_email(alert, name, current_price, old_price, discount, event_info):
    message = Mail(
        from_email='broadway.comms@gmail.com',
        to_emails=alert.user.email,
        subject=f'Price Alert: {name} ${current_price}',
        html_content=f"""
    <strong>{name}</strong> is selling at <strong>~${current_price}</strong>. It was previously selling for ${old_price}.<br><br>

    This is {abs(discount)}% {'cheaper' if discount < 0 else 'higher'} than what you can normally get this show for at Stubhub.<br><br>
    This show is on {event_info['formatted_date']}.<br><br>

    <a href="{event_info['link']}">Buy the tickets here</a><br><br>

    """
    )
    try:
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        print(f'response: {response.status_code}')
    except Exception as e:
        print(e)

testData = {
    "old_price": 100,
    "current_price": 60,
    "name": "Hamilton",
    "alerts": [
        {
            "price_number": None,
            "price_percent": 30,
            "start_date": "2025-08-01",
            "end_date": '2025-08-15',
            "show_time": "Evening",
            'weekday': [1,2,3],
            "notification_method": "sms",
            "user": {
                "id": 31,
                "email": "broadway.comms@gmail.com"
            }
        }
    ],
    "event_info": {
        "average_lowest_price": 100,
        "event_date": "2025-08-13",
        "event_time": "19:30:00",
        "event_weekday": 2,  # Tuesday (0-indexed)
        "formatted_date": "October 1, 2023",
        "link": "https://stubhub.com/hamilton-tickets"
    }
}

# alert_notification_new(testData)