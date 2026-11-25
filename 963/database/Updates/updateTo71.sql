--USE i96X
USE <96XDBNAME>
GO

--
-- 17 March 2009
-- Add new column into Types table to store the numbner of points this device type supports to be logged and collected
-- Moscow ID SA5BB6
--
-- Meaning of different values this column will have:
--
-- 1000 means this device supports maximum 1000 points (1000 is the default value)
-- -1 means this device supports unlimited number of points
-- 0 means this device does not support any logging
--

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = N'Types' AND COLUMN_NAME = N'NumPoints') )
BEGIN
	ALTER TABLE [dbo].[Types] ADD [NumPoints] [int] NOT NULL  DEFAULT 1000
END

GO

--
-- Here are the devices which does not support logging, so set the value to 0 for them
-- It is not confirmed yet, so commented at the moment, will enable back when confirmed
-- It has been set to -1 right now, see section below
--

-- Update [dbo].[Types] SET NumPoints = 0 WHERE Type = N'G' AND subType = N'N'
GO

--
-- Here are the devices which does not have any limit to the number of points, so set the value to -1 for them
--

Update [dbo].[Types] SET NumPoints = -1 WHERE Type = N'F' -- TOPIQ HOST
GO 
Update [dbo].[Types] SET NumPoints = -1 WHERE Type = N'G' AND subType = N'B' -- TOPS MAPPED BACnet Device
GO 
Update [dbo].[Types] SET NumPoints = -1 WHERE Type = N'G' AND subType = N'L' -- TOPS MAPPED LonWorks
GO 
Update [dbo].[Types] SET NumPoints = -1 WHERE Type = N'G' AND subType = N'O' -- TOPS MAPPED OPC Client
GO 
Update [dbo].[Types] SET NumPoints = -1 WHERE Type = N'G' AND subType = N'N' -- TOPS MAPPED Novar Logic 1
GO 
Update [dbo].[Types] SET NumPoints = -1 WHERE Type = N'G' AND subType = N'M' -- TOPS MAPPED Modbus
GO 
					  
SET ANSI_NULLS OFF
GO
SET QUOTED_IDENTIFIER OFF
GO
