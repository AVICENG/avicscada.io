USE <96XDBNAME>
GO

/****** Object:  View dbo.CountAllAlarms    Script Date: 10/11/2004 15:18:53 ******/

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

ALTER  VIEW dbo.CountAllAlarms
AS
SELECT DISTINCT 
                      TOP 100 PERCENT AlarmCode, alarmCodeID, theDescription, Priority, siteLabel, connectionString, lan, os, ackedAlarm, theModule, ModuleLabel, 
                      controllerLabel, lanLabel, COUNT(alarmCodeID) AS theCount, pointID, clearToID, ModuleType, CONVERT(BIT, clearAlarmID) AS IsClear, 
                      ModuleNumber,alarmRequiresAction
FROM         dbo.LastAlarmDetailsByTime
GROUP BY AlarmCode, alarmCodeID, theDescription, Priority, siteLabel, connectionString, lan, os, ackedAlarm, theModule, ModuleLabel, controllerLabel, 
                      lanLabel, pointID, clearToID, ModuleType, clearAlarmID, ModuleNumber,alarmRequiresAction
ORDER BY COUNT(alarmCodeID) DESC

GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

/****** Object:  Stored Procedure dbo.usp_insertLogDataXML    Script Date: 10/11/2004 15:18:53 ******/
--
-- usp_insertFloatLogDataXML - A stored procedure to insert a set of logged floating point values into the PointValueFloat table by sending it as XML
--

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS OFF 
GO

ALTER  PROCEDURE [dbo].[usp_insertLogDataXML]
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

DECLARE log_data_cursor CURSOR FOR
	SELECT theXML.PointID, theXML.DataTime, theXML.DataValue
	FROM OpenXML(@iDoc, '/root/P',1) WITH
	(
		PointID			int		'@i',
		DataTime	 	DATETIME	'@t',
		DataValue		float		'@v'
	) theXML


DECLARE @point_id int
DECLARE @data_time DATETIME
DECLARE @data_val float

OPEN log_data_cursor

FETCH NEXT FROM log_data_cursor
INTO @point_id, @data_time, @data_val

WHILE @@FETCH_STATUS = 0
BEGIN

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

/****** Object:  View dbo.CountClearUnactioned    Script Date: 10/11/2004 15:18:53 ******/

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

ALTER  VIEW dbo.CountClearUnactioned
AS
SELECT COUNT(theIndex) AS CountUnactioned FROM LastAlarmDetailsByTime WHERE (IsRestorable = 0) AND (ackedAlarm = 0)
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO


/****** Object:  View dbo.CountCurrentUnactioned    Script Date: 10/11/2004 15:18:53 ******/

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

ALTER  VIEW dbo.CountCurrentUnactioned
AS
SELECT COUNT(theIndex) AS CountUnactioned FROM LastAlarmDetailsByTime WHERE (IsRestorable = 1) AND (ackedAlarm = 0)
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO
