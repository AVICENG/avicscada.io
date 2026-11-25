--
-- database modification to support non-trend TOPS mapped devices into 963
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

-- add new column into Types table to have sub type

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'Types' AND COLUMN_NAME = 'subType') )
ALTER TABLE Types ADD subType nvarchar(1) NOT NULL DEFAULT N''
GO

-- add new column into Outstations table to have sub device type

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'Outstations' AND COLUMN_NAME = 'deviceSubType') )
ALTER TABLE Outstations	ADD deviceSubType nvarchar(1) NOT NULL DEFAULT N''
GO

-- add new column into Outstations table to have latest overview device comms response

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'Outstations' AND COLUMN_NAME = 'overviewDevCommsResponse') )
ALTER TABLE Outstations ADD overviewDevCommsResponse nvarchar(255) NOT NULL DEFAULT N''
GO

-- modify existing un-used type names in Types table to use them for BACnet

UPDATE Types SET
	[Name] = N'TOPS MAPPED BACnet Device',
	DoesTextComms = 1,
	NumSensors = -1,
	NumDrivers=-1,
	NumKnobs = -1,
	NumInputs = -1,
	NumSwitches = -1,
	NumZones = -1,
	DeviCeMatch = N'----'
WHERE Type = 'G' AND [Name] = N'TONIC IQ'
GO

UPDATE Types SET
	[Name] = N'TOPIQ HOST',
	DoesTextComms = 1
WHERE [Type] = N'F' AND [Name] = N'TONIC Host'
GO

-- update subType for TOPS MAPPED IQ

UPDATE Types SET
	subType = N'B'
WHERE [Type] = N'G' AND [Name] = N'TOPS MAPPED BACnet Device'
GO

-- insert new generic TOPS non-Trend device types

--DELETE FROM Types WHERE [Type] = N'G'
--GO

IF NOT EXISTS (SELECT [Name] FROM Types WHERE [Name] = N'TOPS MAPPED BACnet Device')
BEGIN
	INSERT INTO Types
	([Type],[Name],[IsSupervisor],[DoesTextComms],[NumSensors],[NumDrivers],[NumKnobs],[NumInputs],[NumSwitches],[NumZones],[deviCeMatch],[subType])
	VALUES
	(N'G',N'TOPS MAPPED BACnet Device',0,1,-1,-1,-1,-1,-1,-1,N'----',N'B')
END
GO

IF NOT EXISTS (SELECT [Name] FROM Types WHERE [Name] = N'TOPS MAPPED LonWorks')
BEGIN
	INSERT INTO Types
	([Type],[Name],[IsSupervisor],[DoesTextComms],[NumSensors],[NumDrivers],[NumKnobs],[NumInputs],[NumSwitches],[NumZones],[deviCeMatch],[subType])
	VALUES
	(N'G',N'TOPS MAPPED LonWorks',0,1,-1,-1,-1,-1,-1,-1,N'----',N'L')
END
GO

IF NOT EXISTS (SELECT [Name] FROM Types WHERE [Name] = N'TOPS MAPPED OPC Client')
BEGIN
	INSERT INTO Types
	([Type],[Name],[IsSupervisor],[DoesTextComms],[NumSensors],[NumDrivers],[NumKnobs],[NumInputs],[NumSwitches],[NumZones],[deviCeMatch],[subType])
	VALUES
	(N'G',N'TOPS MAPPED OPC Client',0,1,-1,-1,-1,-1,-1,-1,N'----',N'O')
END
GO

IF NOT EXISTS (SELECT [Name] FROM Types WHERE [Name] = N'TOPS MAPPED Novar Logic 1')
BEGIN
	INSERT INTO Types
	([Type],[Name],[IsSupervisor],[DoesTextComms],[NumSensors],[NumDrivers],[NumKnobs],[NumInputs],[NumSwitches],[NumZones],[deviCeMatch],[subType])
	VALUES
	(N'G',N'TOPS MAPPED Novar Logic 1',0,1,-1,-1,-1,-1,-1,-1,N'----',N'N')
END
GO


SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO