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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_insertLogDataXML]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_insertLogDataXML]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_insertLogDataXML]
	@xml VARCHAR(MAX)
AS

DECLARE @iDoc INT -- A handle to the prepared XML document

-- Prepare the XML document in memory
SET NOCOUNT ON
EXECUTE sp_xml_preparedocument @iDoc OUTPUT, @xml

-- 18/02/2005 : We may find a condition where the XML document contains 2 duplicate times for
-- the same point id, this is likely to happen at the summer time -> standard time change. We
-- cannot violate the primary key constraint, so make sure we check whether a value already
-- exists for this point id and time before inserting.

--
-- 07/07/2006
-- DataValue type changed from float to varchar(10)
-- and converted back to float after replacing comma with decimal point
--

DECLARE log_data_cursor CURSOR FOR
SELECT theXML.PointID, theXML.DataTime, theXML.DataValue, theXML.DataValueType, theXML.DataValueStatus
FROM OpenXML(@iDoc, '/root/P',1) WITH
(
	PointID			int		'@i',
	DataTime	 	DATETIME	'@t',
	DataValue		varchar(10)	'@v',
	DataValueType	int	'@y',
	DataValueStatus	int	'@s'
) theXML


DECLARE @point_id int
DECLARE @data_time DATETIME
DECLARE @data_val varchar(10)
DECLARE @data_value float

DECLARE @data_value_type int
DECLARE @data_value_status int


OPEN log_data_cursor

FETCH NEXT FROM log_data_cursor
INTO @point_id, @data_time, @data_val, @data_value_type, @data_value_status

WHILE @@FETCH_STATUS = 0
BEGIN

	-- replace the , with . in @data_val
	SET @data_val = REPLACE(@data_val,N',',N'.')

    -- change the @data_val here to float
	SET @data_value = CAST(@data_val AS float)
	
	-- if data type and status is equal to -1, then set them to NULL
	IF @data_value_type = -1
		SET @data_value_type = NULL
	
	IF @data_value_status = -1
		SET @data_value_status = NULL

	UPDATE PointValue 
	SET 
	DataValue = @data_val,
	DataValueType = @data_value_type,
	DataValueStatus = @data_value_status
	WHERE (PointID = @point_id) AND (DataTime = @data_time)

	IF @@ROWCOUNT = 0
	BEGIN

		-- Nothing already there for this point / time so we are
		-- safe to do an insert.

		INSERT INTO PointValue (PointID, DataTime, DataValue, DataValueType, DataValueStatus)
		VALUES (@point_id, @data_time, @data_val, @data_value_type, @data_value_status)
	END

	FETCH NEXT FROM log_data_cursor
	INTO @point_id, @data_time, @data_val, @data_value_type, @data_value_status
END

CLOSE log_data_cursor
DEALLOCATE log_data_cursor

-- Remove the XML document
EXECUTE sp_xml_removedocument @iDoc

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