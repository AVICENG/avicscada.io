USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: SA720A
-- Product version: 963 v3.40 ALPHA-2
-- Description: Microsoft has deprecated some of the features and functionality which is being 
-- used by 963. The rcommendation from Microsoft is to remove these deprecated features/APIs/procedures 
-- from your code and replace them with supported ones as the depreated ones will be a part of their 
-- discontinued list from next versions of SQL Server.
--

-- Create Temp table to store errors from this script
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

CREATE TABLE ##ScriptErrorLog( [ErrorCode] [int] NOT NULL) ON [PRIMARY]
GO


-- Encapsulate the whole script into one transaction
BEGIN TRAN Script_TRAN
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code starts here
--///////////////////////////////////////////////////////////////////////////////////

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_insertDefaultAlarmGroup]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_insertDefaultAlarmGroup]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_insertDefaultAlarmGroup]
(
	@defaultAlarmGroupTitle nvarchar(255), -- Default alarm group text
	@defaultAction nvarchar(1024), -- Default alarm action
	@defaultPrintText nvarchar(1024), -- Default print text
	@oldLabelText nvarchar(1024) -- Old Alarm Group Label
)

AS

-- modify the old alarm group label if it exists

IF EXISTS (SELECT title FROM AlarmGroup WHERE title = @oldLabelText)
BEGIN
	UPDATE AlarmGroup SET title = @defaultAlarmGroupTitle WHERE title = @oldLabelText
END

-- If the temporary title is NULL then create the default alarm group
IF NOT EXISTS (SELECT 1 FROM AlarmGroup WHERE title = @defaultAlarmGroupTitle)
BEGIN
		INSERT INTO AlarmGroup (title,backgroundColour,actionWhenOcc,actionWhenNoc,
		diaryGroupID,displayMsg,wavForWrkgrp,PrintOptionsUpdated,PrintWhat,PrintAlarms,
		DisplayPanel,PanelColour,PanelPosX,PanelPosY)
		VALUES(@defaultAlarmGroupTitle,255,@defaultAction,' ',-1,0,' ',1,@defaultPrintText,1,0,255,0,0)
END

GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code ends here
--///////////////////////////////////////////////////////////////////////////////////


-- at the end of whole script code, check the execution status of this sql script
-- commit transaction if successful and log the Success message into 963 version table
-- otherwise roll back the transaction and log the failure message into 963 version table

DECLARE @VersionNumber int
SET @VersionNumber = (SELECT TOP 1 VersionNum FROM Version ORDER BY VersionNum DESC)

IF ( (SELECT COUNT(ErrorCode) FROM  ##ScriptErrorLog WHERE ErrorCode != 0) > 0)
BEGIN
	-- script failed
	-- Update Version table in 963 database with script execution end date and success status
	-- and roll back the transaction
	ROLLBACK TRAN Script_TRAN
	PRINT N'Script Failed'

	UPDATE Version SET RunFinished = GETDATE(), Result = N'Failed' WHERE VersionNum = @VersionNumber
END
ELSE
BEGIN
	-- script successful
	-- Update Version table in 963 database with script execution end date and success status
	-- and commit the transaction
	COMMIT TRAN Script_TRAN
	PRINT N'Script Successful'
	
	UPDATE Version SET RunFinished = GETDATE(), Result = N'Success' WHERE VersionNum = @VersionNumber
END
GO

-- delete temp error log table
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

GO