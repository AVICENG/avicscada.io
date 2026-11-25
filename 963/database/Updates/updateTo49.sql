--USE i96X
USE <96XDBNAME>
GO

--
-- Add new column for number of plots for each device - older devices e.g. IQ1, IQ2, IQL etc
-- Inserts for new column for each device
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Types' AND COLUMN_NAME = N'NumPlots') )
BEGIN
	ALTER TABLE [dbo].[Types] ADD [NumPlots] [smallint] NOT NULL  DEFAULT 0
END
GO

-- update newly created column with appropriate values, got from trend documentation

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 96
WHERE [Type] = N':' AND [Name] = N'IQ251'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 40 -- 32-40
WHERE [Type] = N'3' AND [Name] = N'IQ151'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 32 -- 20-32
WHERE [Type] = N'4' AND [Name] = N'IQ131'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 20 -- 16-20
WHERE [Type] = N'5' AND [Name] = N'IQ111'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 20 -- 16-20
WHERE [Type] = N'6' AND [Name] = N'IQ100'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 16 -- 8-16
WHERE [Type] = N'7' AND [Name] = N'IQ9x'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 6
WHERE [Type] = N'8' AND [Name] = N'IQ7x'
  
GO

UPDATE [i96X].[dbo].[Types]
SET [NumPlots] = 1
WHERE [Type] = N';' AND [Name] = N'IQL'
  
GO


