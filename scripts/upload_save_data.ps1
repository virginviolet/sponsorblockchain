try {
    Import-Module Set-PsEnv

    Set-PsEnv

    Write-Warning "This script will replace save data on the server."
    Write-Host "Server URL: $Env:SERVER_URL"
    Pause
    
    # Create zip file with the slot machine configuration
    $scriptDirPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $blockchainPackageDirPath = Split-Path -Parent $scriptDirPath
    $botDirPath = Split-Path -Parent $blockchainPackageDirPath
    $saveDataDirPath = "$botDirPath\data\save_data"
    $zipFilePath = Join-Path -Path $scriptDirPath -ChildPath 'save_data.zip'
    $zipFilExists = Test-Path -Path $zipFilePath
    if ($zipFilExists) {
        Write-Host "Will use existing save_data.zip file."
        Pause
    } else {
        Compress-Archive -Path $saveDataDirPath -DestinationPath $zipFilePath
    }
    Invoke-RestMethod -Uri "$Env:SERVER_URL/upload_save_data" `
        -Method 'Post' `
        -Headers @{ 'token' = $Env:SERVER_TOKEN } `
        -ContentType 'multipart/form-data' `
        -InFile $zipFilePath

} catch {
    Write-Host "Failed to upload checkpoints."
    Write-Host $_
    Pause
}