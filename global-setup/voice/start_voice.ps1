# global-setup/voice/start_voice.ps1
# Claude Code SessionStart 시 voice_input.py 를 백그라운드로 자동 실행.
# 이미 실행 중이면 중복 실행하지 않음.

$VoiceScript = Join-Path $HOME ".claude\voice\voice_input.py"

# 이미 실행 중인지 확인 (CommandLine은 CIM으로만 조회 가능)
$running = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*voice_input.py*" }

if ($running) { exit 0 }

# python 명령어 탐색
$python = $null
foreach ($cmd in @("python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $python = $cmd
        break
    }
}

if (-not $python) { exit 1 }
if (-not (Test-Path $VoiceScript)) { exit 1 }

Start-Process $python -ArgumentList "`"$VoiceScript`" --hotkey f9" -WindowStyle Hidden -WorkingDirectory (Split-Path $VoiceScript)

# Toast 알림 — 보이스 데몬 시작 알림
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml("<toast duration='short'><visual><binding template='ToastGeneric'><text>&#127908; Voice Input 준비됨</text><text>Ctrl+Shift+Space 로 토글</text></binding></visual></toast>")
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude.Code").Show(
        [Windows.UI.Notifications.ToastNotification]::new($xml)
    )
} catch { }

