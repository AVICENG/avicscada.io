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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_createArchiveDatabase]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_createArchiveDatabase]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_createArchiveDatabase]

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

-- create a new database which will hold the archived data

SET @sqlstr = N'CREATE DATABASE [<DBNAME>] ON (NAME = N''<DBNAME>_Data'', FILENAME = N''<DBPATH>\<DBNAME>_data.mdf'', SIZE = 6, FILEGROWTH = 10%) LOG ON (NAME = N''<DBNAME>_Log'', FILENAME = N''<DBPATH>\<DBNAME>_log.ldf'', FILEGROWTH = 10%) COLLATE SQL_Latin1_General_CP1_CI_AS'
PRINT @sqlstr

SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @archivename)
SET @sqlstr = REPLACE(@sqlstr, N'<DBPATH>', @archivedir)

PRINT @sqlstr
EXECUTE @retval =  sp_executesql @sqlstr

IF @retval  <> 0
BEGIN
	PRINT N'Failed to create archived database.'
	GOTO ON_ERROR
END


-- Now create the database
SET @sqlstr = dbo.GetCreateTableCode(N'SiteDetails') 
+
dbo.GetCreateTableCode(N'Lans')
+
dbo.GetCreateTableCode(N'Outstations')
+
dbo.GetCreateTableCode(N'StrategyList')
+
dbo.GetCreateTableCode(N'Types')
+
dbo.GetCreateTableCode(N'PointValue')
+
dbo.GetCreateTableCode(N'SchematicLookup')
+
dbo.GetCreateTableCode(N'SchematicDataRecordingEntry')
+
dbo.GetCreateTableCode(N'SchematicDataRecordingValues')
+
dbo.GetCreateTableCode(N'Alarms')

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

SET @sqlstr = N'INSERT <DBNAME>.dbo.PointValue SELECT * FROM PointValue WHERE (DataTime < ''' + CAST(@endDate AS NVARCHAR) + N''')  AND (DataTime > ''' + CAST(@startDate AS NVARCHAR) + ''')'

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
-- Set the database to read only so that it should not be changed once archived
-- also detach it from sql server
--

-- set database to single user mode
SET @sqlstr = N'ALTER DATABASE ' + @archivename + N' SET SINGLE_USER;'
PRINT @sqlstr
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to set single user property on archived database'
	GOTO ON_ERROR
END

-- set database to read only
--SET @sqlstr = N'ALTER DATABASE ' + @archivename + N' MODIFY FILEGROUP readonlyfilegroup READONLY'
SET @sqlstr = N'ALTER DATABASE ' + @archivename + N' SET READ_ONLY;'
PRINT @sqlstr
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to set read only property on archived database'
	GOTO ON_ERROR
END

-- set database back to multi user mode
SET @sqlstr = N'ALTER DATABASE ' + @archivename + N' SET MULTI_USER;'
PRINT @sqlstr
EXECUTE @retval = sp_executesql @sqlstr

IF @retval <> 0
BEGIN
	PRINT N'Failed to set multiple user property on archived database'
	GOTO ON_ERROR
END

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