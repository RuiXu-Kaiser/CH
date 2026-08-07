import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Configuration variables
BAM_IP = "bam.conehealth.com"  # Replace with your Address Manager IP or hostname
USERNAME = "xur01"
PASSWORD = "(wrt/E_1WO9h5f"

# Construct the base session URL
session_url = f"https://{BAM_IP}/api/v2/sessions"

# 2. Authenticate to establish a session and get the API token
payload = {
    "username": USERNAME,
    "password": PASSWORD
}

# Note: verify=False bypasses SSL verification for self-signed certificates.
# Remove verify=False or point it to your CA bundle in production environments.
response = requests.post(session_url, json=payload, verify=False)
print (response.status_code)
if response.status_code == 201:
    session_data = response.json()

    # BlueCat REST v2 returns a pre-computed Base64 string for Basic auth
    b64_credentials = session_data["basicAuthenticationCredentials"]
    print("Successfully logged in.")

    # 3. Use the credentials string to authorize subsequent API requests
    api_headers = {
        "Authorization": f"Basic {b64_credentials}",
        "Content-Type": "application/json"
    }

    # Example subsequent call: GET configurations
    config_url = f"https://{BAM_IP}/api/v2/configurations"
    config_response = requests.get(config_url, headers=api_headers, verify=False)

    if config_response.status_code == 200:
        print("Configurations fetched successfully:", config_response.json())
    else:
        print(f"Failed to fetch data: {config_response.status_code}", config_response.text)

    export_url = f"https://{BAM_IP}/api/v1/exportEntities"
    query_params_tree = {
        "selector": "get_entitytree",
        "startEntityId": 1,  # Base ID (1 exports the global configuration tree)
        "types": "IPv4Address",  # Multiple types can be comma-separated
        "children_only": "false",
        "forImport": "true"
    }
    print("Initiating bulk IP4Address export routine...")
    export_response = requests.get(export_url, headers=api_headers, params=query_params_tree, verify=False)

    # Parse the resulting JSON stream containing your structural IP elements
    exported_addresses = export_response.json()
    print(f"Data stream retrieved successfully. Total entries: {len(exported_addresses)}")

    # Output the extracted bulk data
    exported_data = export_response.json()
    print(exported_data)

else:
    print(f"Login failed with status code {response.status_code}: {response.text}")
