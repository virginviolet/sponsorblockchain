try {
    Import-Module Set-PsEnv
    
    Set-PsEnv

    Write-Host "Server URL: $Env:SERVER_URL"
    Write-Warning "This script will replace the bot config on the server."
    Pause
    
    $scriptDirPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $blockchainPackageDirPath = Split-Path -Parent $scriptDirPath
    $botDirPath = Split-Path -Parent $blockchainPackageDirPath
    $botConfigPath = "$botDirPath\data\bot_configuration_production.json"
    Invoke-RestMethod -Uri "$Env:SERVER_URL/set_bot_config" `
        -Method 'Post' `
        -Headers @{'token' = $Env:SERVER_TOKEN; "Content-Type"="application/json"} `
        -Body (Get-Content -Raw -Path $botConfigPath)
}
catch {
    Write-Host $_
    Pause
}