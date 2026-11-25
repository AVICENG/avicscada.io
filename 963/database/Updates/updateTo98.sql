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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_logAlarm]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_logAlarm]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_logAlarm] 

@newPointID INT,
@newAlarmCodeID INT,
@newTheDesc NVARCHAR(255),
@newUserText NVARCHAR(4000),
@newOriginalAlarmTime DATETIME,
@newReceivedTime DATETIME,
@newRequiresUserAction BIT,
@newPriorityLevel INT,
@newIsCurrent BIT,
@unackedClearCountAdjust INT OUTPUT,
@unackedCurrentCountAdjust INT OUTPUT,
@newAlarmID INT OUTPUT

AS

--
-- If there is a -1 point reference then make it a null value
--

IF (@newPointID <= 0) 
BEGIN
	SET @newPointID = NULL
END

--
-- If there is a -1 alarm code then make it a system alarm event

IF (@newAlarmCodeID <= 0)
BEGIN
	-- Index 80 is SYST!
	SET @newAlarmCodeID = 80
END
--

--
-- If the alarm is auto actioned then set up the correct parameters for it
--

DECLARE @newAckedAlarm BIT
DECLARE @newAckedUser NVARCHAR(255)
DECLARE @newAckedTime DATETIME

IF (@newRequiresUserAction = 1)
BEGIN
	--PRINT(N'Action does require user action')
	SET @newAckedAlarm = 0
	SET @newAckedUser  = N''
	SET @newAckedTime  = NULL
END
ELSE
BEGIN
	--PRINT(N'Action does NOT require user action')
	SET @newAckedAlarm = 1
	SET @newAckedUser  = N'963-SYST'
	SET @newAckedTime  = @newReceivedTime
END

DECLARE @newClearToID INT

--
-- Insert the alarm into the main alarms table
--

INSERT INTO Alarms (pointID, alarmCodeID, theDesc, userText, originalAlarmTime, receivedTime, ackedAlarm, ackedUser, ackedTime, priorityLevel)
	VALUES(@newPointID, @newAlarmCodeID, @newTheDesc, @newUserText, @newOriginalAlarmTime, @newReceivedTime, @newAckedAlarm, @newAckedUser, @newAckedTime, @newPriorityLevel)

-- Make a note of the new alarm ID
SET @newAlarmID = @@IDENTITY

--
-- Update the corresponding alarms if there are any
--

-- If the alarm is not current then do a look up for a corresponding current alarm
IF (@newIsCurrent = 0)
BEGIN
	--PRINT(N'Alarm is NOT current hence it must be cleared')

	IF (@newAckedTime IS NULL)
	BEGIN
		-- Indicate that the new alarm is clear
		SET @unackedClearCountAdjust = 1
	END

	-- If we have a clear alarm then make it point to itself
	UPDATE Alarms SET clearAlarmID = @newAlarmID WHERE theIndex = @newAlarmID

	-- If we have a clear alarm then find the occ alarm code id and use it to look up some of the data
	DECLARE @alarmID INT
	SET @alarmID = NULL
	
	SELECT @alarmID = clearToID FROM Lookup WHERE theIndex = @newAlarmCodeID

	IF (@alarmID IS NOT NULL)
	BEGIN
		-- Change any other alarms that are the corresponding clear
		UPDATE Alarms SET clearAlarmID = @newAlarmID WHERE pointID = @newPointID AND clearAlarmID IS NULL AND alarmCodeID = @alarmID
		--PRINT N'The occ ID: ' + CAST(@occID AS NVARCHAR(10)) + 'The new code: ' + CAST(@newAlarmCodeID AS NVARCHAR(10))
	END
END
ELSE
BEGIN
	--PRINT(N'Alarm is current')
	IF (@newAckedTime IS NULL)
	BEGIN
		-- Indicate that the new alarm is occurred and hence current
		SET @unackedCurrentCountAdjust = 1
	END
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