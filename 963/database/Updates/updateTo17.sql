USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO



ALTER    VIEW dbo.CountAllAlarms
AS

--
-- Create counts of the total frequency, number actioned and number cleared for each point / alarm code.
--

SELECT AlarmCode, alarmCodeID, stringResID, genericDescription AS theDescription, Priority, siteLabel, connectionString, lan, os, SUM(ALL numActioned) AS numActioned, theModule, ModuleLabel, controllerLabel,
lanLabel, COUNT(ALL theIndex) AS theCount, pointID, clearToID, ModuleType, SUM(ALL IsClear) AS numCleared, ModuleNumber, alarmRequiresAction, OriginallyCurrent

FROM (

	SELECT LastAlarmDetailsByTime.*, Lookup.theDescription AS genericDescription, Lookup.stringResID, CONVERT(INT, COALESCE(CONVERT(BIT, clearAlarmID), 0)) AS IsClear,
	CONVERT(INT, ackedAlarm) AS numActioned
	FROM LastAlarmDetailsByTime, Lookup
	WHERE LastAlarmDetailsByTime.alarmCodeID = Lookup.theIndex

) AllAlarms

GROUP BY AlarmCode, alarmCodeID, stringResID, genericDescription, Priority, siteLabel, connectionString, lan, os, theModule, ModuleLabel, controllerLabel,
lanLabel, pointID, clearToID, ModuleType, ModuleNumber, alarmRequiresAction, OriginallyCurrent

GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

