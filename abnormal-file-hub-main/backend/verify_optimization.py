import urllib.request
import urllib.parse
import json
import hashlib
import uuid
import sys
import time

BASE_URL = "http://localhost:8000/api"

def calculate_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def check_existence(file_hash, filename, file_type, size):
    url = f"{BASE_URL}/files/dedup-check/"
    data = {
        "file_hash": file_hash,
        "filename": filename,
        "file_type": file_type,
        "size": size
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Check existence failed: {e.code} {e.reason}")
        print(e.read().decode())
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
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Upload failed: {e.code}")
        return None

def main():
    print("--- Testing Client-Side Deduplication ---")
    
    content = "Client-side dedup test content " + uuid.uuid4().hex
    filename = "client_dedup.txt"
    file_hash = calculate_hash(content)
    
    # 1. Check existence (Should be False)
    print("1. Checking existence (Expect False)...")
    res = check_existence(file_hash, filename, "text/plain", len(content))
    if res and res['exists'] == False:
        print("SUCCESS: File does not exist.")
    else:
        print(f"FAILURE: Unexpected result: {res}")
        sys.exit(1)

    # 2. Upload file normally
    print("2. Uploading file...")
    upload_res = upload_file(filename, content)
    if upload_res:
        print(f"SUCCESS: Uploaded {upload_res['id']}")
    else:
        sys.exit(1)

    # 3. Check existence again (Should be True)
    print("3. Checking existence again (Expect True)...")
    res = check_existence(file_hash, "client_dedup_copy.txt", "text/plain", len(content))
    if res and res['exists'] == True:
        print(f"SUCCESS: File exists. Linked to {res['file']['id']}")
        if res['file']['original_filename'] == "client_dedup_copy.txt":
             print("SUCCESS: Filename updated in link.")
    else:
        print(f"FAILURE: Unexpected result: {res}")
        sys.exit(1)

if __name__ == "__main__":
    main()
