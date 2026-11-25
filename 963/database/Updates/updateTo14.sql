--
-- added output parameter to get count of deleted alarms
--

USE <96XDBNAME>
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_deleteHistoricData]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_deleteHistoricData]
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF 
GO

CREATE  PROCEDURE [dbo].[usp_deleteHistoricData]

@start DATETIME,
@end DATETIME,
@purge_unacked BIT,
@purge_current BIT,
@delAlarmsOnly int OUTPUT

AS

-- The alarms table has a self-referencing foreign key between occurred and clear alarms, so we need to delete in two steps
-- first occurred and then cleared.
-- Problems are caused when we specify to purge alarms that are acked. If the clear alarm is acked, but the occurred alarm
-- is not, a foreign key violation will occur as we are trying to delete the clear alarm, but the corresponding occurred
-- alarm was not deleted in the first step. When we delete the clear alarms we will need to test whether any occurred alarms
-- exist that may reference this alarm.


DECLARE @occ INT
DECLARE @clr INT
DECLARE @log INT

IF (@purge_unacked = 1)
BEGIN

	IF (@purge_current = 0)
	BEGIN

		-- DELETE only non-current (where acked and unacked)

		DELETE FROM Alarms -- Occ
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID <> theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID = theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end) 
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))

		SET @clr = @@ROWCOUNT
	END
	ELSE
	BEGIN

		-- DELETE clear and current (where acked and unacked)

		DELETE FROM Alarms -- Occ
		WHERE	((clearAlarmID IS NULL) OR (clearAlarmID <> theIndex))
			AND (originalAlarmTime BETWEEN @start AND @end)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(originalAlarmTime BETWEEN @start AND @end)
			AND (clearAlarmID = theIndex)
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))

		SET @clr = @@ROWCOUNT
	END
END
ELSE -- IF @purge_unacked = 0
BEGIN

	IF (@purge_current = 0)
	BEGIN

		-- DELETE only non-current where acked

		DELETE FROM Alarms -- Occ
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID <> theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end)
			AND (ackedAlarm = 1)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(clearAlarmID IS NOT NULL)
			AND (clearAlarmID = theIndex)
			AND (originalAlarmTime BETWEEN @start AND @end) 
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))
			AND (ackedAlarm = 1)

		SET @clr = @@ROWCOUNT
	END
	ELSE
	BEGIN

		-- DELETE current and clear where acked

		DELETE FROM Alarms -- Occ
		WHERE	((clearAlarmID IS NULL) OR (clearAlarmID <> theIndex))
			AND (originalAlarmTime BETWEEN @start AND @end)
			AND (ackedAlarm = 1)

		SET @occ = @@ROWCOUNT

		DELETE FROM Alarms -- Clear
		WHERE	(originalAlarmTime BETWEEN @start AND @end)
			AND (clearAlarmID = theIndex)
			AND (theIndex NOT IN (SELECT clearAlarmID FROM Alarms WHERE clearAlarmID <> theIndex))
			AND (ackedAlarm = 1)

		SET @clr = @@ROWCOUNT
	END
END



-- Now DELETE the recorded data logs between the two dates
SET @log = 0
IF (@delAlarmsOnly = 0)
BEGIN
	DELETE FROM PointValue WHERE DataTime BETWEEN @start AND @end
	
	SET @log = @@ROWCOUNT

END

INSERT INTO DatabaseDeletionHistory([NumClear], [NumOcc], [NumRecorded], [StartDate], [EndDate]) VALUES (@clr, @occ, @log, @start, @end)

SET @delAlarmsOnly = (@clr + @occ)
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO