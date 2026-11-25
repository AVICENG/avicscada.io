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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_setupRetransmissionTypes]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_setupRetransmissionTypes]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_setupRetransmissionTypes] 

AS

/*
	Called to set up the default values within the RetransmissionTypes table
*/

BEGIN TRAN

-- Disable all constraints and triggers
ALTER TABLE RetransmissionTypes NOCHECK CONSTRAINT all
ALTER TABLE RetransmissionTypes DISABLE TRIGGER all

-- Delete all the data from the retransmission destinations table
DELETE FROM RetransmissionDestinations

-- Delete all data from the Retransmission types table
DELETE FROM RetransmissionTypes

-- Allow insert of explicit identities
SET IDENTITY_INSERT RetransmissionTypes ON

INSERT INTO RetransmissionTypes(theIndex,theCommandCode) 
VALUES(1,N'EMAIL')

INSERT INTO RetransmissionTypes(theIndex,theCommandCode) 
VALUES(2,N'TRENDTEXT')

INSERT INTO RetransmissionTypes(theIndex,theCommandCode) 
VALUES(3,N'TRENDPAGER')

INSERT INTO RetransmissionTypes(theIndex,theCommandCode) 
VALUES(4,N'FREEFORMAT')

INSERT INTO RetransmissionTypes(theIndex,theCommandCode) 
VALUES(5,N'SNMP')

INSERT INTO RetransmissionTypes(theIndex,theCommandCode) 
VALUES(6,N'SMS')

-- Turn off insertation of explicit identities
SET IDENTITY_INSERT RetransmissionTypes OFF

-- Disable all constraints and triggers
ALTER TABLE RetransmissionTypes CHECK CONSTRAINT all
ALTER TABLE RetransmissionTypes ENABLE TRIGGER all

IF @@ERROR <> 0 GOTO anError

COMMIT TRAN

GOTO FINISH

anError:
IF @@TRANCOUNT > 0
BEGIN
	PRINT N'Error adding data to retransmission types table'
	ROLLBACK TRAN
END

FINISH:

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