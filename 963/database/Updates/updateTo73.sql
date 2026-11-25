--USE i96X
USE <96XDBNAME>
GO

--
-- 05 Oct 2009
-- Moscow ID DH70D6, DH5F52, DH5C6A, DH5A1E
--
-- Device Friendly Names
--
-- Update the names in Types table to make them more human readable
-- These names will be used throughout the 963 for a trend device
-- These names will also be used as a file name, so ensure the characters used in these names are valid for windows filename
--
-- New device types
--
-- Add new device types for IQView variants (IQView4, IQView8)
-- Add new device type for IQeco
-- Add new device types for IQeco project INC devices (BINC, LINC, ZINC)
-- Add new device types for TOPS devices
-- Add new device types for TOPS served INC devices
--

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- Add new device types

--
-- Add new type for IQView4
--
-- Record of discussion with Rory
-- IQView4 is not designed to appear on the network, this is a stand alone device
-- If configued incorrectly it may appear on the network and in this case 963 will display icon in the devices tree
-- based on the information added into database as below
--
-- Name = IQView4
-- Type = v
-- subType = 4
--

IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'v' AND [dbo].[Types].[subType] = N'4')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])
	VALUES (N'v' /*Type*/, N'IQView4' /*Name*/, 1 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	-1 /*NumSensors*/, -1 /*NumDrivers*/, -1 /*NumKnobs*/, -1 /*NumInputs*/, -1 /*NumSwitches*/, -1 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'4' /*subType*/, -1 /*NumPlots*/,	-1 /*NumPoints*/)
GO

-- Add device type for IQView8
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'v' AND [dbo].[Types].[subType] = N'8')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'v' /*Type*/, N'IQView8' /*Name*/, 1 /*IsSupervisor*/, 1 /*DoesTextComms*/, 
	-1 /*NumSensors*/, -1 /*NumDrivers*/, -1 /*NumKnobs*/, -1 /*NumInputs*/, -1 /*NumSwitches*/, -1 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'8' /*subType*/, -1 /*NumPlots*/,	-1 /*NumPoints*/)
GO

-- Add device type for IQeco
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'<' AND [dbo].[Types].[subType] = N'')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'<' /*Type*/, N'IQeco' /*Name*/, 0 /*IsSupervisor*/, 1 /*DoesTextComms*/, 
	-1 /*NumSensors*/, -1 /*NumDrivers*/, -1 /*NumKnobs*/, -1 /*NumInputs*/, -1 /*NumSwitches*/, -1 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'' /*subType*/, -1 /*NumPlots*/,	-1 /*NumPoints*/)
GO

-- Add device type for NiagaraAX
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'G' AND [dbo].[Types].[subType] = N'A')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'G' /*Type*/, N'NiagaraAX' /*Name*/, 0 /*IsSupervisor*/, 1 /*DoesTextComms*/, 
	-1 /*NumSensors*/, -1 /*NumDrivers*/, -1 /*NumKnobs*/, -1 /*NumInputs*/, -1 /*NumSwitches*/, -1 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'A' /*subType*/, -1 /*NumPlots*/,	-1 /*NumPoints*/)
GO

-- Add device type for TOPS-Generic
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'G' AND [dbo].[Types].[subType] = N'G')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'G' /*Type*/, N'TOPS-Generic' /*Name*/, 0 /*IsSupervisor*/, 1 /*DoesTextComms*/, 
	-1 /*NumSensors*/, -1 /*NumDrivers*/, -1 /*NumKnobs*/, -1 /*NumInputs*/, -1 /*NumSwitches*/, -1 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'G' /*subType*/, -1 /*NumPlots*/,	-1 /*NumPoints*/)
GO

-- Add device type for TrendTool
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'T' AND [dbo].[Types].[subType] = N'')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'T' /*Type*/, N'TrendTool' /*Name*/, 0 /*IsSupervisor*/, 1 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for GDP
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'p' AND [dbo].[Types].[subType] = N'')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'p' /*Type*/, N'GDP' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for BINC (MSTP Lan), IQeco
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'M')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'BINC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'm' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for LINC (LON Lan), IQeco
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'L')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'LINC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'l' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for ZINC (Zigbee Lan), IQeco
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'Z')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'ZINC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'Z' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for INC-GDP (INC device hosted in GDP Trend Lan), Generic INC, IQeco
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'T')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'T' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served BACnet INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'B')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'B' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served LonWorks INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'L')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'L' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served OPC INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'O')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'O' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served Modbus INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'M')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'M' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served Generic INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'G')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'G' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served NiagaraAX INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'A')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'A' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Add device type for TOPS served Novar-Logic-One INC
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[Types] WHERE [dbo].[Types].[Type] = N'I' AND [dbo].[Types].[subType] = N'N')
	INSERT INTO [i96X].[dbo].[Types] (
	[Type] ,[Name] ,[IsSupervisor] ,[DoesTextComms] ,[NumSensors] ,[NumDrivers],
	[NumKnobs] ,[NumInputs] ,[NumSwitches] ,[NumZones] ,[deviCeMatch] ,[subType],
	[NumPlots] ,[NumPoints])	
	VALUES (N'I' /*Type*/, N'INC' /*Name*/, 0 /*IsSupervisor*/, 0 /*DoesTextComms*/, 
	0 /*NumSensors*/, 0 /*NumDrivers*/, 0 /*NumKnobs*/, 0 /*NumInputs*/, 0 /*NumSwitches*/, 0 /*NumZones*/,
	N'----' /*deviCeMatch*/, N'N' /*subType*/, 0 /*NumPlots*/,	0 /*NumPoints*/)
GO

-- Update Types table, take out device with \ type as it is not used anymore

DELETE FROM [i96X].[dbo].[Types] WHERE Type = N'\' AND subType = N''
GO

-- Update Types table with user friendly device names for major device types

UPDATE [dbo].[Types] SET [Name] = N'IQ3' WHERE Type = N'q' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQEYE-Collector' WHERE Type = N'x' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ2' WHERE Type = N':' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ150-V2' WHERE Type = N'1' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ150-V3' WHERE Type = N'2' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ151' WHERE Type = N'3' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ131' WHERE Type = N'4' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ111' WHERE Type = N'5' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ100' WHERE Type = N'6' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ9x' WHERE Type = N'7' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQ7x' WHERE Type = N'8' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'FNC' WHERE Type = N'9' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQL' WHERE Type = N';' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'Supervisor' WHERE Type = N'!' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'Autodialler' WHERE Type = N'A' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'CNC' WHERE Type = N'C' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'INC' WHERE Type = N'I' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'MNC' WHERE Type = N'M' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'PNC' WHERE Type = N'P' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'TrendTool' WHERE Type = N'T' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'XNC' WHERE Type = N'X' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'Non-Trend-Supervisor' WHERE Type = N'Z' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'92x' WHERE Type = N'a' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'95x' WHERE Type = N'e' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'940' WHERE Type = N'j' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'943-v1' WHERE Type = N'k' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'943-v1-1' WHERE Type = N'l' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'942' WHERE Type = N'm' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'945' WHERE Type = N'n' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'NDP' WHERE Type = N'o' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'GDP' WHERE Type = N'p' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQeco' WHERE Type = N'<' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'TOPS-Server' WHERE Type = N'F' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'IQView' WHERE Type = N'v' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'OEM-z-comms' WHERE Type = N'D' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'OEM-v-comms' WHERE Type = N'E' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'Network' WHERE Type = N'~' AND subType = N''
GO

UPDATE [dbo].[Types] SET [Name] = N'Unknown' WHERE Type = N'?' AND subType = N''
GO

-- Update Types table with user friendly device names for device types having sub types

UPDATE [dbo].[Types] SET [Name] = N'BACnet' WHERE Type = N'G' AND subType = N'B'  
GO

UPDATE [dbo].[Types] SET [Name] = N'LonWorks' WHERE Type = N'G' AND subType = N'L'
GO

UPDATE [dbo].[Types] SET [Name] = N'OPCClient' WHERE Type = N'G' AND subType = N'O'
GO

UPDATE [dbo].[Types] SET [Name] = N'Novar-Logic-One' WHERE Type = N'G' AND subType = N'N'
GO

UPDATE [dbo].[Types] SET [Name] = N'Modbus' WHERE Type = N'G' AND subType = N'M'
GO

UPDATE [dbo].[Types] SET [Name] = N'NiagaraAX' WHERE Type = N'G' AND subType = N'A'
GO

UPDATE [dbo].[Types] SET [Name] = N'TOPS-Generic' WHERE Type = N'G' AND subType = N'G'
GO

UPDATE [dbo].[Types] SET [Name] = N'IQView4' WHERE Type = N'v' AND subType = N'4'
GO

UPDATE [dbo].[Types] SET [Name] = N'IQView8' WHERE Type = N'v' AND subType = N'8'
GO
					  
SET ANSI_NULLS OFF
GO
SET QUOTED_IDENTIFIER OFF
GO
