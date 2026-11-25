USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

--
-- make type column of Types table case sensitive
-- to resolve the issue of X (XNC) and x (IQEYE)
-- will help also in future - for similar type os issues
--

--
-- Temp Test
--
	-- select * from Types where [Type] = N'x'
	-- select * from Types where [Type] = N'X'

	-- EXEC sp_help 'Types'
	-- Column Name = Type
	-- Collation = SQL_Latin1_General_CP1_CI_AS
	-- Column Name = subType
	-- Collation = SQL_Latin1_General_CP1_CI_AS

ALTER TABLE Types
    ALTER COLUMN [Type] nvarchar(1) 
    COLLATE Latin1_General_CS_AS 
GO 

ALTER TABLE Types
    ALTER COLUMN [subType] nvarchar(1) 
    COLLATE Latin1_General_CS_AS 
GO 

--
-- adds new device type into types table for IQ EYE
--

If Not Exists (Select 1 from [Types] where [Type] = N'x' AND [deviCeMatch] = N'IQ_EYE*')
INSERT INTO [Types]
           ([Type]
           ,[Name]
           ,[IsSupervisor]
           ,[DoesTextComms]
           ,[NumSensors]
           ,[NumDrivers]
           ,[NumKnobs]
           ,[NumInputs]
           ,[NumSwitches]
           ,[NumZones]
           ,[deviCeMatch])
     VALUES
           (
			N'x'
           ,N'IQ EYE Data Collector'
           ,0
           ,1
           ,0
           ,0
           ,0
           ,0
           ,0
           ,0
           ,N'IQ_EYE*'
	   )
GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO


