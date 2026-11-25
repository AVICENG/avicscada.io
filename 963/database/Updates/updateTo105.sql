
USE <96XDBNAME>
--USE [i96X]
GO

--
-- TAG_ALARM_SCRIPT
-- MoSCoW Ref: SA750E
-- 963 version:963 v3.40 ALPHA - 4
-- Description: New alarm for IQeco V2 Release.
-- If a strategy load fails due to licensing issues then an alarm will be sent out via the “General Alarm Group”.
-- Alarm Code – FLIC
-- Alarm Description – Strategy Licence Err (20 character maximum)

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

	-- SET FLIC alarm
	-- Orginated from IQeco v2.0 controller in case of strategy load fail due to licensing issue.
	IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FLIC')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FLIC', N'Strategy Licence Error', 0, 0, 1, 16, N'R', NULL, 57923)


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

GO