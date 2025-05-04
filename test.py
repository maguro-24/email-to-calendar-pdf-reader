from gmail_api import init_gmail_service, get_email_messages, get_email_message_details, download_attachments
from PyPDF2 import PdfReader
import os
import datetime as dt
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from calender_api import init_calendar_service, add_event
from datetime import datetime



client_file = 'client_secret_new.json'
service = init_gmail_service(client_file)

messages = get_email_messages(service, max_results=100)

for msg in messages:
    detail = get_email_message_details(service, msg['id'])

    if '### @employer email ### ' in detail['sender']:
        download_attachments(service,'me',msg['id'],'### project location ###')
        break
        



path = '### project location ###'
dir_list = os.listdir(path)
print("Files and directories in '", path, "' :")
# prints all files
print(dir_list)

text = []

with open(f'downloads/{dir_list[0]}', 'rb') as f:
    pdf_reader = PdfReader(f)
    num_page = len(pdf_reader.pages)

    for page_num in range(num_page):
        page = pdf_reader.pages[page_num]

        page_text = page.extract_text()

        text.extend(page_text.split('\n'))

for i in range(len(text)):
    text[i] = [text[i]]

print(text)

for i in range(len(text)):
    text[i] = text[i][0].split(' ')
    if '### NAME ###' in text[i][0]:
        my_days = text[i][:-1]
        time_data = my_days
        combined_time_data = []
        j = 0
        while j < len(time_data):
            if time_data[j] == 'RO' or time_data[j] == 'OFF':
                combined_time_data.append(time_data[j])  # Keep 'RO' or 'OFF'
                combined_time_data.append('-')  # Insert '-' after 'RO' or 'OFF'
            elif time_data[j] == '0.0':
                # Check if the last index isn't '-'
                if len(combined_time_data) == 0 or combined_time_data[-1] != '-':
                    combined_time_data.append('-')  # Add '-'
                    combined_time_data.append('-')  # Add another '-'
                combined_time_data.append(time_data[j])  # Add '0.0'
            elif time_data[j] in ['AM', 'PM'] and len(combined_time_data) > 0:
                # Combine with the previous time
                combined_time_data[-1] = f"{combined_time_data[-1]} {time_data[j]}"
            else:
                combined_time_data.append(time_data[j])  # Add other elements as is
            j += 1

    
    if 'MONDAY' in text[i] and '2025' in text[i][0].split('/'):
        print('big dingus')
        dates_raw = text[i]
    
    elif 'MONDAY' not in text[i] and '2025' in text[i][0].split('/'):
        print('little dingus')
        dates_raw = text[i]
    
    print(text[i])



print(dates_raw)
dates = []
if dates_raw:
    for date in dates_raw:
        # Extract the date part (digits and '/')
        date_part = ''.join([char for char in date if char.isdigit() or char == '/'])
        if date_part:  # Skip empty or invalid strings
            try:
                month, day, year = date_part.split('/')
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"  # Add leading zeros
                dates.append(formatted_date)
            except ValueError:
                print(f"Invalid date format: {date_part}")
else:
    print("Error: dates_raw is empty or invalid.")

for i in range(len(combined_time_data)-1, -1, -1):
    if 'PM' in combined_time_data[i]:
        time = combined_time_data[i].replace('PM', '').strip()  # Remove 'PM' and strip whitespace
        time = time.split(':')  # Split into hours and minutes
        hour = int(time[0]) + 12  # Convert hour to 24-hour format
        minute = int(time[1])  # Keep the minutes as is
        combined_time_data[i] = f"{hour}:{minute:02d}"  # Update the list with the converted time
    if i%3 == 0:
        combined_time_data.pop(i)  # Remove the time data
time_groups = []
for i in range(0, len(combined_time_data), 2):
    if i + 1 < len(combined_time_data):  # Ensure there is a pair
        time_groups.append([combined_time_data[i], combined_time_data[i + 1]])
    else:
        time_groups.append([combined_time_data[i]])  # Handle the last single element if odd

print(time_groups)
print(dates)


calendar_service = init_calendar_service(client_file)

for i in range(len(time_groups)):
    if time_groups[i][0] in ['RO', 'OFF', '-']:
        print(f"Skipping invalid time group: {time_groups[i]}")
        continue
    if len(time_groups[i]) < 2:
        print(f"Skipping incomplete time group: {time_groups[i]}")
        continue
    if len(dates) <= i:
        print(f"Skipping time group due to missing date: {time_groups[i]}")
        continue

    start_time = f"{dates[i]}T{time_groups[i][0]}:00"
    end_time = f"{dates[i]}T{time_groups[i][1]}:00"

    if start_time >= end_time:
        print(f"Skipping invalid time range: start_time={start_time}, end_time={end_time}")
        continue

    event = {
        'summary': 'Work',
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Chicago',  # Adjust to your timezone
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/Chicago',  # Adjust to your timezone
        },
    }

    try:
        print(f"Creating event: {event}")
        event_result = calendar_service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event_result.get('htmlLink')}")
    except HttpError as error:
        print(f"An error occurred: {error}")

file_path = f'downloads/{dir_list[0]}'

if os.path.exists(file_path):
    os.remove(file_path)
    print(f"File '{file_path}' deleted successfully.")
else:
    print(f"File '{file_path}' does not exist.")
