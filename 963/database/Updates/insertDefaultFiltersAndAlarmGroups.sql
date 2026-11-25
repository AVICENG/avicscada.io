--
-- insert default alarm groups and alarm filters
-- and assign alarm filters to alarm groups
--

--USE <96XDBNAME>
USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS OFF
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_insertDefaultFiltersAndAlarmGroups]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_insertDefaultFiltersAndAlarmGroups]
GO

/****** Object:  Stored Procedure dbo.usp_insertDefaultFiltersAndAlarmGroups    Script Date: 10/11/2004 15:18:53 ******/



CREATE PROCEDURE dbo.usp_insertDefaultFiltersAndAlarmGroups

AS

BEGIN	
	
	--
	-- variables to store filter names
	--

	DECLARE @963_SENSOR_ALARMS_FILTER VARCHAR(255) -- 1	
	DECLARE @963_DRIVER_ALARMS_FILTER VARCHAR(255) -- 2
	DECLARE @963_DIGITAL_INPUT_ALARMS_FILTER VARCHAR(255) -- 3
	DECLARE @963_CRITICAL_ALARMS_FILTER VARCHAR(255) -- 4
	DECLARE @963_NETWORK_ALARMS_FILTER VARCHAR(255) -- 5
	DECLARE @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER VARCHAR(255) -- 6
	DECLARE @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER VARCHAR(255) -- 7
	DECLARE @963_USER_ADJUSTMENTS_ALARMS_FILTER VARCHAR(255) -- 8
	DECLARE @963_CATCH_ALL_ALARMS_FILTER VARCHAR(255) -- 9
	DECLARE @963_USER_LOGIN_LOGOUT_ALARMS_FILTER VARCHAR(255) -- 10
	DECLARE @963_DATA_LOGGING_OK_ALARMS_FILTER VARCHAR(255) -- 11
	DECLARE @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER VARCHAR(255) -- 12
	DECLARE @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER VARCHAR(255) -- 13
	DECLARE @963_DATA_LOGGING_FAILED_ALARMS_FILTER VARCHAR(255) -- 14
	DECLARE @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER VARCHAR(255) -- 15
	DECLARE @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER VARCHAR(255) -- 16
	DECLARE @963_AUTO_DIALLER_ALARMS_FILTER VARCHAR(255) -- 17
	DECLARE @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER VARCHAR(255) -- 18
	DECLARE @963_STARTUP_SHUTDOWN_ALARMS_FILTER VARCHAR(255) -- 19
	DECLARE @963_INTERNAL_SYSTEM_ALARMS_FILTER VARCHAR(255) -- 20
	DECLARE @963_SECURE_SPECIFIC_ALARMS_FILTER VARCHAR(255) -- 21
	DECLARE @963_ID_ACCESS_SYSTEM_ALARMS_FILTER VARCHAR(255) -- 22
	DECLARE @963_LOOP_FAILED_ALARMS_FILTER VARCHAR(255) -- 23
	DECLARE @963_LOOP_OK_ALARMS_FILTER VARCHAR(255) -- 24

	--
	-- variables to store alarm group names
	--

	DECLARE @963_SECURE_SPECIFIC_ALARMS_GROUP VARCHAR(255) -- 1
	DECLARE @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP VARCHAR(255) -- 2
	DECLARE @963_STRATEGY_SPECIFIC_ALARMS_GROUP VARCHAR(255) -- 3
	DECLARE @963_NETWORK_COMMUNICATION_ALARMS_GROUP VARCHAR(255) -- 4
	DECLARE @963_DEVICE_SPECIFIC_ALARMS_GROUP VARCHAR(255) -- 5
	DECLARE @963_CRITICAL_ALARMS_GROUP VARCHAR(255) -- 6
	DECLARE @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP VARCHAR(255) -- 7
	DECLARE @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP VARCHAR(255) -- 8

	--
	-- filter names (english), can be translated for international languages
	--

	SET @963_SENSOR_ALARMS_FILTER = N'963 - Sensor Alarms' --1
	SET @963_DRIVER_ALARMS_FILTER = N'963 - Driver Alarms' -- 2
	SET @963_DIGITAL_INPUT_ALARMS_FILTER = N'963 - Digital Input Alarms' -- 3
	SET @963_CRITICAL_ALARMS_FILTER = N'963 - Critical Alarms' -- 4
	SET @963_NETWORK_ALARMS_FILTER = N'963 - Network Alarms' -- 5
	SET @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER = N'963 - General controller faults' -- 6
	SET @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER = N'963 - Alarm retransmission failure' -- 7
	SET @963_USER_ADJUSTMENTS_ALARMS_FILTER = N'963 - User adjustments' -- 8
	SET @963_CATCH_ALL_ALARMS_FILTER = N'963 - Catch all' -- 9
	SET @963_USER_LOGIN_LOGOUT_ALARMS_FILTER = N'963 - User login/logout' -- 10
	SET @963_DATA_LOGGING_OK_ALARMS_FILTER = N'963 - Data logging OK' -- 11
	SET @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER = N'963 - Diary download OK' -- 12
	SET @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER = N'963 - Diary download failed' -- 13
	SET @963_DATA_LOGGING_FAILED_ALARMS_FILTER = N'963 - Data logging failed' -- 14
	SET @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER = N'963 - Scheduler action failed' -- 15
	SET @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER = N'963 - Scheduler action completed' -- 16
	SET @963_AUTO_DIALLER_ALARMS_FILTER = N'963 - Autodialler alarms' -- 17
	SET @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER = N'963 - Alarm retransmission OK' -- 18
	SET @963_STARTUP_SHUTDOWN_ALARMS_FILTER = N'963 - Startup/shutdown' -- 19
	SET @963_INTERNAL_SYSTEM_ALARMS_FILTER = N'963 - Internal system alarms' -- 20
	SET @963_SECURE_SPECIFIC_ALARMS_FILTER = N'963 - Secure-specific alarms' -- 21
	SET @963_ID_ACCESS_SYSTEM_ALARMS_FILTER = N'963 - ID Access system alarms' -- 22
	SET @963_LOOP_FAILED_ALARMS_FILTER = N'963 - Loop failed alarms' -- 23
	SET @963_LOOP_OK_ALARMS_FILTER = N'963 - Loop OK' -- 24

	--
	-- alarm group names (english), can be translated for international languages
	--

	SET @963_SECURE_SPECIFIC_ALARMS_GROUP = N'963 - 963 Secure specific' -- 1
	SET @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP = N'963 - User activity (login/logout/adjustments)' -- 2
	SET @963_STRATEGY_SPECIFIC_ALARMS_GROUP = N'963 - Strategy specific' -- 3
	SET @963_NETWORK_COMMUNICATION_ALARMS_GROUP = N'963 - Network communication' -- 4
	SET @963_DEVICE_SPECIFIC_ALARMS_GROUP = N'963 - Device specific' -- 5
	SET @963_CRITICAL_ALARMS_GROUP = N'963 - Critical alarms' -- 6
	SET @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP = N'963 - Scheduled action failed' -- 7
	SET @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP = N'963 - Alarm retransmission failure' -- 8

	--
	-- insert default pre-configured filters
	--

	DECLARE @extendedFilterID int
	DECLARE @filterIndex int

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SENSOR_ALARMS_FILTER )
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'OUTL, LOW, O/K,CHIH,CLOW,HIGH,READ', N'*', N'*', @963_SENSOR_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''READ'') OR (AlarmCode LIKE N''HIGH'') OR (AlarmCode LIKE N''CLOW'') OR (AlarmCode LIKE N''CHIH'') OR (AlarmCode LIKE N'' O/K'') OR (AlarmCode LIKE N'' LOW'') OR (AlarmCode LIKE N''OUTL''))')	

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'OUTL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'OUTL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LOW')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'O/K')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'O/K',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHIH')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHIH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLOW')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HIGH')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HIGH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'READ')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'READ',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SENSOR_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''READ'') OR (AlarmCode LIKE N''HIGH'') OR (AlarmCode LIKE N''CLOW'') OR (AlarmCode LIKE N''CHIH'') OR (AlarmCode LIKE N'' O/K'') OR (AlarmCode LIKE N'' LOW'') OR (AlarmCode LIKE N''OUTL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'OUTL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'OUTL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LOW')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'O/K')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'O/K',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHIH')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHIH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLOW')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HIGH')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HIGH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'READ')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'READ',N'%',N'%',1,1,0)
	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DRIVER_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CDGT,CMNT,SDGT,MINT', N'*', N'*', @963_DRIVER_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''MINT'') OR (AlarmCode LIKE N''SDGT'') OR (AlarmCode LIKE N''CMNT'') OR (AlarmCode LIKE N''CDGT''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDGT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CMNT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CMNT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDGT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MINT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MINT',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DRIVER_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''MINT'') OR (AlarmCode LIKE N''SDGT'') OR (AlarmCode LIKE N''CMNT'') OR (AlarmCode LIKE N''CDGT''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDGT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CMNT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CMNT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDGT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MINT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MINT',N'%',N'%',1,1,0)

	END
		
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIGITAL_INPUT_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DI=0,DI=1,CDI0,CDI1', N'*', N'*', @963_DIGITAL_INPUT_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''CDI1'') OR (AlarmCode LIKE N''CDI0'') OR (AlarmCode LIKE N''DI=1'') OR (AlarmCode LIKE N''DI=0''))')
		
		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=0')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=1')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=1',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI0')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI1')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI1',N'%',N'%',1,1,0)
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIGITAL_INPUT_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CDI1'') OR (AlarmCode LIKE N''CDI0'') OR (AlarmCode LIKE N''DI=1'') OR (AlarmCode LIKE N''DI=0''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=0')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=1')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=1',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI0')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI1')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI1',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_CRITICAL_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SCRI,CCRI', N'*', N'*', @963_CRITICAL_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''CCRI'') OR (AlarmCode LIKE N''SCRI''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SCRI')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SCRI',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CCRI')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CCRI',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_CRITICAL_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CCRI'') OR (AlarmCode LIKE N''SCRI''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SCRI')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SCRI',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CCRI')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CCRI',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_NETWORK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'NKBK,NKCH,NKDA,NKFL,NKHD,NKOK,NKSV,NKUR,DVDD,DVOK', N'*', N'*', @963_NETWORK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DVOK'') OR (AlarmCode LIKE N''DVDD'') OR (AlarmCode LIKE N''NKUR'') OR (AlarmCode LIKE N''NKSV'') OR (AlarmCode LIKE N''NKOK'') OR (AlarmCode LIKE N''NKHD'') OR (AlarmCode LIKE N''NKFL'') OR (AlarmCode LIKE N''NKDA'') OR (AlarmCode LIKE N''NKCH'') OR (AlarmCode LIKE N''NKBK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKCH')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKCH',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKDA')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKDA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKHD')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKHD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKOK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKSV')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKSV',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKUR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVDD')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVDD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_NETWORK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DVOK'') OR (AlarmCode LIKE N''DVDD'') OR (AlarmCode LIKE N''NKUR'') OR (AlarmCode LIKE N''NKSV'') OR (AlarmCode LIKE N''NKOK'') OR (AlarmCode LIKE N''NKHD'') OR (AlarmCode LIKE N''NKFL'') OR (AlarmCode LIKE N''NKDA'') OR (AlarmCode LIKE N''NKCH'') OR (AlarmCode LIKE N''NKBK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKCH')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKCH',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKDA')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKDA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKHD')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKHD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKOK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKSV')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKSV',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKUR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVDD')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVDD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVOK',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CONL,FDRT,FLER,FPIA,FPRM,FRAM,FRTC,FSWR,FTKA,FTKP,HELP,NKBL', N'*', N'*', @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''NKBL'') OR (AlarmCode LIKE N''HELP'') OR (AlarmCode LIKE N''FTKP'') OR (AlarmCode LIKE N''FTKA'') OR (AlarmCode LIKE N''FSWR'') OR (AlarmCode LIKE N''FRTC'') OR (AlarmCode LIKE N''FRAM'') OR (AlarmCode LIKE N''FPRM'') OR (AlarmCode LIKE N''FPIA'') OR (AlarmCode LIKE N''FLER'') OR (AlarmCode LIKE N''FDRT'') OR (AlarmCode LIKE N''CONL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FDRT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FDRT',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FLER')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FLER',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPIA')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPIA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPRM')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPRM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRAM')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRAM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRTC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRTC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FSWR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FSWR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKA')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKP')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HELP')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HELP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''NKBL'') OR (AlarmCode LIKE N''HELP'') OR (AlarmCode LIKE N''FTKP'') OR (AlarmCode LIKE N''FTKA'') OR (AlarmCode LIKE N''FSWR'') OR (AlarmCode LIKE N''FRTC'') OR (AlarmCode LIKE N''FRAM'') OR (AlarmCode LIKE N''FPRM'') OR (AlarmCode LIKE N''FPIA'') OR (AlarmCode LIKE N''FLER'') OR (AlarmCode LIKE N''FDRT'') OR (AlarmCode LIKE N''CONL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FDRT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FDRT',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FLER')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FLER',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPIA')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPIA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPRM')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPRM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRAM')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRAM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRTC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRTC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FSWR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FSWR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKA')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKP')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HELP')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HELP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBL',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'TXFL', N'*', N'*', @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''TXFL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXFL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''TXFL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXFL',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_ADJUSTMENTS_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'ADJF,ADJU', N'*', N'*', @963_USER_ADJUSTMENTS_ALARMS_FILTER, N'*', 0, 1, 1)
		
		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''ADJU'') OR (AlarmCode LIKE N''ADJF''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJU')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJU',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_ADJUSTMENTS_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''ADJU'') OR (AlarmCode LIKE N''ADJF''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJU')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJU',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_CATCH_ALL_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'*', N'*', @963_CATCH_ALL_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'*')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'%')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_CATCH_ALL_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'*')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'%')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_LOGIN_LOGOUT_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'LGOF,LGON', N'*', N'*', @963_USER_LOGIN_LOGOUT_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''LGON'') OR (AlarmCode LIKE N''LGOF''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGOF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGOF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGON')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGON',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_LOGIN_LOGOUT_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''LGON'') OR (AlarmCode LIKE N''LGOF''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGOF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGOF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGON')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGON',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DLOK', N'*', N'*', @963_DATA_LOGGING_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DLOK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLOK',N'%',N'%',1,1,0)
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DLOK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DYOK', N'*', N'*', @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DYOK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DYOK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DYFL', N'*', N'*', @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DYFL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYFL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DYFL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYFL',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DLFL', N'*', N'*', @963_DATA_LOGGING_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DLFL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLFL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DLFL''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLFL',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'Scheduler command failed*', N'*', @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((theDescription LIKE N''Scheduler command failed%''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE N'Scheduler command failed%')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'Scheduler command failed%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((theDescription LIKE N''Scheduler command failed%''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE N'Scheduler command failed%')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'Scheduler command failed%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'Scheduler command completed*', N'*', @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((theDescription LIKE N''Scheduler command completed%''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE N'Scheduler command completed%')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'Scheduler command completed%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((theDescription LIKE N''Scheduler command completed%''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE N'Scheduler command completed%')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'Scheduler command completed%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_AUTO_DIALLER_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'AANR,AONL,BTNR,LINR,MONR,PGNR', N'*', N'*', @963_AUTO_DIALLER_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''PGNR'') OR (AlarmCode LIKE N''MONR'') OR (AlarmCode LIKE N''LINR'') OR (AlarmCode LIKE N''BTNR'') OR (AlarmCode LIKE N''AONL'') OR (AlarmCode LIKE N''AANR''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AANR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AANR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AONL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'BTNR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'BTNR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LINR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LINR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MONR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MONR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'PGNR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'PGNR',N'%',N'%',1,1,0)


	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_AUTO_DIALLER_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''PGNR'') OR (AlarmCode LIKE N''MONR'') OR (AlarmCode LIKE N''LINR'') OR (AlarmCode LIKE N''BTNR'') OR (AlarmCode LIKE N''AONL'') OR (AlarmCode LIKE N''AANR''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AANR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AANR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AONL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'BTNR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'BTNR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LINR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LINR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MONR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MONR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'PGNR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'PGNR',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'TXOK', N'*', N'*', @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''TXOK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''TXOK''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_STARTUP_SHUTDOWN_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SHDN,STUP', N'*', N'*', @963_STARTUP_SHUTDOWN_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''STUP'') OR (AlarmCode LIKE N''SHDN''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SHDN')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SHDN',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'STUP')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'STUP',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_STARTUP_SHUTDOWN_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''STUP'') OR (AlarmCode LIKE N''SHDN''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SHDN')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SHDN',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'STUP')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'STUP',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_INTERNAL_SYSTEM_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SYST', N'*', N'*', @963_INTERNAL_SYSTEM_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''SYST''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SYST')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SYST',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_INTERNAL_SYSTEM_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SYST''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SYST')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SYST',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SECURE_SPECIFIC_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CLKU,CLMK,CHMK,CONF,HMKT,LKUR,LMKT,MKFL,MKOK', N'*', N'*', @963_SECURE_SPECIFIC_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''MKOK'') OR (AlarmCode LIKE N''MKFL'') OR (AlarmCode LIKE N''LMKT'') OR (AlarmCode LIKE N''LKUR'') OR (AlarmCode LIKE N''HMKT'') OR (AlarmCode LIKE N''CONF'') OR (AlarmCode LIKE N''CHMK'') OR (AlarmCode LIKE N''CLMK'') OR (AlarmCode LIKE N''CLKU''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLKU')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLKU',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLMK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHMK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HMKT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LKUR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LMKT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_SECURE_SPECIFIC_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''MKOK'') OR (AlarmCode LIKE N''MKFL'') OR (AlarmCode LIKE N''LMKT'') OR (AlarmCode LIKE N''LKUR'') OR (AlarmCode LIKE N''HMKT'') OR (AlarmCode LIKE N''CONF'') OR (AlarmCode LIKE N''CHMK'') OR (AlarmCode LIKE N''CLMK'') OR (AlarmCode LIKE N''CLKU''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLKU')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLKU',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLMK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHMK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HMKT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LKUR')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LMKT')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKFL')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKOK')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_ID_ACCESS_SYSTEM_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DRAC,DRFC,DRFS,DRHC,DRHS,DROC,DROS,DRSC,DRSF,DRVS', N'*', N'*', @963_ID_ACCESS_SYSTEM_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DRVS'') OR (AlarmCode LIKE N''DRSF'') OR (AlarmCode LIKE N''DRSC'') OR (AlarmCode LIKE N''DROS'') OR (AlarmCode LIKE N''DROC'') OR (AlarmCode LIKE N''DRHS'') OR (AlarmCode LIKE N''DRHC'') OR (AlarmCode LIKE N''DRFS'') OR (AlarmCode LIKE N''DRFC'') OR (AlarmCode LIKE N''DRAC''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRAC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRAC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRVS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRVS',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_ID_ACCESS_SYSTEM_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DRVS'') OR (AlarmCode LIKE N''DRSF'') OR (AlarmCode LIKE N''DRSC'') OR (AlarmCode LIKE N''DROS'') OR (AlarmCode LIKE N''DROC'') OR (AlarmCode LIKE N''DRHS'') OR (AlarmCode LIKE N''DRHC'') OR (AlarmCode LIKE N''DRFS'') OR (AlarmCode LIKE N''DRFC'') OR (AlarmCode LIKE N''DRAC''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRAC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRAC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSC')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSF')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRVS')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRVS',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SDEV', N'*', N'*', @963_LOOP_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''SDEV''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDEV')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDEV',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SDEV''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDEV')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDEV',N'%',N'%',1,1,0)
	END

	IF NOT EXISTS (SELECT Title FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [<96XDBNAME>].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CSDV', N'*', N'*', @963_LOOP_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''CSDV''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CSDV')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CSDV',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [<96XDBNAME>].[dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [<96XDBNAME>].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CSDV''))')

		-- insert into [<96XDBNAME>].[dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CSDV')
		INSERT INTO [<96XDBNAME>].[dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CSDV',N'%',N'%',1,1,0)

	END

	--
	-- insert default pre-configured alarm groups
	--

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_SECURE_SPECIFIC_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_SECURE_SPECIFIC_ALARMS_GROUP, N'', 0, 255, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP, N'', 0, 255, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_STRATEGY_SPECIFIC_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_STRATEGY_SPECIFIC_ALARMS_GROUP, N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_NETWORK_COMMUNICATION_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_NETWORK_COMMUNICATION_ALARMS_GROUP, N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_DEVICE_SPECIFIC_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_DEVICE_SPECIFIC_ALARMS_GROUP, N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_CRITICAL_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_CRITICAL_ALARMS_GROUP, N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP, N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [<96XDBNAME>].[dbo].[AlarmGroup] WHERE title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP, N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	--
	-- inserts into AlarmFilterToAlarmGroup for pre-configured alarm filters and alarm groups
	--

	DECLARE @alarmGroupID int
	-- DECLARE @extendedFilterID int

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_SECURE_SPECIFIC_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SECURE_SPECIFIC_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_USER_ADJUSTMENTS_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_USER_LOGIN_LOGOUT_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_STARTUP_SHUTDOWN_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_STRATEGY_SPECIFIC_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SENSOR_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DRIVER_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DIGITAL_INPUT_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_LOOP_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_LOOP_OK_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_NETWORK_COMMUNICATION_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_NETWORK_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_DEVICE_SPECIFIC_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_AUTO_DIALLER_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_ID_ACCESS_SYSTEM_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_NETWORK_COMMUNICATION_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_NETWORK_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_CRITICAL_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_CRITICAL_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DATA_LOGGING_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [<96XDBNAME>].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--
END
GO

exec [<96XDBNAME>].[dbo].[usp_insertDefaultFiltersAndAlarmGroups]

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO



