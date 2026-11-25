--
-- problem found on german windows, comma and decimal point should behave same
-- solution for the decimal point, now comma and dot can be used as decimal point
-- 123.12 or 123,12 both are valid
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF
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
	SELECT theXML.PointID, theXML.DataTime, theXML.DataValue
	FROM OpenXML(@iDoc, '/root/P',1) WITH
	(
		PointID			int		'@i',
		DataTime	 	DATETIME	'@t',
		DataValue		varchar(10)	'@v'
	) theXML


DECLARE @point_id int
DECLARE @data_time DATETIME
DECLARE @data_val varchar(10)
DECLARE @data_value float

OPEN log_data_cursor

FETCH NEXT FROM log_data_cursor
INTO @point_id, @data_time, @data_val

WHILE @@FETCH_STATUS = 0
BEGIN

	-- replace the , with . in @data_val
	SET @data_val = REPLACE(@data_val,N',',N'.')

        	-- change the @data_val here to float
	SET @data_value = CAST(@data_val AS float)

	UPDATE PointValue SET DataValue = @data_val
	WHERE (PointID = @point_id) AND (DataTime = @data_time)

	IF @@ROWCOUNT = 0
	BEGIN

		-- Nothing already there for this point / time so we are
		-- safe to do an insert.

		INSERT INTO PointValue (PointID, DataTime, DataValue)
		VALUES (@point_id, @data_time, @data_val)
	END

	FETCH NEXT FROM log_data_cursor
	INTO @point_id, @data_time, @data_val
END

CLOSE log_data_cursor
DEALLOCATE log_data_cursor

-- Remove the XML document

EXECUTE sp_xml_removedocument @iDoc

GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO