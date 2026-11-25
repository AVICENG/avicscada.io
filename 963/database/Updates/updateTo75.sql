--USE <96XDBNAME>
USE [i96X]
GO

--
-- This script is just to test the new process where 963 checks for the results of script execution
--

/****** Object:  View [dbo].[PlotsForModule]    Script Date: 07/03/2008 15:01:32 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- Create Temp table to store errors from this script

IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

CREATE TABLE ##ScriptErrorLog( [ErrorCode] [int] NOT NULL) ON [PRIMARY]
GO


-- encapsulate the whole script into a transaction
BEGIN TRAN Script_TRAN
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Script code starts from here
--///////////////////////////////////////////////////////////////////////////////////

-- Update device type for TOPS served Zigbee INC
UPDATE [dbo].[Types] SET [subType] = N'Z' WHERE Name = N'INC' AND Type = N'I' AND subType = N'z'
GO

-- insert error code for the above sql statement into temp error log table
INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

-- Update device type for ZINC (Zigbee Lan), IQeco
UPDATE [dbo].[Types] SET [subType] = N'z' WHERE Name = N'ZINC' AND Type = N'I' AND subType = N'Z'
GO

-- insert error code for the above sql statement into temp error log table
INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Script code ends here
--///////////////////////////////////////////////////////////////////////////////////


-- at the end of the script code
-- check the status of sql script, commit transaction if successful and log the results into 963 version table
-- otherwise roll back the transaction and log the results into 963 versiont table

DECLARE @VersionNumber int
SET @VersionNumber = (SELECT TOP 1 VersionNum FROM Version ORDER BY VersionNum DESC)

IF ( (SELECT COUNT(ErrorCode) FROM  ##ScriptErrorLog WHERE ErrorCode != 0) > 0)
BEGIN
	-- script failed
	-- Update Version table in 963 database with script execution end date and success status
	ROLLBACK TRAN Script_TRAN
	PRINT N'Script Failed'

	UPDATE Version SET RunFinished = GETDATE(), Result = N'Failed' WHERE VersionNum = @VersionNumber
END
ELSE
BEGIN
	-- script successful
	-- Update Version table in 963 database with script execution end date and success status
	COMMIT TRAN Script_TRAN
	PRINT N'Script Successful'
	
	UPDATE Version SET RunFinished = GETDATE(), Result = N'Success' WHERE VersionNum = @VersionNumber
END
GO

-- delete temp error log table
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

SET ANSI_NULLS OFF
GO
SET QUOTED_IDENTIFIER OFF
GO