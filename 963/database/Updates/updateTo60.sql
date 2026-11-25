USE <96XDBNAME>
GO

--
-- modify views to select all fields by name instead of using *
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- modify [PlotsForModuleDetails]

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[PlotsForModuleDetails]'))
DROP VIEW [dbo].[PlotsForModuleDetails]
GO

CREATE VIEW [dbo].[PlotsForModuleDetails]
AS

	SELECT 

	LFC.theIndex, LFC.lanID, LFC.siteID, LFC.LanNo, LFC.outstationID, LFC.NodeAddress, 
	LFC.deviceSubType, LFC.deviCeResponse, LFC.FWVersionMajor, LFC.FWVersionMinor, 
	LFC.siteConnectionString, LFC.item, LFC.itemtype, LFC.itemnum, LFC.theValue, LFC.theStatus, LFC.theLabel, 
	LFC.theUnits, LFC.thePasswordLevel, LFC.theType, LFC.DeviceType, LFC.batchMode, 
	LFC.siteLabel, LFC.lanLabel, LFC.osLabel,

	PFM.ModuleID, PFM.PointID, PFM.TimingType, PFM.SourceModuleValue, 
	PFM.NumberOfRecords, PFM.SourceModuleID, PFM.LastTotalRecordCount, PFM.TimeOfLastRecord, 
	PFM.LoggingInterval, PFM.TimeOfLastDownload,
	PFM.SourceModuleItem

	FROM dbo.LabelsFromController LFC INNER JOIN dbo.PlotsForModule PFM
	ON LFC.theIndex = PFM.PointID

GO

-- modify [AllDetailsForPlots]

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[AllDetailsForPlots]'))
DROP VIEW [dbo].[AllDetailsForPlots]
GO

CREATE VIEW [dbo].[AllDetailsForPlots]
AS

	SELECT

	LFC.theIndex, LFC.lanID, LFC.siteID, LFC.LanNo, LFC.outstationID, LFC.NodeAddress, 
	LFC.deviceSubType, LFC.deviCeResponse, LFC.FWVersionMajor, LFC.FWVersionMinor, 
	LFC.siteConnectionString, LFC.item, LFC.itemtype, LFC.itemnum, LFC.theValue, LFC.theStatus, LFC.theLabel, 
	LFC.theUnits, LFC.thePasswordLevel, LFC.theType, LFC.DeviceType, LFC.batchMode, 
	LFC.siteLabel, LFC.lanLabel, LFC.osLabel,

	PD.PlotID,PD.PointID, PD.TimingType, PD.SourceModuleValue, PD.SourceModuleID, PD.NumberOfRecords, PD.LastTotalRecordCount, PD.TimeOfLastRecord,
	PD.LoggingInterval, PD.TimeOfLastDownload

	FROM LabelsFromController LFC INNER JOIN PlotDetails PD
	ON LFC.theIndex = PD.PointID

GO


-- modify [AlarmsForPanelsLink]

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[AlarmsForPanelsLink]'))
DROP VIEW [dbo].[AlarmsForPanelsLink]
GO

CREATE  VIEW [dbo].[AlarmsForPanelsLink]
AS

	SELECT

	LADBT.pointID, LADBT.alarmCodeID, LADBT.AlarmCode, LADBT.theDescription, LADBT.originalAlarmTime, 
	LADBT.userText, LADBT.TheReceivedTime, LADBT.ackedAlarm, LADBT.Priority, 
	LADBT.clearAlarmID, LADBT.IsRestorable, LADBT.theIndex, LADBT.alarmRequiresAction, LADBT.clearToID, 
	LADBT.ackedUser, LADBT.ackedTime, LADBT.ClearAlarmTime, 
	LADBT.connectionString, LADBT.os, 
	LADBT.lan, LADBT.ModuleNumber, LADBT.ModuleType, 
	LADBT.theModule, LADBT.ModuleLabel, LADBT.siteLabel, 
	LADBT.lanLabel, LADBT.controllerLabel, LADBT.lanID, 
	LADBT.siteID, LADBT.outstationID, LADBT.OriginallyCurrent,

	ATPL.AlarmGroupIndex, ATPL.AlarmIndex, ATPL.AlarmsToPanelLookupID

	FROM dbo.LastAlarmDetailsByTime LADBT INNER JOIN dbo.AlarmsToPanelLookup ATPL
	ON LADBT.theIndex = ATPL.AlarmIndex


GO

SET QUOTED_IDENTIFIER OFF
GO




