USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: JA7356
-- 963 version: v3.51 WIP-1
-- Description: Add new device types for ANC subtypes -- TMNG, TMNH, TMHE, MNC, AND, XN28
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

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'A' AND [dbo].[Types].[subType] = N'G')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'A' /*Type*/, N'TMNG' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'G' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
GO

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'A' AND [dbo].[Types].[subType] = N'D')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'A' /*Type*/, N'TMNH' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'D' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
GO

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'A' AND [dbo].[Types].[subType] = N'E')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'A' /*Type*/, N'TMNE' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'E' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
GO

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'A' AND [dbo].[Types].[subType] = N'M')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'A' /*Type*/, N'AND' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'M' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
GO

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'A' AND [dbo].[Types].[subType] = N'T')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'A' /*Type*/, N'MNC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'T' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
GO

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'A' AND [dbo].[Types].[subType] = N'X')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'A' /*Type*/, N'XN28' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'X' /*subType*/, 0 /*NumPlots*/,	1000 /*NumPoints*/)
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