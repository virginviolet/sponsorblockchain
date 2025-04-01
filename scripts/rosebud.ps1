try {
    # https://www.powershellgallery.com/packages/Set-PsEnv
    Import-Module Set-PsEnv
    # https://www.powershellgallery.com/packages/InteractiveMenu
    Import-Module InteractiveMenu
    
    Set-PsEnv

    if (-not $Env:SERVER_URL_LOCAL) {
        $message = "SERVER_URL_LOCAL is not set. " + `
            "Set it with the the .env file and restart your console. " + `
            "Make sure you are running this script from " + `
            "this script's directory."
        Write-Host $message
        exit 1
    } elseif (-not $Env:SERVER_URL_PRODUCTION) {
        $message = "SERVER_URL_PRODUCTION is not set. " + `
            "Add it to a file named `.env` in the script's directory " + `
            "and restart your console. " + `
            "Make sure you are running this script from " + `
            "this script's directory."
        Write-Host "SERVER_URL_PRODUCTION is not set. "
    }
    $answerItems = @(
        Get-InteractiveChooseMenuOption `
            -Value "$Env:SERVER_URL_LOCAL" `
            -Label "$Env:SERVER_URL_LOCAL" `
            -Info "Local server"
        Get-InteractiveChooseMenuOption `
            -Value "$Env:SERVER_URL_PRODUCTION" `
            -Label "$Env:SERVER_URL_PRODUCTION" `
            -Info "Production server"
    )
    $question = "Pick server"
    $serverUrl = Get-InteractiveMenuChooseUserSelection -Question $question -Answers $answerItems
    $transaction = @{
        sender   = "rosebud"
        receiver = $Env:USER_HASHED
        amount   = 1000
        method   = "manual"
    }
    $body = @{"data" = @(@{"transaction" = $transaction }) } | ConvertTo-Json -Depth 3
    Write-Host "Body: $body"
    Read-Host -Prompt "Press Enter to continue..."
    Invoke-RestMethod -Uri "$serverUrl/add_block" `
        -Method 'Post' `
        -Headers @{'token' = $Env:SERVER_TOKEN } `
        -ContentType 'application/json' `
        -Body $body
} catch {
    Write-Host "Failed to add block."
    Write-Host $_
} finally {
    Read-Host "Press Enter to exit..."
}