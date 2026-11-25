--
-- if default alarm group already exists with old format then replace it with new format
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS OFF 
GO


/****** Object:  Stored Procedure dbo.usp_insertDefaultAlarmGroup    Script Date: 10/11/2004 15:18:53 ******/



ALTER       PROCEDURE dbo.usp_insertDefaultAlarmGroup

(
	@defaultAlarmGroupTitle nvarchar(255), -- Default alarm group text
	@defaultAction nvarchar(1024), -- Default alarm action
	@defaultPrintText nvarchar(1024), -- Default print text
	@oldLabelText nvarchar(1024) -- Old Alarm Group Label
)

AS


-- modify the old alarm group label if it exists

IF Exists (SELECT title FROM AlarmGroup Where title = @oldLabelText)
BEGIN
	UPDATE AlarmGroup SET title = @defaultAlarmGroupTitle WHERE title = @oldLabelText
END

-- If the temporary title is NULL then create the default alarm group
If Not Exists (Select 1 from AlarmGroup where title = @defaultAlarmGroupTitle)
	Begin
		Insert into AlarmGroup (title,backgroundColour,actionWhenOcc,actionWhenNoc,
		diaryGroupID,displayMsg,wavForWrkgrp,PrintOptionsUpdated,PrintWhat,PrintAlarms,
		DisplayPanel,PanelColour,PanelPosX,PanelPosY)
		Values(@defaultAlarmGroupTitle,255,@defaultAction,' ',-1,0,' ',1,@defaultPrintText,1,0,255,0,0)
	End

GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

