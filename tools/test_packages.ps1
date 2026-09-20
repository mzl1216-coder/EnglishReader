$ErrorActionPreference = 'Stop'
$TaskRoot = Split-Path -Parent $PSScriptRoot
$TaskTestRoot = Join-Path $TaskRoot 'test-results\packages'
$TaskTest = Join-Path $TaskTestRoot ([guid]::NewGuid().ToString())
$TaskPortable = Join-Path $TaskTest 'portable'
$TaskInstalled = Join-Path $TaskTest 'installed'
New-Item -ItemType Directory -Force $TaskTest | Out-Null
Expand-Archive -LiteralPath (Join-Path $TaskRoot 'dist\EnglishReader-Portable-x64.zip') -DestinationPath $TaskPortable -Force

function Test-ReaderBundle($Executable, $DataDirectory) {
    $TaskOldPath = $env:PATH
    try {
        $env:PATH = "$env:SystemRoot\system32;$env:SystemRoot"
        $env:ENGLISHREADER_DATA_DIR = $DataDirectory
        $TaskProcess = Start-Process -FilePath $Executable -ArgumentList '--smoke-test' -WindowStyle Hidden -PassThru
        if (-not $TaskProcess.WaitForExit(30000)) { $TaskProcess.Kill(); throw 'Application timed out' }
        if ($TaskProcess.ExitCode -ne 0) { throw "Application exit code $($TaskProcess.ExitCode)" }
        $TaskReport = Get-Content -LiteralPath (Join-Path $DataDirectory 'EnglishReader\smoke-test.json') | ConvertFrom-Json
        if (-not $TaskReport.visible -or -not $TaskReport.frozen) { throw 'Bundled Qt window or runtime failed' }
        return $TaskReport
    } finally {
        $env:PATH = $TaskOldPath
    }
}

$TaskPortableResult = Test-ReaderBundle (Join-Path $TaskPortable 'EnglishReader.exe') (Join-Path $TaskTest 'portable-data')
$TaskInstaller = Join-Path $TaskRoot 'dist\EnglishReader-Setup-x64.exe'
$TaskInstallProcess = Start-Process -FilePath $TaskInstaller -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS',"/DIR=`"$TaskInstalled`"" -WindowStyle Hidden -PassThru -Wait
if ($TaskInstallProcess.ExitCode -ne 0) { throw "Installer exit code $($TaskInstallProcess.ExitCode)" }
$TaskInstallResult = Test-ReaderBundle (Join-Path $TaskInstalled 'EnglishReader.exe') (Join-Path $TaskTest 'installed-data')

# Remove only the test installation created above, using its own uninstaller.
$TaskResolvedInstall = [System.IO.Path]::GetFullPath($TaskInstalled)
if (-not $TaskResolvedInstall.StartsWith([System.IO.Path]::GetFullPath($TaskTest) + '\')) { throw 'Unexpected test installation path' }
$TaskUninstall = Start-Process -FilePath (Join-Path $TaskResolvedInstall 'unins000.exe') -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -WindowStyle Hidden -PassThru -Wait
if ($TaskUninstall.ExitCode -ne 0) { throw "Uninstaller exit code $($TaskUninstall.ExitCode)" }
@{ portable = $TaskPortableResult; installed = $TaskInstallResult; installerExit = $TaskInstallProcess.ExitCode; uninstallExit = $TaskUninstall.ExitCode; directory = $TaskTest } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $TaskTestRoot 'report.json')
Get-Content -LiteralPath (Join-Path $TaskTestRoot 'report.json')
