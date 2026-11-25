USE <96XDBNAME>
GO

--
-- Added two more columns in PointValue to accomodate new plots data with enumerated datat types
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'PointValue' AND COLUMN_NAME = N'DataValueType') )
BEGIN
	ALTER TABLE [dbo].[PointValue] ADD [DataValueType] [tinyint] NULL  DEFAULT NULL
END
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'PointValue' AND COLUMN_NAME = N'DataValueStatus') )
BEGIN
ALTER TABLE [dbo].[PointValue] ADD [DataValueStatus] [tinyint] NULL  DEFAULT NULL
END

GO

--
-- Creat new table to stroe types, names and data types for the plots data values
--

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PointValueTypeLookup]') AND type in (N'U'))
DROP TABLE [dbo].[PointValueTypeLookup]
GO

CREATE TABLE [dbo].[PointValueTypeLookup](
	[ValueTypeID] [int] IDENTITY(1,1) NOT NULL,
	[ValueType] [tinyint] NOT NULL,
	[ValueDataType] [nvarchar](255) NOT NULL,
	[ValueName] [nvarchar](255) NOT NULL,
 CONSTRAINT [PK_PointValueTypeLookup] PRIMARY KEY CLUSTERED 
(
	[ValueTypeID] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

--
-- Inserts for PointValueTypeLookup
--

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 0)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (0,
           N'Integer',
           N'Log-status')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 1)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (1,
           N'Digital',
           N'Digital-value')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 2)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (2,
           N'Analog',
           N'Analog-value')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 3)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (3,
           N'Integer',
           N'Enum-value')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 4)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (4,
           N'Integer',
           N'Unsigned-value')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 5)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (5,
           N'Integer',
           N'Signed-value')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 6)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (6,
           N'Integer',
           N'Bitstring-value')
GO

-- no data, so no data type
IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 7)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (7,
           N'Integer',
           N'Null')
GO

-- no data, so no data type
IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 8)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (8,
           N'Integer',
           N'Failure')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 9)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (9,
           N'Integer',
           N'Time-change')
GO

IF NOT EXISTS (SELECT TOP 1 * FROM PointValueTypeLookup WHERE ValueType = 10)
INSERT INTO [i96X].[dbo].[PointValueTypeLookup]
           ([ValueType]
           ,[ValueDataType]
           ,[ValueName])
     VALUES           
           (10,
           N'',
           N'Any')
GO