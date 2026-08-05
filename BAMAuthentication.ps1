# 1. Safely prompt the user for credentials
$username = "xur01"
$password = "(wrt/E_1WO9h5f"

# 2. Define the login endpoint and payload
$Uri = "https://bam.conehealth.com/api/v2/sessions"
$body = @{
    username = $username
    password = $password
} | ConvertTo-Json

# 3. Send the login request
try {
    $loginResponse = Invoke-RestMethod -Uri $loginUri -Method Post -Body $body -ContentType "application/json"
    
    # 4. Extract the token (adjust '.token' to match your API's exact JSON key)
    $bearerToken = $loginResponse.apiToken
	
    Write-Host "Login successful! Token acquired." -ForegroundColor Green
	Write-Host $bearerToken

    # 5. Create authenticated headers for future API requests
    $authHeaders = @{
        "Authorization" = "Bearer $bearerToken"
        "Accept"        = "application/json"
    }

    # Example of a subsequent authenticated request
    # $data = Invoke-RestMethod -Uri "https://example.com" -Method Get -Headers $authHeaders
}
catch {
    Write-Error "Login failed: $_"
}