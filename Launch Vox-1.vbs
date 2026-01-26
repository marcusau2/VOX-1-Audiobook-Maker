' ============================================
' VOX-1 Audiobook Generator Launcher (Hidden)
' ============================================

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the script directory
objShell.CurrentDirectory = scriptDir

' Check if Python 3.10 is available
On Error Resume Next
result = objShell.Run("py -3.10 --version", 0, True)
On Error GoTo 0

If result <> 0 Then
    MsgBox "ERROR: Python 3.10 is not installed or not found." & vbCrLf & vbCrLf & _
           "Please install Python 3.10.8 from:" & vbCrLf & _
           "https://www.python.org/downloads/release/python-3108/", _
           vbCritical, "VOX-1 Launcher"
    WScript.Quit 1
End If

' Launch the GUI without showing console window (0 = hidden)
objShell.Run "py -3.10 app.py", 0, False

' Exit
WScript.Quit
