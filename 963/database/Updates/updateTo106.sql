--
-- TAG_ALARM_SCRIPT
-- This process applies to all future scripts above updateTo74.sql
-- Note: In your actual script code (see section below) ensure that you log the @@ERROR into temp table i.e. ##ScriptErrorLog
-- at the end of each sql statement
--

USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: DS75FC
-- 963 version: 963 v3.40 ALPHA - 5
-- Description: 963 misinterprets SetPoint deviation attribute alarms as PV fail.
-- Attribute alarm parameters for PVFL and SDEV are not insert properly. They are actaully interchanged no need to interchange again to make it proper.
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

UPDATE [dbo].[Lookup] SET [dbo].[Lookup].[attributeCodeLookup] = 1 WHERE [dbo].[Lookup].[AlarmCode] = N'PVFL'
GO
UPDATE [dbo].[Lookup] SET [dbo].[Lookup].[attributeCodeLookup] = 0 WHERE [dbo].[Lookup].[AlarmCode] = N'SDEV'

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