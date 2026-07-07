Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & root & "\scripts\launch-hidden.ps1"" -ProjectRoot """ & root & """"
exitCode = shell.Run(command, 0, True)
If exitCode <> 0 Then
  shell.Popup "SEO internal link MVP failed to start. Please check logs\start-local.log.", 10, "Startup failed", 48
End If
