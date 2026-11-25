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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_deleteHistoricData]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_deleteHistoricData]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE  PROCEDURE [dbo].[usp_deleteHistoricData]

@start DATETIME,
@end DATETIME,
@purge_unacked BIT,
@purge_current BIT,
@delAlarmsOnly int OUTPUT

AS

-- The alarms table has a self-referencing foreign key between occurred and clear alarms, so we need to delete in two steps
-- first occurred and then cleared.
-- Problems are caused when we specify to purge alarms that are acked. If the clear alarm is acked, but the occurred alarm
-- is not, a foreign key violation will occur as we are trying to delete the clear alarm, but the corresponding occurred
-- alarm was not deleted in the first step. When we delete the clear alarms we will need to test whether any occurred alarms
-- exist that may reference this alarm.


DECLARE @occ INT
DECLARE @clr INT
DECLARE @log INT

IF (@purge_unacked = 1)
BEGIN

	IF (@purge_current = 0)
	BEGIN

		-- DELETE only non-current (where acked and unacked)

		DELETE FROM Alarms -- Occ
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID <> theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID = theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end) 
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))

		SET @clr = @@ROWCOUNT
	END
	ELSE
	BEGIN

		-- DELETE clear and current (where acked and unacked)

		DELETE FROM Alarms -- Occ
		WHERE	((clearAlarmID IS NULL) OR (clearAlarmID <> theIndex))
			AND (originalAlarmTime BETWEEN @start AND @end)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(originalAlarmTime BETWEEN @start AND @end)
			AND (clearAlarmID = theIndex)
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))

		SET @clr = @@ROWCOUNT
	END
END
ELSE -- IF @purge_unacked = 0
BEGIN

	IF (@purge_current = 0)
	BEGIN

		-- DELETE only non-current where acked

		DELETE FROM Alarms -- Occ
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID <> theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end)
			AND (ackedAlarm = 1)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID = theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end) 
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))
			AND (ackedAlarm = 1)

		SET @clr = @@ROWCOUNT
	END
	ELSE
	BEGIN

		-- DELETE current and clear where acked

		DELETE FROM Alarms -- Occ
		WHERE	((clearAlarmID IS NULL) OR (clearAlarmID <> theIndex))
			AND (originalAlarmTime BETWEEN @start AND @end)
			AND (ackedAlarm = 1)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(originalAlarmTime BETWEEN @start AND @end)
			AND (clearAlarmID = theIndex)
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))
			AND (ackedAlarm = 1)

		SET @clr = @@ROWCOUNT
	END
END



-- Now DELETE the recorded data logs between the two dates
SET @log = 0
IF (@delAlarmsOnly = 0)
BEGIN

	DELETE FROM PointValue WHERE DataTime BETWEEN @start AND @end	
	SET @log = @@ROWCOUNT
	
END

INSERT INTO DatabaseDeletionHistory([NumClear], [NumOcc], [NumRecorded], [StartDate], [EndDate]) VALUES (@clr, @occ, @log, @start, @end)

SET @delAlarmsOnly = (@clr + @occ)

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