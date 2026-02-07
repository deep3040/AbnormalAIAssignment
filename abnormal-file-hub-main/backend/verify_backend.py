import urllib.request
import urllib.parse
import json
import uuid
import mimetypes
import sys
import time

BASE_URL = "http://localhost:8000/api"

def get_stats():
    req = urllib.request.Request(f"{BASE_URL}/files/stats/")
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            return json.loads(response.read().decode())
        else:
            print(f"Failed to get stats: {response.status}")
            return None

def upload_file(filename, content):
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    
    data = []
    data.append(f'--{boundary}')
    data.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    data.append('Content-Type: text/plain')
    data.append('')
    data.append(content)
    data.append(f'--{boundary}--')
    data.append('')
    
    body = '\r\n'.join(data).encode('utf-8')
    
    req = urllib.request.Request(f"{BASE_URL}/files/", data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Content-Length', len(body))
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Upload failed: {e.code} {e.reason}")
        print(e.read().decode())
        return None

def main():
    print("Waiting for server to start...")
    time.sleep(5)
    
    print("\n--- Testing Upload ---")
    content1 = "This is a test file for deduplication."
    file1 = upload_file("test1.txt", content1)
    if file1:
        print(f"Uploaded file 1: {file1['id']} - Hash: {file1.get('file_hash')}")
    else:
        sys.exit(1)

    print("\n--- Testing Deduplication (Same Content) ---")
    file2 = upload_file("test2.txt", content1)
    if file2:
        print(f"Uploaded file 2: {file2['id']} - Hash: {file2.get('file_hash')}")
        if file1['file_hash'] == file2['file_hash']:
            print("SUCCESS: Hashes match.")
        else:
            print("FAILURE: Hashes do not match.")
    
    print("\n--- Testing Stats ---")
    stats = get_stats()
    if stats:
        print(json.dumps(stats, indent=2))
        if stats['saved_size'] > 0:
            print("SUCCESS: Saved size is greater than 0.")
        else:
            print("FAILURE: Saved size is 0.")

    print("\n--- Testing Search ---")
    # Search for 'test1'
    search_url = f"{BASE_URL}/files/?search=test1"
    req = urllib.request.Request(search_url)
    with urllib.request.urlopen(req) as response:
         results = json.loads(response.read().decode())
         print(f"Search 'test1' results: {len(results)}")
         if len(results) >= 1 and any('test1' in f['original_filename'] for f in results):
             print("SUCCESS: Search found test1.")

if __name__ == "__main__":
    main()
