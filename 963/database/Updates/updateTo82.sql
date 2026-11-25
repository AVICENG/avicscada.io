USE <96XDBNAME>
--USE [i96X]
GO

--
-- TAG_ALARM_SCRIPT
-- MoSCoW SA72C2
-- 963 version: 963 V3.30 ALPHA-7
-- Description: General Alarm Message reception fully integrated into 963 alarm reception
--
-- Detailed Description:
-- General alarm message is sent both when the alarm condition occurs and when it is cleared with SET and CLEAR
-- semantics as per other Trend alarms
--

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS OFF
GO

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

	-- SET GENL alarm
	-- orginated from Sensors, analog drivers, digital drivers and digital inputs
	IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'GENL')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'GENL', N'General Alarm', 1, 1, 1, 100, N'S,D,J,I', NULL, 41615)

	-- CLEAR GENL alarm
	-- orginated from Sensors, analog drivers, digital drivers and digital inputs
	IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CGEN')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CGEN', N'Clear General Alarm', 0, 0, 1, 100, N'S,D,J,I', @@IDENTITY, 41616)

	-- make sure that you record the script creation error code into ##ScriptErrorLog table after each SQL statement
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

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER OFF
GO