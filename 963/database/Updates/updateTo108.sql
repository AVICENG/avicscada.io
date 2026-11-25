USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: CC76C2
-- 963 version: v3.50 ALPHA-3
-- Description: Add new device types for IQ3 derivative -- IQ4
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

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'q' AND [dbo].[Types].[subType] = N'4')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'q' /*Type*/, N'IQ4' /*Name*/, 0 /*IsSupervisor*/, 1 /*DoesTextComms*/, 
	-1 /*NumSensors*/, -1 /*NumDrivers*/, -1 /*NumKnobs*/, -1 /*NumInputs*/, -1 /*NumSwitches*/, -1 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'4' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
GO

SET ANSI_NULLS OFF
GO
SET QUOTED_IDENTIFIER OFF
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