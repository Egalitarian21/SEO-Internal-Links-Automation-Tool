Set shell = CreateObject("WScript.Shell")
scriptPath = "C:\Users\yiguo\Desktop\Internal Link Tool\Product\Internal-linking-tool v1\Codes\Launch-Internal-Link-Tool.ps1"
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & scriptPath & Chr(34)
shell.Run command, 0, False
