--
-- modified to get OriginallyCurrent field for alarmFilter queries
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


/****** Object:  View dbo.LastAlarmDetailsByTime    Script Date: 10/11/2004 15:18:53 ******/
ALTER  VIEW dbo.LastAlarmDetailsByTime
AS
SELECT     dbo.Alarms.pointID, dbo.Alarms.alarmCodeID, dbo.Lookup.AlarmCode, dbo.Alarms.theDesc AS theDescription, dbo.Alarms.originalAlarmTime, 
                      dbo.Alarms.userText, dbo.Alarms.receivedTime AS TheReceivedTime, dbo.Alarms.ackedAlarm, dbo.Alarms.priorityLevel AS Priority, 
                      dbo.Alarms.clearAlarmID, dbo.Lookup.IsRestorable, dbo.Alarms.theIndex, dbo.Lookup.alarmRequiresAction, dbo.Lookup.clearToID, 
                      dbo.Alarms.ackedUser, dbo.Alarms.ackedTime, Alarms_1.originalAlarmTime AS ClearAlarmTime, 
                      dbo.LabelsFromController.siteConnectionString AS connectionString, dbo.LabelsFromController.NodeAddress AS os, 
                      dbo.LabelsFromController.LanNo AS lan, dbo.LabelsFromController.itemnum AS ModuleNumber, dbo.LabelsFromController.itemtype AS ModuleType, 
                      dbo.LabelsFromController.item AS theModule, dbo.LabelsFromController.theLabel AS ModuleLabel, dbo.LabelsFromController.siteLabel, 
                      dbo.LabelsFromController.lanLabel, dbo.LabelsFromController.osLabel AS controllerLabel, dbo.LabelsFromController.lanID, 
                      dbo.LabelsFromController.siteID, dbo.LabelsFromController.outstationID, dbo.Lookup.IsRestorable AS OriginallyCurrent
FROM         dbo.Alarms INNER JOIN
                      dbo.Lookup ON dbo.Alarms.alarmCodeID = dbo.Lookup.theIndex INNER JOIN
                      dbo.LabelsFromController ON dbo.Alarms.pointID = dbo.LabelsFromController.theIndex LEFT OUTER JOIN
                      dbo.Alarms Alarms_1 ON dbo.Alarms.clearAlarmID = Alarms_1.theIndex



GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


ALTER   VIEW dbo.CountAllAlarms
AS
SELECT DISTINCT 
                      TOP 100 PERCENT AlarmCode, alarmCodeID, theDescription, Priority, siteLabel, connectionString, lan, os, ackedAlarm, theModule, ModuleLabel, 
                      controllerLabel, lanLabel, COUNT(alarmCodeID) AS theCount, pointID, clearToID, ModuleType, CONVERT(BIT, clearAlarmID) AS IsClear, 
                      ModuleNumber,alarmRequiresAction, OriginallyCurrent
FROM         dbo.LastAlarmDetailsByTime
GROUP BY AlarmCode, alarmCodeID, theDescription, Priority, siteLabel, connectionString, lan, os, ackedAlarm, theModule, ModuleLabel, controllerLabel, 
                      lanLabel, pointID, clearToID, ModuleType, clearAlarmID, ModuleNumber,alarmRequiresAction,OriginallyCurrent
ORDER BY COUNT(alarmCodeID) DESC


GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO
