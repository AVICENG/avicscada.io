USE <96XDBNAME>
--USE [i96X]
GO

--
-- Add primary key column to all the tables which previously does not have
-- Changed creation of index from NONCLUSTERED to CLUSTERED, as online creation of NONCLUSTERED is not supported on SQL2005
-- Create / Modify [AlarmsForPanelsLink], last script didnt create it because AlarmsToPanelLookupID was not present
--

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS ON 
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'AlarmFilterToAlarmGroupLink' AND COLUMN_NAME = 'AlarmFilterToAlarmGroupLinkID') )
BEGIN
	ALTER TABLE AlarmFilterToAlarmGroupLink ADD AlarmFilterToAlarmGroupLinkID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE AlarmFilterToAlarmGroupLink ADD PRIMARY KEY (AlarmFilterToAlarmGroupLinkID)
END
GO


IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'AlarmGroupToWorkgroupLink' AND COLUMN_NAME = 'AlarmGroupToWorkgroupLinkID') )
BEGIN
	ALTER TABLE AlarmGroupToWorkgroupLink ADD AlarmGroupToWorkgroupLinkID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE AlarmGroupToWorkgroupLink ADD PRIMARY KEY (AlarmGroupToWorkgroupLinkID)
END
GO


IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'AlarmsToPanelLookup' AND COLUMN_NAME = 'AlarmsToPanelLookupID') )
BEGIN
	ALTER TABLE AlarmsToPanelLookup ADD AlarmsToPanelLookupID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE AlarmsToPanelLookup ADD PRIMARY KEY (AlarmsToPanelLookupID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'DatabaseDeletionHistory' AND COLUMN_NAME = 'DatabaseDeletionHistoryID') )
BEGIN
	ALTER TABLE DatabaseDeletionHistory ADD DatabaseDeletionHistoryID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE DatabaseDeletionHistory ADD PRIMARY KEY (DatabaseDeletionHistoryID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'DiaryGroupToDayIdExceptionLink' AND COLUMN_NAME = 'DiaryGroupToDayIdExceptionLinkID') )
BEGIN
	ALTER TABLE DiaryGroupToDayIdExceptionLink ADD DiaryGroupToDayIdExceptionLinkID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE DiaryGroupToDayIdExceptionLink ADD PRIMARY KEY (DiaryGroupToDayIdExceptionLinkID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'DiaryWeekdaySetToDayLink' AND COLUMN_NAME = 'DiaryWeekdaySetToDayLinkID') )
BEGIN
	ALTER TABLE DiaryWeekdaySetToDayLink ADD DiaryWeekdaySetToDayLinkID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE DiaryWeekdaySetToDayLink ADD PRIMARY KEY (DiaryWeekdaySetToDayLinkID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'ModuleToPlotLink' AND COLUMN_NAME = 'ModuleToPlotLinkID') )
BEGIN
	ALTER TABLE ModuleToPlotLink ADD ModuleToPlotLinkID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE ModuleToPlotLink ADD PRIMARY KEY (ModuleToPlotLinkID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'PhoneSettings' AND COLUMN_NAME = 'PhoneSettingsID') )
BEGIN
	ALTER TABLE PhoneSettings ADD PhoneSettingsID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE PhoneSettings ADD PRIMARY KEY (PhoneSettingsID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'PrintTemplates' AND COLUMN_NAME = 'PrintTemplatesID') )
BEGIN
	ALTER TABLE PrintTemplates ADD PrintTemplatesID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE PrintTemplates ADD PRIMARY KEY (PrintTemplatesID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'SchematicDataRecordingValues' AND COLUMN_NAME = 'SchematicDataRecordingValuesID') )
BEGIN
	ALTER TABLE SchematicDataRecordingValues ADD SchematicDataRecordingValuesID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE SchematicDataRecordingValues ADD PRIMARY KEY (SchematicDataRecordingValuesID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'SystemAdministratorProperties' AND COLUMN_NAME = 'SystemAdministratorPropertiesID') )
BEGIN
	ALTER TABLE SystemAdministratorProperties ADD SystemAdministratorPropertiesID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE SystemAdministratorProperties ADD PRIMARY KEY (SystemAdministratorPropertiesID)
END
GO

--IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'TraceDataTmp' AND COLUMN_NAME = 'TraceDataTmpID') )
--BEGIN
--	ALTER TABLE TraceDataTmp ADD TraceDataTmpID [int] IDENTITY(1,1) NOT NULL	
--	
--	ALTER TABLE TraceDataTmp WITH NOCHECK 
--	ADD CONSTRAINT PK_TraceDataTmp PRIMARY KEY CLUSTERED ([TraceDataTmpID] ASC)
--	WITH (FILLFACTOR = 75, ONLINE = ON, PAD_INDEX = ON, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON, STATISTICS_NORECOMPUTE  = OFF)
--	ON [PRIMARY]
--END
--GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'UserPasswords' AND COLUMN_NAME = 'UserPasswordsID') )
BEGIN
	ALTER TABLE UserPasswords ADD UserPasswordsID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE UserPasswords ADD PRIMARY KEY (UserPasswordsID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'WorkgroupsToSchematicsFolderLink' AND COLUMN_NAME = 'WorkgroupsToSchematicsFolderLinkID') )
BEGIN
	ALTER TABLE WorkgroupsToSchematicsFolderLink ADD WorkgroupsToSchematicsFolderLinkID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE WorkgroupsToSchematicsFolderLink ADD PRIMARY KEY (WorkgroupsToSchematicsFolderLinkID)
END
GO

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'WWW' AND COLUMN_NAME = 'WWWID') )
BEGIN
	ALTER TABLE WWW ADD WWWID [int] IDENTITY(1,1) NOT NULL	
	
	ALTER TABLE WWW ADD PRIMARY KEY (WWWID)
END
GO


SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO

--
-- Test code, to drop constraint and column
--
--ALTER TABLE AlarmFilterToAlarmGroupLink DROP CONSTRAINT PK_AlarmFilterToAlarmGroupLink
--GO
--ALTER TABLE AlarmFilterToAlarmGroupLink DROP COLUMN AlarmFilterToAlarmGroupLinkID


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
