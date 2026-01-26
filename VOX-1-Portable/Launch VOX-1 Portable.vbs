' ============================================
' VOX-1 Portable Launcher
' ============================================

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
portableDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Check if setup was run
If Not objFSO.FileExists(portableDir & "\python310\python.exe") Then
    MsgBox "ERROR: Portable version not set up!" & vbCrLf & vbCrLf & _
           "Please run Setup-Portable.bat first." & vbCrLf & vbCrLf & _
           "If you haven't downloaded Python yet, run:" & vbCrLf & _
           "1. Download-Python.bat" & vbCrLf & _
           "2. Setup-Portable.bat", _
           vbCritical, "VOX-1 Portable"
    WScript.Quit 1
End If

If Not objFSO.FileExists(portableDir & "\app\app.py") Then
    MsgBox "ERROR: Application files not found!" & vbCrLf & vbCrLf & _
           "Please run Setup-Portable.bat to copy app files.", _
           vbCritical, "VOX-1 Portable"
    WScript.Quit 1
End If

' Change to app directory
objShell.CurrentDirectory = portableDir & "\app"

' Launch the GUI using portable Python (hidden window)
pythonPath = portableDir & "\python310\python.exe"
appPath = portableDir & "\app\app.py"

objShell.Run """" & pythonPath & """ """ & appPath & """", 0, False

' Exit
WScript.Quit
