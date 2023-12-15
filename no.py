import re
import requests
from pymongo import MongoClient

# MongoDB connection details
mongo_host = '0.tcp.in.ngrok.io'
mongo_port = 13881
mongo_db_name = 'porn'
mongo_collection_name = 'links'

# MongoDB connection
client = MongoClient(mongo_host, mongo_port)
db = client[mongo_db_name]
collection = db[mongo_collection_name]
print("Connected to MongoDB successfully!")

PREFIX = 'https:/'

def extract_streamtape_link(url):
    try:
        # Make a GET request
        response = requests.get(url)
        print(response.status_code, 1)

        # Extract links using regular expression
        streamtape_links = re.findall(r'https://streamtape\.(?:com|net|to)/v/[^/]+/[^/]+\.mp4', response.text)
        print(url)
        if not streamtape_links:
            return 0

        # Standardize the domain to streamtape.to
        standardized_links = [re.sub(r'https://streamtape\.(com|net)/', r'https://streamtape.to/', link) for link in streamtape_links]

        # Return the first standardized link if found, otherwise return None
        return standardized_links[0]
    
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        return None

# Example usage
url = "https://example.com"
streamtape_link = extract_streamtape_link(url)

if streamtape_link:
    print(f"Streamtape link found: {streamtape_link}")
else:
    print("No Streamtape link found.")

    



def get_curl_command(url: str) -> str:
    html1 = requests.get(url)
    print(html1.status_code,2)
    if int(html1.status_code) != 200:
            return 0
    html=html1.content.decode()
    token = re.match(r".*document.getElementById.*\('norobotlink'\).innerHTML =.*?token=(.*?)'.*?;", html, re.M|re.S).group(1)
    infix = re.match(r'.*<div id="ideoooolink" style="display:none;">(.*?token=).*?<[/]div>', html, re.M|re.S).group(1)
    final_URL = f'{PREFIX}{infix}{token}'
    orig_title = re.match(r'.*<meta name="og:title" content="(.*?)">', html, re.M|re.S).group(1)
    print(f"{final_URL}")
    return f"{final_URL}"

def upload_file_to_api(video_url):
    # Fetching the raw video data
    video_response = requests.get(video_url)
    print(video_response.status_code,3)
    # Content-Type will be determined based on the file extension
    files = {'file': ('video.mp4', video_response.content)}
    
    api_url = "https://api.penpencil.co/v1/files"
    headers = {
        # Include your headers here
    }

    # Uploading the video
    response = requests.post(api_url, headers=headers, files=files)
    print(response.json())
    if response.status_code == 200:
        return response.json()['data']['baseUrl'] + response.json()['data']['key']
        print("done2")
    else:
        return None

# Iterate through each document in the collection
i=1
for document in collection.find({"vlink": {"$exists": False}}):
    if i<41:
            print("skip",i)
            i+=1
            continue
    link = document.get('link')
    _id = document.get('_id')

    link1=extract_streamtape_link(link)
    if link1==0:
            print("skip")
            continue
    streamtape_url = get_curl_command(link1)
    if streamtape_url==0:
            print("skip")
            continue
    uploaded_video_url = upload_file_to_api(streamtape_url)

        # Update the document with the new 'vlink' field
    if uploaded_video_url:
          collection.update_one({'_id': document['_id']}, {'$set': {'vlink': uploaded_video_url}})
          print(f"Document {_id} updated successfully.")
    else:
          print(f"Failed to upload video for document {_id}.")
    
client.close()
