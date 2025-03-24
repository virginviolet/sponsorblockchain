try {
    Import-Module Set-PsEnv
    
    Set-PsEnv
    
    Write-Warning "This script will replace the slot machine configuration on the server."
    Write-Host "Server URL: $Env:SERVER_URL"
    Pause
    
    $scriptDirPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $blockchainPackageDirPath = Split-Path -Parent $scriptDirPath
    $botDirPath = Split-Path -Parent $blockchainPackageDirPath
    $slotMachineConfigPath = "$botDirPath\data\slot_machine_production.json"
    
    Invoke-RestMethod -Uri "$Env:SERVER_URL/set_slot_machine_config" `
        -Method 'Post' `
        -Headers @{'token' = $Env:SERVER_TOKEN; "Content-Type"="application/json"} `
        -Body (Get-Content -Raw -Path $slotMachineConfigPath)
}
catch {
    Write-Host $_
    Pause
}