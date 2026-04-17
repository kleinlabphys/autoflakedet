Public Const StatusUnknown = -1
Public Const StatusFalse = 0
Public Const StatusTrue = 1

dim nikonLV
set nikonLV = CreateObject ("Nikon.LvMic.NikonLV")

If (nikonLV.Nosepiece.IsMounted = StatusTrue) Then
	nikonLV.Nosepiece.Forward
	dim lPos
	lPos = nikonLV.Nosepiece.Position
	dim strMsg
	newName = nikonLV.Database.Objectives(lPos).ObjectiveData
	canModify = nikonLV.Database.Objectives(lPos).CanModify
	' nikonLV.Database.Objectives(lPos).Name = newName
	strMsg = "Nosepiece.Position: " & CStr(lPos) & vbCr
	strMsg = strMsg & "Name: " & nikonLV.Database.Objectives(lPos).Name & vbCr
	strMsg = strMsg & "Description: " & nikonLV.Database.Objectives(lPos).Description & vbCr

	Dim DbObjectives
	Set DbObjectives =NikonLv.Database.Objectives

	' DbObjectives(lPos).Name = ""

	' Dim newObj
	' Set newObj = nikonLv.Database.CreateObjective()

	' newObj.Name = "something"
	' newObj.Magnification = 40

	' newObj.Save

	' WScript.Echo newObj.Name
	' WScript.Echo DbObjectives(lPos).Name
	WScript.Echo strMsg
	' WScript.Echo canModify & " <-- modify status"
Else
	WScript.Echo "Nosepiece is not mounted."
End If
