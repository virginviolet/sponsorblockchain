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
    Write-Warning "This script will replace the slot machine high scores on the server."
    Read-Host -Prompt "Press Enter to continue..."
    $scriptDirPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $blockchainPackageDirPath = Split-Path -Parent $scriptDirPath
    $botDirPath = Split-Path -Parent $blockchainPackageDirPath
    $highScorePath = "$botDirPath\data\slot_machine_high_scores_production.json"
    $highScoreData = Get-Content -Raw -Path $highScorePath
    Invoke-RestMethod -Uri "$serverUrl/set_leaderboard_slots" `
        -Method 'Post' `
        -Headers @{'token' = $Env:SERVER_TOKEN; "Content-Type" = "application/json" } `
        -Body $highScoreData
    Write-Host "$highScoreData"
    Write-Host "Slot machine high scores uploaded successfully."
} catch {
    Write-Host "Failed to upload slot machine high scores."
    Write-Host $_
} finally {
    Read-Host "Press Enter to exit..."
}