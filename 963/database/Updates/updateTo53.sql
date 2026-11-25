USE <96XDBNAME>
--USE [i96X]
GO

-- Added data type and status information to store against logged data for BACnet devices

/****** Object:  StoredProcedure [dbo].[usp_insertLogDataXML]    Script Date: 07/04/2008 15:24:23 ******/
SET ANSI_NULLS OFF
GO

SET QUOTED_IDENTIFIER ON
GO


ALTER   PROCEDURE [dbo].[usp_insertLogDataXML]
	@xml TEXT
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


