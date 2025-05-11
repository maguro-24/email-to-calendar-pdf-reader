from gmail_api import init_gmail_service, get_email_messages, get_email_message_details, download_attachments
from PyPDF2 import PdfReader
import os
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
from calender_api import init_calendar_service



client_file = 'client_secret_new.json'
service = init_gmail_service(client_file)

messages = get_email_messages(service, max_results=100)

for msg in messages:
    detail = get_email_message_details(service, msg['id'])

    if '' in detail['sender']: ### Employer email handle ### 
        download_attachments(service,'me',msg['id'],'/path/to/Projects/work_schedule/downloads') ### IMPORTANT ###
        break
        



path = '/path/to/Projects/work_schedule/downloads'
dir_list = os.listdir(path)
print("Files and directories in '", path, "' :")
# prints all files

print(dir_list)
text = []
pdf = None
for item in dir_list:
    if item.endswith('.pdf'):
        pdf = item

with open(f'downloads/{pdf}', 'rb') as f:
    pdf_reader = PdfReader(f)
    num_page = len(pdf_reader.pages)

    for page_num in range(num_page):
        page = pdf_reader.pages[page_num]

        page_text = page.extract_text()

        text.extend(page_text.split('\n'))

for i in range(len(text)):
    text[i] = [text[i]]



for i in range(len(text)):
    text[i] = text[i][0].split(' ')
    if '' in text[i][0]:  ### NAME ###
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

    elif 'AM' in combined_time_data[i]:
        time = combined_time_data[i].replace('AM', '').strip() 
        time=time.split(':')
        hour = int(time[0])
        minute = int(time[1])  # Keep the minutes as is
        combined_time_data[i] = f"{hour}:{minute:02d}"

    if i%3 == 0:
        combined_time_data.pop(i)  # Remove the time data
time_groups = []
for i in range(0, len(combined_time_data), 2):
    if i + 1 < len(combined_time_data):  # Ensure there is a pair
        time_groups.append([combined_time_data[i], combined_time_data[i + 1]])
    else:
        time_groups.append([combined_time_data[i]])  # Handle the last single element if odd

print(time_groups)


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

    start_time = datetime.fromisoformat(f"{dates[i]}T{time_groups[i][0]}:00").replace(tzinfo=timezone.utc).isoformat()
    end_time = datetime.fromisoformat(f"{dates[i]}T{time_groups[i][1]}:00").replace(tzinfo=timezone.utc).isoformat()

    if start_time >= end_time:
        print(f"Skipping invalid time range: start_time={start_time}, end_time={end_time}")
        continue

    # Check for duplicate event directly with an if statement
    try:
        events_result = calendar_service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime',
            q='Work'
        ).execute()

        duplicate_found = False
        for existing_event in events_result.get('items', []):
            if existing_event.get('summary', '').strip().lower() == 'work':
                print(f"Skipping duplicate event: {start_time} to {end_time}")
                duplicate_found = True
                break

        if duplicate_found:
            continue

    except HttpError as error:
        print(f"An error occurred while checking for duplicates: {error}")
        continue

    event = {
        'summary': 'Work',
        'start': {
            'dateTime': start_time,

        },
        'end': {
            'dateTime': end_time,

        },
    }

    try:
        print(f"Creating event: {event}")
        event_result = calendar_service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event_result.get('htmlLink')}")
    except HttpError as error:
        print(f"An error occurred: {error}")

file_path = f'downloads/{pdf}'

if os.path.exists(file_path):
    os.remove(file_path)
    print(f"File '{file_path}' deleted successfully.")
else:
    print(f"File '{file_path}' does not exist.")