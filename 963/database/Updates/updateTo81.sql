USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW DH4B4A
-- 963 version: 963 V3.30 ALPHA-6
-- Description: Alarm panels not displaying on the client.
--
-- Detailed Description:
-- The issue mentioned above in description section is a result of some orphan records left in the 963 database.
-- The purpose of this sql script is not only to resolve this particular issue but to address any other issues related to orphan records in any of the
-- databse table in 963.
-- This script will create a stored procedure which will have all the necessary code to remove those orphan records from the 963 database.
-- And this script will be executed from 963 on startup, each time 963 starts up it will clean up the database from all unused data.
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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_cleanUpDatabase]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_cleanUpDatabase]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_cleanUpDatabase]

AS

BEGIN	
	
	-- Delete orphan records from AlarmGroupToWorkgroupLink table to resolve the issue described in MOSCOW DH4B4A
	DELETE FROM dbo.AlarmGroupToWorkgroupLink
	WHERE (alarmGroupID NOT IN (SELECT theIndex AS 'alarmGroupID' FROM AlarmGroup))

END
GO

-- make sure that you record the script creation error code into ##ScriptErrorLog table after each SQL statement
INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

-- execute the above created stored procedure here
exec [dbo].[usp_cleanUpDatabase]
GO

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