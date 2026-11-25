USE <96XDBNAME>
--USE [i96X]
GO

--
-- Modified Types and PointValue tables to incorporate new changes made in 963 v3.10 db
-- Added code to detach media if archive not successful, otherwise it will not be possible to delete the created archive files
--

/****** Object:  StoredProcedure [dbo].[usp_createArchiveDatabase]    Script Date: 07/01/2008 16:04:14 ******/
SET ANSI_NULLS OFF
GO

SET QUOTED_IDENTIFIER ON
GO


--
-- usp_createArchiveDatabase - A stored procedure to ALTER  a removable archive database and copy the
-- data between two date ranges into it.
--

ALTER PROCEDURE [dbo].[usp_createArchiveDatabase]

@startDate DATETIME, -- The start date of data to archive
@endDate DATETIME,-- The end date of the data to archive
@archivename NVARCHAR(123), -- The name of the archive database, also used as the basis for the file names
@archivedir NVARCHAR(4000), -- The directory path where the database files will be created.
@deleteOldData BIT, -- A flag used to indicate whether we want to delete the old data in the database
@dataArchivedFAIL BIT OUTPUT -- A flag used to indicate whether the data has been archived OK

AS

-- Remove any white spaces
SET @archivename = REPLACE(@archivename, N' ', N'')

SET @dataArchivedFAIL = 0

DECLARE @sqlstr nvarchar(4000) -- Temporary string used for holding dynamic SQL statements

DECLARE @retval INT -- An int used to hold return values from system stored procedures...
SET @retval = 0

-- Create a removable db. This uses 1 file for system tables, 1 file for the transaction log and 1 file
-- for the read only data tables.

SET @sqlstr = N'EXECUTE sp_create_removable ''<DBNAME>'',
	''<DBNAME>_sys'', ''<DBPATH>\<DBNAME>_sys.mdf'', 5,
	''<DBNAME>_log'', ''<DBPATH>\<DBNAME>_log.ldf'', 5,
	''<DBNAME>_data'', ''<DBPATH>\<DBNAME>_data.ndf'', 5'

SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
SET @sqlstr = REPLACE(@sqlstr, N'<DBPATH>', @archivedir)

PRINT @sqlstr
EXECUTE @retval =  sp_executesql @sqlstr

IF @retval  <> 0
BEGIN
	PRINT N'Failed to create removable database.'
	GOTO ON_ERROR
END


-- Now create the database

SET @sqlstr = N'
CREATE TABLE <DBNAME>.[dbo].[SiteDetails] (
	[siteID] [int] NOT NULL ,
	[siteLabel] [nvarchar] (255) NOT NULL ,
	[siteConnectionString] [nvarchar] (255)  NOT NULL ,
	[siteRemoteLAN] [int] NOT NULL 
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[Lans] (
	[lanID] [int]  NOT NULL ,
	[siteID] [int] NOT NULL ,
	[LanNo] [smallint] NOT NULL ,
	[DeviceType] [nvarchar] (1) NOT NULL ,
	[theLabel] [nvarchar] (50) NOT NULL,
	[deviceSubType] [nvarchar] (1) NOT NULL 
) ON [PRIMARY]'

+
N'
CREATE TABLE <DBNAME>.[dbo].[Outstations] (
	[outstationID] [int] NOT NULL ,
	[lanID] [int] NOT NULL ,
	[NodeAddress] [smallint] NOT NULL ,
	[FWVersionMajor] [smallint] NOT NULL ,
	[FWVersionMinor] [smallint] NOT NULL ,
	[DeviceType] [nvarchar] (1) NOT NULL ,
	[theLabel] [nvarchar] (50) NOT NULL ,
	[outPin] [smallint] NOT NULL ,
	[deviCeResponse] [nvarchar] (255) NOT NULL ,
	[nodeIpAddr] [nvarchar] (255) NOT NULL,
	[batchMode] [bit] NOT NULL,
	[deviceSubType] [nvarchar] (1) NOT NULL,
	[overviewDevCommsResponse] [nvarchar] (255) NOT NULL
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[StrategyList] (
	[theIndex] [int] NOT NULL ,
	[outstationID] [int] NOT NULL ,
	[item] [nvarchar] (255) NOT NULL ,
	[theValue] [nvarchar] (255) NOT NULL ,
	[theStatus] [nvarchar] (255) NOT NULL ,
	[theLabel] [nvarchar] (255) NOT NULL ,
	[theUnits] [nvarchar] (255) NOT NULL ,
	[thePasswordLevel] [smallint] NOT NULL ,
	[theType] [smallint] NOT NULL 
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[Types] (
	[theIndex] [int] NOT NULL ,
	[Type] [nvarchar] (1) NOT NULL ,
	[Name] [nvarchar] (50) NOT NULL ,
	[IsSupervisor] [bit] NOT NULL ,
	[DoesTextComms] [bit] NOT NULL ,
	[NumSensors] [smallint] NOT NULL ,
	[NumDrivers] [smallint] NOT NULL ,
	[NumKnobs] [smallint] NOT NULL ,
	[NumInputs] [smallint] NOT NULL ,
	[NumSwitches] [smallint] NOT NULL ,
	[NumZones] [smallint] NOT NULL ,
	[deviCeMatch] [nvarchar] (255) NOT NULL,
	[deviceSubType] [nvarchar] (1) NOT NULL,
	[NumPlots] [smallint] NOT NULL
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[PointValue] (
	[PointID] [int] NOT NULL ,
	[DataTime] [datetime] NOT NULL ,
	[DataValue] [float] NOT NULL ,
	[DataValueType] [tinyint] NULL,
	[DataValueStatus] [tinyint] NULL
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[SchematicLookup] (
	[theIndex] [int] NOT NULL ,
	[fileName] [nvarchar] (4000) NOT NULL 
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[SchematicDataRecordingEntry] (
	[theIndex] [int] NOT NULL ,
	[schemLookupID] [int] NOT NULL,
	[dataTime] [dateTime] NOT NULL 
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[SchematicDataRecordingValues] (
	[schemEntryID] [int] NOT NULL ,
	[pointID] [int] NOT NULL ,
	[dataValue] [nvarchar] (255) NOT NULL ,
	[dataState] [int] NOT NULL 
) ON [PRIMARY]'
+
N'
CREATE TABLE <DBNAME>.[dbo].[Alarms] (
	[theIndex] [int] NOT NULL ,
	[pointID] [int] NULL ,
	[alarmCodeID] [int] NOT NULL ,
	[theDesc] [nvarchar] (255) NULL ,
	[userText] [nvarchar] (2000) NULL ,
	[originalAlarmTime] [datetime] NOT NULL ,
	[receivedTime] [datetime] NOT NULL ,
	[ackedAlarm] [bit] NOT NULL ,
	[ackedUser] [nvarchar] (255) NOT NULL ,
	[ackedTime] [datetime] NULL ,
	[priorityLevel] [int] NULL ,
	[clearAlarmID] [int] NULL 
) ON [PRIMARY]'


SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)

PRINT @sqlstr
EXECUTE @retval =  sp_executesql @sqlstr

IF @retval  <> 0
BEGIN
	PRINT N'Failed to create removable database.'
	GOTO ON_ERROR
END

-- Now the database has been created attempt to copy the specified information into with the appropriate dates

BEGIN TRANSACTION

--
-- Copy the data from the existing tables
--

-- Copy the Types table over

SET @sqlstr = N'INSERT <DBNAME>.dbo.Types SELECT * FROM Types'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert types data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the SiteDetails table over

SET @sqlstr = N'INSERT <DBNAME>.dbo.SiteDetails SELECT * FROM SiteDetails'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert site data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the Lans table over

SET @sqlstr = N'INSERT <DBNAME>.dbo.Lans SELECT * FROM Lans'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert lan data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the Outstations table over

SET @sqlstr = N'INSERT <DBNAME>.dbo.Outstations SELECT * FROM Outstations'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert outstation data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the StrategyList table over

SET @sqlstr = N'INSERT <DBNAME>.dbo.StrategyList SELECT * FROM StrategyList'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert strategylist data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the logged data into the new point value table

SET @sqlstr = N'INSERT INTO <DBNAME>.dbo.PointValue(PointID, DataTime, DataValue)
SELECT PointID, DataTime, DataValue
FROM PointValue
WHERE (DataTime < ''' + CAST(@endDate AS NVARCHAR) + N''')  AND (DataTime > ''' + CAST(@startDate AS NVARCHAR) + ''')'

SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
PRINT @sqlstr
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert point logged data.'
	ROLLBACK
	GOTO ON_ERROR
END

PRINT N'Copying schematic information over!'

-- Copy the Schematic logged information over

SET @sqlstr = N'INSERT <DBNAME>.dbo.SchematicLookup SELECT * FROM SchematicLookup'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert schematic data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the SchematicDataRecordingEntry information over

SET @sqlstr = N'INSERT <DBNAME>.dbo.SchematicDataRecordingEntry
SELECT * FROM SchematicDataRecordingEntry
WHERE (dataTime < ''' + CAST(@endDate AS NVARCHAR) + N''')  AND (dataTime > ''' + CAST(@startDate AS NVARCHAR) + ''')'

SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert SchematicDataRecordingEntry data'
	ROLLBACK
	GOTO ON_ERROR
END

-- Copy the SchematicDataRecordingValues information over

SET @sqlstr = N'INSERT <DBNAME>.dbo.SchematicDataRecordingValues SELECT * FROM SchematicDataRecordingValues'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert SchematicDataRecordingValues data'
	ROLLBACK
	GOTO ON_ERROR
END

PRINT N'Copying alarm information over'

-- Copy the Alarms information over

SET @sqlstr = N'INSERT <DBNAME>.dbo.Alarms
SELECT * FROM Alarms
WHERE (receivedTime < ''' + CAST(@endDate AS NVARCHAR) + N''')  AND (receivedTime > ''' + CAST(@startDate AS NVARCHAR) + ''')'
SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to insert alarms data'
	ROLLBACK
	GOTO ON_ERROR
END

COMMIT TRANSACTION

--
-- Certify and detach the database
--

-- Modify the filegroup to be read only (the once the data has been archived, it should not be changed)

SET @sqlstr = N'ALTER DATABASE ' + @archivename + N' MODIFY FILEGROUP readonlyfilegroup READONLY'
PRINT @sqlstr
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to set read only property on file group'
	GOTO ON_ERROR
END

PRINT N'About to certify the database'

-- Certify the database is removable
EXECUTE sp_certify_removable @archivename, 'auto'

PRINT N'About to detach the database'

-- Detach the database from SQL Server
EXECUTE sp_detach_db @archivename

-- Delete the old data out of the main database if we need too
IF @deleteOldData <> 0
BEGIN
	PRINT N'Deleting old data from database'
	DELETE FROM PointValue WHERE DataTime BETWEEN @startDate AND @endDate
	DELETE FROM Alarms WHERE receivedTime BETWEEN @startDate AND @endDate
	DELETE FROM SchematicDataRecordingEntry WHERE dataTime BETWEEN @startDate AND @endDate
END

PRINT N'Finished processing archive'

-- Return OK
RETURN 0

ON_ERROR:
	-- This is a generic error handler, rollback the transaction so we do not lose any data...
	PRINT N'An error occurred, rolling back the transaction...'

	ROLLBACK

	-- Set OK flag to false
	SET @dataArchivedFAIL = 1
	
	-- Detach the database from SQL Server
	EXECUTE sp_detach_db @archivename

	-- Return error code
	RETURN 1


GO


