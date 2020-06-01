import json
import requests

people_api_url = 'http://130.60.24.72/api/get_persons'
r = requests.get(people_api_url)
people = r.json()
data_for_events = list()
url_list = list()
for person in people:
    last_name = person[0].replace(' ', '%20')
    name = person[1].replace(' ', '%20')
    if name == 's.n.' or last_name == 's.n.':
        continue
    location = 'None'
    url = f'http://130.60.24.72/api/get_correspondence/{last_name}/{name}/{location}'
    last_name = person[0].replace(' ', '_')
    name = person[1].replace(' ', '_')
    url_name = f'{last_name}/{name}'
    full_name = f'{person[1]} {person[0]}'
    file_name = f'{person[0].replace(" ", "_")}_{person[1].replace(" ", "_")}'
    if url not in url_list:
        url_list.append(url)
        data_for_events.append([url, full_name, file_name, url_name])
print(data_for_events)

for data_event in data_for_events:
    r = requests.get(data_event[0])
    data = r.json()

    events = dict()

    events['events'] = list()
    for key, value in data.items():

        event = dict()
        if value.get("year")[0] is None or value.get("year")[0] == 0:
            continue

        location = value.get("location")[0]
        if location == 's.n.' or location == 's.l.':
            location = 'Unknown'

        year = str(value.get("year")[0])
        month = str(value.get("month")[0])
        day = str(value.get("day")[0])

        if value.get("day")[0] is None or value.get("day")[0] == 0:
            if value.get("month")[0] is None or value.get("month")[0] == 0:
                day = '1'
                month = '8'
            else:
                day = '15'

        event["start_date"] = dict()
        event["media"] = dict()
        event["start_date"]["year"] = year
        event["start_date"]["month"] = month
        event["start_date"]["day"] = day

        if value.get("is_sender"):
            event["media"]["thumbnail"] = "../../static/green.jpg"
        elif not value.get("is_sender"):
            event["media"]["thumbnail"] = "../../static/red.jpg"
        else:
            print(value.get("is_sender"))
        txt = dict()
        txt["headline"] = f'{day}.{month}.{year}, location: {location}'
        txt["text"] = f'Briefwechsel zwischen Heinrich Bullinger und {data_event[1]}'
        event["text"] = txt
        events['events'].append(event)
    with open(f'static/data/{data_event[2]}.json', 'w+') as json_events:
        print(data_event[2], data_event[0])
        json.dump(events, json_events)
    with open('urls.txt', 'a+') as urls_file:
        urls_file.write(f'http://0.0.0.0:5000/{data_event[3]}\n')




