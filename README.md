# CanvasAutoDownload

Downloads the files of your favorite Canvas courses. Files are sorted by course and module. Files that are not part of a module end up in the `Other files` folder. Files that were already downloaded are skipped, so you can run the script as often as you like.

## Setup

1. Install [Python 3](https://www.python.org/downloads/). Tick "Add python.exe to PATH" in the installer.
2. Install the dependency in PowerShell:

   ```powershell
   pip install requests
   ```

3. Set the Canvas address of your university (the address you use to log in to Canvas in the browser, without any path) and open a new terminal:

   ```powershell
   setx CANVAS_URL "https://canvas.example"
   ```

4. On the Canvas dashboard, star the courses you want to sync. Only favorite courses are downloaded.
5. Create an access token in Canvas: Account -> Settings -> "+ New Access Token". Copy it right away, it is only shown once. Never share it.
6. Save the token in a file:

   ```powershell
   New-Item -ItemType Directory -Force "$env:APPDATA\canvas-auto-download"
   Set-Content -NoNewline "$env:APPDATA\canvas-auto-download\token" "PASTE_TOKEN_HERE"
   ```

7. Run it:

   ```powershell
   python canvas-auto-download.py
   ```

The files end up in `C:\Users\<name>\Documents\Canvas`.

## Run automatically (optional)

Create an hourly task in PowerShell (adjust the path to the script):

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\canvas-auto-download.py"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "canvas-auto-download" -Action $action -Trigger $trigger
```
