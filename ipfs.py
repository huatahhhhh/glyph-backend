import os
import json
import requests

projectId = os.environ.get("IPFS_PROJECT_ID")
projectSecret = os.environ.get("IPFS_PROJECT_SECRET")
endpoint = os.environ.get("IPFS_NODE_URL")

def write_to_ipfs(data):
    data = json.dumps(data, indent=2).encode('utf-8')
    files = {'file.json': data}
    response1 = requests.post(endpoint + '/api/v0/add', files=files, auth=(projectId, projectSecret))
    hash = response1.text.split(",")[1].split(":")[1].replace('"','')
    print(hash)
    return hash

# ### READ FILE WITH HASH ###
# params = {
    # 'arg': hash
# }
# response2 = requests.post(endpoint + '/api/v0/cat', params=params, auth=(projectId, projectSecret))
# print(response2)
# print(response2.text)

if __name__ == "__main__":
    hash = write_to_ipfs(dict(a=1, b=2))
    print(hash)

    # verify with https://ipfs.io/ipfs/ or other public gateways (some are more connected to ipfs then others)
