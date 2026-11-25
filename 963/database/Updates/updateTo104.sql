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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_setupTypes]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_setupTypes]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_setupTypes] 

AS

/*
	Called to set up the default values within the Types table
*/

BEGIN TRAN

-- Disable all constraints and triggers
ALTER TABLE [dbo].[Types] NOCHECK CONSTRAINT all
ALTER TABLE [dbo].[Types] DISABLE TRIGGER all

-- Delete all data from the Types table
DELETE FROM [dbo].[Types]

-- Allow insert of explicit identities
SET IDENTITY_INSERT [dbo].[Types] ON

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(1,N'M',N'MNC',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(2,N':',N'IQ251',0,-1,96,64,60,96,60,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(3,N'1',N'IQ150 v2',0,0,4,4,4,4,4,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(4,N'9',N'FNC',0,-1,99,0,10,0,10,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(5,N'2',N'IQ 150 v3',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(6,N'3',N'IQ151',0,-1,48,32,30,48,20,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(7,N'4',N'IQ131',0,-1,32,12,25,32,20,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(8,N'5',N'IQ111',0,-1,32,12,25,32,20,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(9,N'6',N'IQ100',0,-1,32,12,25,32,20,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(10,N'7',N'IQ9x',0,-1,12,6,6,12,6,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(11,N'8',N'IQ7x',0,-1,12,8,6,12,6,1,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(12,N'A',N'ANC',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(13,N'C',N'CNC+',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(14,N'D',N'Non Trend',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(15,N'E',N'Non Trend(Text)',0,-1,24,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(16,N'F',N'TONIC Host',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(17,N'G',N'TONIC IQ',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(18,N'I',N'INC',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(19,N'P',N'PNC',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(20,N'X',N'XNC',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(21,N'Z',N'OEM',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(22,N'a',N'920/921',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(23,N'e',N'950/951',-1,-1,24,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(24,N'j',N'940',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(25,N'k',N'943 v1',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(26,N'l',N'943 v1.1',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(27,N'm',N'942',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(28,N'n',N'945',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(29,N'o',N'NDP',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(30,N'~',N'Network',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(31,N'!',N'ViewPoint',-1,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(32,N'?',N'Unknown',0,0,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(33,N';',N'IQL',0,-1,12,12,20,12,20,5,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(34,N'q',N'IQ3xcite',0,-1,-1,-1,-1,-1,-1,-1,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(35,N'v',N'IQView',-1,-1,0,0,0,0,0,0,N'----')

INSERT INTO [dbo].[Types](theIndex,Type,Name,IsSupervisor,DoesTextComms,NumSensors,NumDrivers,NumKnobs,NumInputs,NumSwitches,NumZones,deviCeMatch) 
VALUES(36,N'\',N'',0,0,0,0,0,0,0,0,N'')


-- Turn off insertation of explicit identities
SET IDENTITY_INSERT [dbo].[Types] OFF

-- Disable all constraints and triggers
ALTER TABLE [dbo].[Types] CHECK CONSTRAINT all
ALTER TABLE [dbo].[Types] ENABLE TRIGGER all

IF @@ERROR <> 0 GOTO anError

COMMIT TRAN

GOTO FINISH

anError:
IF @@TRANCOUNT > 0
BEGIN
	PRINT N'Error adding data to the [dbo].[Types] table'
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