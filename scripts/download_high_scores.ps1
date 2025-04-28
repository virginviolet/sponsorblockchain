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
    Invoke-RestMethod -Uri "$serverUrl/get_leaderboard_slots" `
        -Method 'Get' `
        -Headers @{'token' = $Env:SERVER_TOKEN } `
        -OutFile "slot_machine_high_scores_downloaded.json"
    Write-Host "Slot machine high scores downloaded successfully."
} catch {
    Write-Host "Failed to download slot machine high scores."
    Write-Host $_
} finally {
    Read-Host "Press Enter to exit..."
}