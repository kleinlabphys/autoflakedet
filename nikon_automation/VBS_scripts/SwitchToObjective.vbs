Public Const StatusUnknown = -1
Public Const StatusFalse = 0
Public Const StatusTrue = 1

Dim args
Set args = WScript.Arguments
Dim desiredObjective
desiredObjective = args(0)

Dim nikonLV
Set nikonLV = CreateObject ("Nikon.LvMic.NikonLV")

WScript.Echo desiredObjective

Dim objectivePositionToMagnification
Set objectivePositionToMagnification = CreateObject("Scripting.Dictionary")

objectivePositionToMagnification.Add "2.5x", 1
objectivePositionToMagnification.Add "5x", 2
objectivePositionToMagnification.Add "20x", 3
objectivePositionToMagnification.Add "50x", 4
objectivePositionToMagnification.Add "100x", 5

If objectivePositionToMagnification.Exists(desiredObjective) Then
    WScript.Echo "Setting Microscope Objective to " & desiredObjective
Else
    WScript.Echo "Magnification not found."
	WScript.Quit
End If

Dim targetPosition
targetPosition = objectivePositionToMagnification(desiredObjective)
If (nikonLV.Nosepiece.IsMounted = StatusTrue) Then
	Dim lPos
	lPos = nikonLV.Nosepiece.Position

	If lPos < targetPosition Then
		While lPos < targetPosition
			nikonLV.Nosepiece.Forward
			lPos = lPos + 1
		Wend
	ElseIf lPos > targetPosition Then
		While lPos > targetPosition
			nikonLV.Nosepiece.Reverse
			lPos = lPos - 1
		Wend
	Else
	End If

	WScript.Echo "Objective now set to " & desiredObjective
Else
	WScript.Echo "Nosepiece is not mounted."
End If
