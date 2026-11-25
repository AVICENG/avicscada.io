--
-- one more new device type for modbus
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

IF NOT EXISTS (SELECT [Name] FROM Types WHERE [Name] = N'TOPS MAPPED Modbus')
BEGIN
	INSERT INTO Types
	([Type],[Name],[IsSupervisor],[DoesTextComms],[NumSensors],[NumDrivers],[NumKnobs],[NumInputs],[NumSwitches],[NumZones],[deviCeMatch],[subType])
	VALUES
	(N'G',N'TOPS MAPPED Modbus',0,1,-1,-1,-1,-1,-1,-1,N'----',N'M')
END
GO


SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO