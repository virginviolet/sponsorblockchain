param(
    [string]$from,
    [string]$to,
    [int]$amount
)
try {
    Import-Module Set-PsEnv
    
    Set-PsEnv
    
    $transaction = @{
        sender = $from
        receiver = $to
        amount = $amount
        method = "manual"
    }
    Write-Host "Server URL: $Env:SERVER_URL"
    $body = @{"data" = @(@{"transaction" = $transaction})} | ConvertTo-Json -Depth 3
    Write-Host "Body: $body"
    Invoke-RestMethod -Uri "$Env:SERVER_URL/add_block" `
        -Method 'Post' `
        -Headers @{'token' = $Env:SERVER_TOKEN} `
        -ContentType 'application/json' `
        -Body $body
}
catch {
    Write-Host "Failed to add block."
    Write-Host $_
    Pause
}