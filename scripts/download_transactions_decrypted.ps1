try {
    Import-Module Set-PsEnv
    
    Set-PsEnv
    
    Write-Host "Server URL: $Env:SERVER_URL"
    Invoke-RestMethod -Uri "$Env:SERVER_URL/download_transactions_decrypted" `
        -Method 'Get' `
        -Headers @{'token' = $Env:SERVER_TOKEN} `
        -OutFile "transactions_decrypted_downloaded.tsv"
}
catch {
    Write-Host "Failed to download decrypted transactions."
    Write-Host $_
    Pause
}