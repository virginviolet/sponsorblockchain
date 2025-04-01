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
    Write-Warning "Checkpoints will be uploaded and conflicting files will be replaced."
    Read-Host -Prompt "Press Enter to continue..."

    # Create zip file with the slot machine configuration
    $scriptDirPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $blockchainPackageDirPath = Split-Path -Parent $scriptDirPath
    $botDirPath = Split-Path -Parent $blockchainPackageDirPath
    $checkpointsDirPath = "$botDirPath\data\checkpoints"
    $zipFilePath = Join-Path -Path $scriptDirPath -ChildPath 'checkpoints.zip'
    $zipFilExists = Test-Path -Path $zipFilePath
    if ($zipFilExists) {
        Write-Host "Will use existing checkpoints.zip file."
        Read-Host -Prompt "Press Enter to continue..."
    } else {
        Compress-Archive -Path $checkpointsDirPath -DestinationPath $zipFilePath
    }

    Invoke-RestMethod -Uri "$serverUrl/upload_checkpoints" `
        -Method 'Post' `
        -Headers @{ 'token' = $Env:SERVER_TOKEN } `
        -ContentType 'multipart/form-data' `
        -InFile $zipFilePath
    Write-Host "Checkpoints uploaded successfully."

} catch {
    Write-Host "Failed to upload checkpoints."
    Write-Host $_
} finally {
    Read-Host "Press Enter to exit..."
}