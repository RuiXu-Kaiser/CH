import json
import requests

# 1. Define configuration variables
BAM_IP = "192.168.1.50"  # Replace with your Address Manager IP
AUTH_TOKEN = "BAMAuthToken: UTtSjMTQ1ODAzMTgzMDUxMzphcGk="  # Replace with your session token

# 2. Define selection criteria payload (e.g., fetch all IPv4 Networks and Blocks)
criteria = {
    "selector": "search",
    "types": "IP4Block,IP4Network",
    "keyword": "*",
}

# 3. Setup endpoint and parameters
# The JSON object MUST be passed as a string string inside 'selectCriteria'
url = f"https://{BAM_IP}/Services/REST/v1/exportEntities"
params = {"selectCriteria": json.dumps(criteria)}

headers = {
    "Authorization": AUTH_TOKEN,
    "Accept": "application/octet-stream",  # API returns data as an octet stream
}

# 4. Execute stream call to handle large datasets efficiently
try:
    response = requests.get(url, headers=headers, params=params, stream=True, verify=False)
    response.raise_for_status()

    # Save output directly to a file chunk by chunk
    output_filename = "exported_entities.json"
    with open(output_filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    print(f"Success! Data exported successfully to {output_filename}")

except requests.exceptions.RequestException as e:
    print(f"API Error occurred: {e}")