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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_insertDefaultFiltersAndAlarmGroups]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_insertDefaultFiltersAndAlarmGroups]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_insertDefaultFiltersAndAlarmGroups]

@alarmFiltersXml NVARCHAR(MAX), -- names of all default alarm filters in xml format
@alarmGroupsXml NVARCHAR(MAX), -- name of all default alarm groups in xml format
@alarmMiscellaneousXml NVARCHAR(MAX), -- all miscelleneous fields related to alarm filters and alarm groups
@defaultWorkgroup NVARCHAR(255), -- name of workgroup which needs to be notified
@success BIT OUTPUT -- A flag used to indicate whether the procedure executed successfully or failed

AS

BEGIN	
	
	--
	-- variables to store filter names
	--

	DECLARE @963_SENSOR_ALARMS_FILTER NVARCHAR(255) -- 1	
	DECLARE @963_DRIVER_ALARMS_FILTER NVARCHAR(255) -- 2
	DECLARE @963_DIGITAL_INPUT_ALARMS_FILTER NVARCHAR(255) -- 3
	DECLARE @963_CRITICAL_ALARMS_FILTER NVARCHAR(255) -- 4
	DECLARE @963_NETWORK_ALARMS_FILTER NVARCHAR(255) -- 5
	DECLARE @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER NVARCHAR(255) -- 6
	DECLARE @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER NVARCHAR(255) -- 7
	DECLARE @963_USER_ADJUSTMENTS_ALARMS_FILTER NVARCHAR(255) -- 8
	DECLARE @963_CATCH_ALL_ALARMS_FILTER NVARCHAR(255) -- 9
	DECLARE @963_USER_LOGIN_LOGOUT_ALARMS_FILTER NVARCHAR(255) -- 10
	DECLARE @963_DATA_LOGGING_OK_ALARMS_FILTER NVARCHAR(255) -- 11
	DECLARE @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER NVARCHAR(255) -- 12
	DECLARE @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER NVARCHAR(255) -- 13
	DECLARE @963_DATA_LOGGING_FAILED_ALARMS_FILTER NVARCHAR(255) -- 14
	DECLARE @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER NVARCHAR(255) -- 15
	DECLARE @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER NVARCHAR(255) -- 16
	DECLARE @963_AUTO_DIALLER_ALARMS_FILTER NVARCHAR(255) -- 17
	DECLARE @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER NVARCHAR(255) -- 18
	DECLARE @963_STARTUP_SHUTDOWN_ALARMS_FILTER NVARCHAR(255) -- 19
	DECLARE @963_INTERNAL_SYSTEM_ALARMS_FILTER NVARCHAR(255) -- 20
	DECLARE @963_SECURE_SPECIFIC_ALARMS_FILTER NVARCHAR(255) -- 21
	DECLARE @963_ID_ACCESS_SYSTEM_ALARMS_FILTER NVARCHAR(255) -- 22
	DECLARE @963_LOOP_FAILED_ALARMS_FILTER NVARCHAR(255) -- 23
	DECLARE @963_LOOP_OK_ALARMS_FILTER NVARCHAR(255) -- 24
	DECLARE @963_SERVICE_PIN_ALARMS_FILTER NVARCHAR(255) -- 25

	--
	-- variables to store alarm group names
	--

	DECLARE @963_SECURE_SPECIFIC_ALARMS_GROUP NVARCHAR(255) -- 1
	DECLARE @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP NVARCHAR(255) -- 2
	DECLARE @963_STRATEGY_SPECIFIC_ALARMS_GROUP NVARCHAR(255) -- 3
	DECLARE @963_NETWORK_COMMUNICATION_ALARMS_GROUP NVARCHAR(255) -- 4
	DECLARE @963_DEVICE_SPECIFIC_ALARMS_GROUP NVARCHAR(255) -- 5
	DECLARE @963_CRITICAL_ALARMS_GROUP NVARCHAR(255) -- 6
	DECLARE @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP NVARCHAR(255) -- 7
	DECLARE @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP NVARCHAR(255) -- 8
	DECLARE @963_SERVICE_PIN_ALARMS_GROUP NVARCHAR(255) -- 9

	--
	-- variables to store miscelleneous alarm fields
	--

	DECLARE @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText NVARCHAR(255) --1
	DECLARE @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText NVARCHAR(255) --2
	DECLARE @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText NVARCHAR(255) --3
	DECLARE @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText NVARCHAR(255) --4
	DECLARE @963_MISC_PARAM_SITE NVARCHAR(255) --5
	DECLARE @963_MISC_PARAM_LAN NVARCHAR(255) --6
	DECLARE @963_MISC_PARAM_OS NVARCHAR(255) --7
	DECLARE @963_MISC_PARAM_ALARM_SPIN NVARCHAR(255) --8
	DECLARE @963_MISC_PARAM_SPIN_RECEIVED_MESSAGE NVARCHAR(255) --9
	DECLARE @963_MISC_PARAM_DEVICE_SERIAL_NUMBER NVARCHAR(255) --10


	-- handle to alarm groups and alarm filters xml document
	DECLARE @hXmlDocGroups INT
	DECLARE @hXmlDocFilters INT
	DECLARE @hXmlDocMiscelleneous INT

	DECLARE @retValue INT

	BEGIN TRAN DefaultAlarmConfiguration_TRAN

	SET @success = 0 -- return 0 if everything is ok
	
	SET NOCOUNT ON

	EXECUTE sp_xml_preparedocument @hXmlDocFilters OUTPUT, @alarmFiltersXml -- get document handle to be passed to OPENXML
	IF (@retValue <> 0)
	BEGIN
		PRINT N'sp_xml_preparedocument failed for alarm filter names'
		GOTO ON_ERROR
	END

	EXECUTE @retValue = sp_xml_preparedocument @hXmlDocGroups OUTPUT, @alarmGroupsXml -- get document handle to be passed to OPENXML
	IF (@retValue <> 0)
	BEGIN
		PRINT N'sp_xml_preparedocument failed for alarm group names'
		GOTO ON_ERROR
	END

	EXECUTE @retValue = sp_xml_preparedocument @hXmlDocMiscelleneous OUTPUT, @alarmMiscellaneousXml -- get document handle to be passed to OPENXML
	IF (@retValue <> 0)
	BEGIN
		PRINT N'sp_xml_preparedocument failed for alarm miscelleneous field names'
		GOTO ON_ERROR
	END

	-- cursor to get default alarm filter names from xml document passed as paramter
	DECLARE alarm_filters_cursor CURSOR FOR
	SELECT	
	alarmFiltersXml.SENSOR_ALARMS_FILTER,
	alarmFiltersXml.DRIVER_ALARMS_FILTER,
	alarmFiltersXml.DIGITAL_INPUT_ALARMS_FILTER,
	alarmFiltersXml.CRITICAL_ALARMS_FILTER,
	alarmFiltersXml.NETWORK_ALARMS_FILTER,
	alarmFiltersXml.GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER,
	alarmFiltersXml.ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER,
	alarmFiltersXml.USER_ADJUSTMENTS_ALARMS_FILTER,
	alarmFiltersXml.CATCH_ALL_ALARMS_FILTER,
	alarmFiltersXml.USER_LOGIN_LOGOUT_ALARMS_FILTER,
	alarmFiltersXml.DATA_LOGGING_OK_ALARMS_FILTER,
	alarmFiltersXml.DIARY_DOWNLOAD_OK_ALARMS_FILTER,
	alarmFiltersXml.DIARY_DOWNLOAD_FAILED_ALARMS_FILTER,
	alarmFiltersXml.DATA_LOGGING_FAILED_ALARMS_FILTER,
	alarmFiltersXml.SCHEDULER_ACTION_FAILED_ALARMS_FILTER,
	alarmFiltersXml.SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER,
	alarmFiltersXml.AUTO_DIALLER_ALARMS_FILTER,
	alarmFiltersXml.ALARM_RETRANSMISSION_OK_ALARMS_FILTER,
	alarmFiltersXml.STARTUP_SHUTDOWN_ALARMS_FILTER,
	alarmFiltersXml.INTERNAL_SYSTEM_ALARMS_FILTER,
	alarmFiltersXml.SECURE_SPECIFIC_ALARMS_FILTER,
	alarmFiltersXml.ID_ACCESS_SYSTEM_ALARMS_FILTER,
	alarmFiltersXml.LOOP_FAILED_ALARMS_FILTER,
	alarmFiltersXml.LOOP_OK_ALARMS_FILTER,
	alarmFiltersXml.SERVICE_PIN_ALARMS_FILTER
	FROM OpenXML(@hXmlDocFilters, '/DefaultAlarmConfiguration/AlarmFilters',1) WITH
	(
		SENSOR_ALARMS_FILTER NVARCHAR(255) N'@SENSOR_ALARMS_FILTER',
		DRIVER_ALARMS_FILTER NVARCHAR(255) N'@DRIVER_ALARMS_FILTER',
		DIGITAL_INPUT_ALARMS_FILTER NVARCHAR(255) N'@DIGITAL_INPUT_ALARMS_FILTER',
		CRITICAL_ALARMS_FILTER NVARCHAR(255) N'@CRITICAL_ALARMS_FILTER',
		NETWORK_ALARMS_FILTER NVARCHAR(255) N'@NETWORK_ALARMS_FILTER',
		GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER NVARCHAR(255) N'@GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER',
		ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER NVARCHAR(255) N'@ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER',
		USER_ADJUSTMENTS_ALARMS_FILTER NVARCHAR(255) N'@USER_ADJUSTMENTS_ALARMS_FILTER',
		CATCH_ALL_ALARMS_FILTER NVARCHAR(255) N'@CATCH_ALL_ALARMS_FILTER',
		USER_LOGIN_LOGOUT_ALARMS_FILTER NVARCHAR(255) N'@USER_LOGIN_LOGOUT_ALARMS_FILTER',
		DATA_LOGGING_OK_ALARMS_FILTER NVARCHAR(255) N'@DATA_LOGGING_OK_ALARMS_FILTER',
		DIARY_DOWNLOAD_OK_ALARMS_FILTER NVARCHAR(255) N'@DIARY_DOWNLOAD_OK_ALARMS_FILTER',
		DIARY_DOWNLOAD_FAILED_ALARMS_FILTER NVARCHAR(255) N'@DIARY_DOWNLOAD_FAILED_ALARMS_FILTER',
		DATA_LOGGING_FAILED_ALARMS_FILTER NVARCHAR(255) N'@DATA_LOGGING_FAILED_ALARMS_FILTER',
		SCHEDULER_ACTION_FAILED_ALARMS_FILTER NVARCHAR(255) N'@SCHEDULER_ACTION_FAILED_ALARMS_FILTER',
		SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER NVARCHAR(255) N'@SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER',
		AUTO_DIALLER_ALARMS_FILTER NVARCHAR(255) N'@AUTO_DIALLER_ALARMS_FILTER',
		ALARM_RETRANSMISSION_OK_ALARMS_FILTER NVARCHAR(255) N'@ALARM_RETRANSMISSION_OK_ALARMS_FILTER',
		STARTUP_SHUTDOWN_ALARMS_FILTER NVARCHAR(255) N'@STARTUP_SHUTDOWN_ALARMS_FILTER',
		INTERNAL_SYSTEM_ALARMS_FILTER NVARCHAR(255) N'@INTERNAL_SYSTEM_ALARMS_FILTER',
		SECURE_SPECIFIC_ALARMS_FILTER NVARCHAR(255) N'@SECURE_SPECIFIC_ALARMS_FILTER',
		ID_ACCESS_SYSTEM_ALARMS_FILTER NVARCHAR(255) N'@ID_ACCESS_SYSTEM_ALARMS_FILTER',
		LOOP_FAILED_ALARMS_FILTER NVARCHAR(255) N'@LOOP_FAILED_ALARMS_FILTER',
		LOOP_OK_ALARMS_FILTER NVARCHAR(255) N'@LOOP_OK_ALARMS_FILTER',
		SERVICE_PIN_ALARMS_FILTER NVARCHAR(255) N'@SERVICE_PIN_ALARMS_FILTER'

	) alarmFiltersXml

	OPEN alarm_filters_cursor
	FETCH NEXT FROM alarm_filters_cursor
	INTO
	@963_SENSOR_ALARMS_FILTER,
	@963_DRIVER_ALARMS_FILTER,
	@963_DIGITAL_INPUT_ALARMS_FILTER,
	@963_CRITICAL_ALARMS_FILTER,
	@963_NETWORK_ALARMS_FILTER,
	@963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER,
	@963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER,
	@963_USER_ADJUSTMENTS_ALARMS_FILTER,
	@963_CATCH_ALL_ALARMS_FILTER,
	@963_USER_LOGIN_LOGOUT_ALARMS_FILTER,
	@963_DATA_LOGGING_OK_ALARMS_FILTER,
	@963_DIARY_DOWNLOAD_OK_ALARMS_FILTER,
	@963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER,
	@963_DATA_LOGGING_FAILED_ALARMS_FILTER,
	@963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER,
	@963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER,
	@963_AUTO_DIALLER_ALARMS_FILTER,
	@963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER,
	@963_STARTUP_SHUTDOWN_ALARMS_FILTER,
	@963_INTERNAL_SYSTEM_ALARMS_FILTER,
	@963_SECURE_SPECIFIC_ALARMS_FILTER,
	@963_ID_ACCESS_SYSTEM_ALARMS_FILTER,
	@963_LOOP_FAILED_ALARMS_FILTER,
	@963_LOOP_OK_ALARMS_FILTER,
	@963_SERVICE_PIN_ALARMS_FILTER

	-- cursor to get default alarm group names from xml document passed as paramter
	DECLARE alarm_groups_cursor CURSOR FOR
	SELECT
	alarmGroupsXml.SECURE_SPECIFIC_ALARMS_GROUP,
	alarmGroupsXml.USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP,
	alarmGroupsXml.STRATEGY_SPECIFIC_ALARMS_GROUP,
	alarmGroupsXml.NETWORK_COMMUNICATION_ALARMS_GROUP,
	alarmGroupsXml.DEVICE_SPECIFIC_ALARMS_GROUP,
	alarmGroupsXml.CRITICAL_ALARMS_GROUP,
	alarmGroupsXml.SCHEDULED_ACTION_FAILED_ALARMS_GROUP,
	alarmGroupsXml.ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP,
	alarmGroupsXml.SERVICE_PIN_ALARMS_GROUP
	FROM OpenXML(@hXmlDocGroups, '/DefaultAlarmConfiguration/AlarmGroups',1) WITH
	(
		SECURE_SPECIFIC_ALARMS_GROUP NVARCHAR(255)  N'@SECURE_SPECIFIC_ALARMS_GROUP',
		USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP NVARCHAR(255) N'@USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP',
		STRATEGY_SPECIFIC_ALARMS_GROUP NVARCHAR(255) N'@STRATEGY_SPECIFIC_ALARMS_GROUP',
		NETWORK_COMMUNICATION_ALARMS_GROUP NVARCHAR(255) N'@NETWORK_COMMUNICATION_ALARMS_GROUP',
		DEVICE_SPECIFIC_ALARMS_GROUP NVARCHAR(255) N'@DEVICE_SPECIFIC_ALARMS_GROUP',
		CRITICAL_ALARMS_GROUP NVARCHAR(255) N'@CRITICAL_ALARMS_GROUP',
		SCHEDULED_ACTION_FAILED_ALARMS_GROUP NVARCHAR(255) N'@SCHEDULED_ACTION_FAILED_ALARMS_GROUP',
		ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP NVARCHAR(255) N'@ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP',
		SERVICE_PIN_ALARMS_GROUP NVARCHAR(255) N'@SERVICE_PIN_ALARMS_GROUP'

	) alarmGroupsXml

	OPEN alarm_groups_cursor
	FETCH NEXT FROM alarm_groups_cursor
	INTO
	@963_SECURE_SPECIFIC_ALARMS_GROUP,
	@963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP,
	@963_STRATEGY_SPECIFIC_ALARMS_GROUP,
	@963_NETWORK_COMMUNICATION_ALARMS_GROUP,
	@963_DEVICE_SPECIFIC_ALARMS_GROUP,
	@963_CRITICAL_ALARMS_GROUP,
	@963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP,
	@963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP,
	@963_SERVICE_PIN_ALARMS_GROUP

	-- cursor to get miscelleneous alarm configuration related fields
	DECLARE alarm_miscelleneous_cursor CURSOR FOR
	SELECT	
	alarmMiscelleneousXml.MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText,
	alarmMiscelleneousXml.MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText,
	alarmMiscelleneousXml.MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText,	
	alarmMiscelleneousXml.MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText,
	alarmMiscelleneousXml.MISC_PARAM_SITE,
	alarmMiscelleneousXml.MISC_PARAM_LAN,
	alarmMiscelleneousXml.MISC_PARAM_OS,
	alarmMiscelleneousXml.MISC_PARAM_ALARM_SPIN,
	alarmMiscelleneousXml.MISC_PARAM_SPIN_RECEIVED_MESSAGE,
	alarmMiscelleneousXml.MISC_PARAM_DEVICE_SERIAL_NUMBER
	FROM OpenXML(@hXmlDocMiscelleneous, '/DefaultAlarmConfiguration/Miscellaneous',1) WITH
	(	
		MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText NVARCHAR(255) N'@MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText',
		MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText NVARCHAR(255) N'@MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText',
		MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText NVARCHAR(255) N'@MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText',
		MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText NVARCHAR(255) N'@MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText',
		MISC_PARAM_SITE NVARCHAR(255) N'@MISC_PARAM_SITE',
		MISC_PARAM_LAN NVARCHAR(255) N'@MISC_PARAM_LAN',
		MISC_PARAM_OS NVARCHAR(255) N'@MISC_PARAM_OS',
		MISC_PARAM_ALARM_SPIN NVARCHAR(255) N'@MISC_PARAM_ALARM_SPIN',
		MISC_PARAM_SPIN_RECEIVED_MESSAGE NVARCHAR(255) N'@MISC_PARAM_SPIN_RECEIVED_MESSAGE',
		MISC_PARAM_DEVICE_SERIAL_NUMBER NVARCHAR(255) N'@MISC_PARAM_DEVICE_SERIAL_NUMBER'
	) alarmMiscelleneousXml

	OPEN alarm_miscelleneous_cursor
	FETCH NEXT FROM alarm_miscelleneous_cursor
	INTO
	@963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText,
	@963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText,
	@963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText,	
	@963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText,
	@963_MISC_PARAM_SITE,
	@963_MISC_PARAM_LAN,
	@963_MISC_PARAM_OS,
	@963_MISC_PARAM_ALARM_SPIN,
	@963_MISC_PARAM_SPIN_RECEIVED_MESSAGE,
	@963_MISC_PARAM_DEVICE_SERIAL_NUMBER

	--
	-- Step 1
	-- insert default pre-configured filters
	--

	DECLARE @extendedFilterID int
	DECLARE @filterIndex int

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SENSOR_ALARMS_FILTER )
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'OUTL, LOW, O/K,CHIH,CLOW,HIGH,READ', N'*', N'*', @963_SENSOR_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''READ'') OR (AlarmCode LIKE N''HIGH'') OR (AlarmCode LIKE N''CLOW'') OR (AlarmCode LIKE N''CHIH'') OR (AlarmCode LIKE N'' O/K'') OR (AlarmCode LIKE N'' LOW'') OR (AlarmCode LIKE N''OUTL''))')	

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'OUTL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'OUTL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LOW')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'O/K')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'O/K',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHIH')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHIH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLOW')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HIGH')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HIGH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'READ')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'READ',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SENSOR_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''READ'') OR (AlarmCode LIKE N''HIGH'') OR (AlarmCode LIKE N''CLOW'') OR (AlarmCode LIKE N''CHIH'') OR (AlarmCode LIKE N'' O/K'') OR (AlarmCode LIKE N'' LOW'') OR (AlarmCode LIKE N''OUTL''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'OUTL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'OUTL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LOW')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'O/K')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'O/K',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHIH')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHIH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLOW')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLOW',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HIGH')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HIGH',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'READ')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'READ',N'%',N'%',1,1,0)
	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DRIVER_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CDGT,CMNT,SDGT,MINT', N'*', N'*', @963_DRIVER_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''MINT'') OR (AlarmCode LIKE N''SDGT'') OR (AlarmCode LIKE N''CMNT'') OR (AlarmCode LIKE N''CDGT''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDGT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CMNT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CMNT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDGT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MINT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MINT',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DRIVER_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''MINT'') OR (AlarmCode LIKE N''SDGT'') OR (AlarmCode LIKE N''CMNT'') OR (AlarmCode LIKE N''CDGT''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDGT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CMNT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CMNT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDGT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDGT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MINT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MINT',N'%',N'%',1,1,0)

	END
		
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIGITAL_INPUT_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DI=0,DI=1,CDI0,CDI1', N'*', N'*', @963_DIGITAL_INPUT_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''CDI1'') OR (AlarmCode LIKE N''CDI0'') OR (AlarmCode LIKE N''DI=1'') OR (AlarmCode LIKE N''DI=0''))')
		
		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=0')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=1')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=1',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI0')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI1')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI1',N'%',N'%',1,1,0)
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIGITAL_INPUT_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CDI1'') OR (AlarmCode LIKE N''CDI0'') OR (AlarmCode LIKE N''DI=1'') OR (AlarmCode LIKE N''DI=0''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=0')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DI=1')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DI=1',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI0')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI0',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CDI1')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CDI1',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_CRITICAL_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SCRI,CCRI', N'*', N'*', @963_CRITICAL_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''CCRI'') OR (AlarmCode LIKE N''SCRI''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SCRI')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SCRI',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CCRI')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CCRI',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_CRITICAL_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CCRI'') OR (AlarmCode LIKE N''SCRI''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SCRI')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SCRI',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CCRI')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CCRI',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_NETWORK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'NKBK,NKCH,NKDA,NKFL,NKHD,NKOK,NKSV,NKUR,DVDD,DVOK', N'*', N'*', @963_NETWORK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DVOK'') OR (AlarmCode LIKE N''DVDD'') OR (AlarmCode LIKE N''NKUR'') OR (AlarmCode LIKE N''NKSV'') OR (AlarmCode LIKE N''NKOK'') OR (AlarmCode LIKE N''NKHD'') OR (AlarmCode LIKE N''NKFL'') OR (AlarmCode LIKE N''NKDA'') OR (AlarmCode LIKE N''NKCH'') OR (AlarmCode LIKE N''NKBK''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKCH')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKCH',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKDA')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKDA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKHD')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKHD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKOK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKSV')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKSV',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKUR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVDD')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVDD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_NETWORK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DVOK'') OR (AlarmCode LIKE N''DVDD'') OR (AlarmCode LIKE N''NKUR'') OR (AlarmCode LIKE N''NKSV'') OR (AlarmCode LIKE N''NKOK'') OR (AlarmCode LIKE N''NKHD'') OR (AlarmCode LIKE N''NKFL'') OR (AlarmCode LIKE N''NKDA'') OR (AlarmCode LIKE N''NKCH'') OR (AlarmCode LIKE N''NKBK''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKCH')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKCH',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKDA')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKDA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKHD')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKHD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKOK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKSV')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKSV',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKUR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVDD')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVDD',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DVOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DVOK',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CONL,FDRT,FLER,FPIA,FPRM,FRAM,FRTC,FSWR,FTKA,FTKP,HELP,NKBL', N'*', N'*', @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''NKBL'') OR (AlarmCode LIKE N''HELP'') OR (AlarmCode LIKE N''FTKP'') OR (AlarmCode LIKE N''FTKA'') OR (AlarmCode LIKE N''FSWR'') OR (AlarmCode LIKE N''FRTC'') OR (AlarmCode LIKE N''FRAM'') OR (AlarmCode LIKE N''FPRM'') OR (AlarmCode LIKE N''FPIA'') OR (AlarmCode LIKE N''FLER'') OR (AlarmCode LIKE N''FDRT'') OR (AlarmCode LIKE N''CONL''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FDRT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FDRT',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FLER')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FLER',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPIA')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPIA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPRM')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPRM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRAM')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRAM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRTC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRTC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FSWR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FSWR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKA')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKP')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HELP')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HELP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''NKBL'') OR (AlarmCode LIKE N''HELP'') OR (AlarmCode LIKE N''FTKP'') OR (AlarmCode LIKE N''FTKA'') OR (AlarmCode LIKE N''FSWR'') OR (AlarmCode LIKE N''FRTC'') OR (AlarmCode LIKE N''FRAM'') OR (AlarmCode LIKE N''FPRM'') OR (AlarmCode LIKE N''FPIA'') OR (AlarmCode LIKE N''FLER'') OR (AlarmCode LIKE N''FDRT'') OR (AlarmCode LIKE N''CONL''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FDRT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FDRT',N'%',N'%',1,1,0)
		
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FLER')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FLER',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPIA')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPIA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FPRM')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FPRM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRAM')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRAM',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FRTC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FRTC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FSWR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FSWR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKA')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKA',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'FTKP')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'FTKP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HELP')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HELP',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'NKBL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'NKBL',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'TXFL', N'*', N'*', @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''TXFL''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXFL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''TXFL''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXFL',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_ADJUSTMENTS_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'ADJF,ADJU', N'*', N'*', @963_USER_ADJUSTMENTS_ALARMS_FILTER, N'*', 0, 1, 1)
		
		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''ADJU'') OR (AlarmCode LIKE N''ADJF''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJU')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJU',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_ADJUSTMENTS_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''ADJU'') OR (AlarmCode LIKE N''ADJF''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'ADJU')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'ADJU',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_CATCH_ALL_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'*', N'*', @963_CATCH_ALL_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'*')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'%')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_CATCH_ALL_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'*')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'%')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_LOGIN_LOGOUT_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'LGOF,LGON', N'*', N'*', @963_USER_LOGIN_LOGOUT_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''LGON'') OR (AlarmCode LIKE N''LGOF''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGOF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGOF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGON')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGON',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_USER_LOGIN_LOGOUT_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''LGON'') OR (AlarmCode LIKE N''LGOF''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGOF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGOF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LGON')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LGON',N'%',N'%',1,1,0)

	END
	
	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DLOK', N'*', N'*', @963_DATA_LOGGING_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DLOK''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLOK',N'%',N'%',1,1,0)
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DLOK''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DYOK', N'*', N'*', @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DYOK''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DYOK''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DYFL', N'*', N'*', @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DYFL''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYFL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DYFL''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DYFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DYFL',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DLFL', N'*', N'*', @963_DATA_LOGGING_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DLFL''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLFL',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_DATA_LOGGING_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DLFL''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DLFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DLFL',N'%',N'%',1,1,0)

	END

	DECLARE @filterSQL NVARCHAR(255)	-- to use the translatable description passed as paramter from application

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText, N'*', @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY		

		SET @filterSQL = N'((theDescription LIKE ' + 'N''' + @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText + '''))'		

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex , @filterSQL)
		

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText)
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',@963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText,N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER)

		SET @filterSQL = N'((theDescription LIKE ' + 'N''' + @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText + '''))'

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID , @filterSQL)

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE @963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText)
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',@963_MISC_PARAM_SCHEDULER_ACTION_FAILED_ALARMS_FILTER_FilterMatchLookup_AlarmText,N'%',1,1,0)

	END	

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_ExtendedAlarmFilters_AlarmText, N'*', @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY
		
		SET @filterSQL = N'((theDescription LIKE ' + 'N''' + @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText + '''))'

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex , @filterSQL)

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText)
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',@963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText,N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER)

		SET @filterSQL = N'((theDescription LIKE ' + 'N''' + @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText + '''))'

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID , @filterSQL)

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmText LIKE @963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText)
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',@963_MISC_PARAM_SCHEDULER_ACTION_COMPLETED_ALARMS_FILTER_FilterMatchLookup_AlarmText,N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_AUTO_DIALLER_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'AANR,AONL,BTNR,LINR,MONR,PGNR', N'*', N'*', @963_AUTO_DIALLER_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''PGNR'') OR (AlarmCode LIKE N''MONR'') OR (AlarmCode LIKE N''LINR'') OR (AlarmCode LIKE N''BTNR'') OR (AlarmCode LIKE N''AONL'') OR (AlarmCode LIKE N''AANR''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AANR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AANR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AONL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'BTNR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'BTNR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LINR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LINR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MONR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MONR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'PGNR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'PGNR',N'%',N'%',1,1,0)


	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_AUTO_DIALLER_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''PGNR'') OR (AlarmCode LIKE N''MONR'') OR (AlarmCode LIKE N''LINR'') OR (AlarmCode LIKE N''BTNR'') OR (AlarmCode LIKE N''AONL'') OR (AlarmCode LIKE N''AANR''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AANR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AANR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'AONL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'AONL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'BTNR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'BTNR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LINR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LINR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MONR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MONR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'PGNR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'PGNR',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'TXOK', N'*', N'*', @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''TXOK''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_ALARM_RETRANSMISSION_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''TXOK''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'TXOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'TXOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_STARTUP_SHUTDOWN_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SHDN,STUP', N'*', N'*', @963_STARTUP_SHUTDOWN_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''STUP'') OR (AlarmCode LIKE N''SHDN''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SHDN')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SHDN',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'STUP')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'STUP',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_STARTUP_SHUTDOWN_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''STUP'') OR (AlarmCode LIKE N''SHDN''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SHDN')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SHDN',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'STUP')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'STUP',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_INTERNAL_SYSTEM_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SYST', N'*', N'*', @963_INTERNAL_SYSTEM_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''SYST''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SYST')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SYST',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_INTERNAL_SYSTEM_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SYST''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SYST')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SYST',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SECURE_SPECIFIC_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CLKU,CLMK,CHMK,CONF,HMKT,LKUR,LMKT,MKFL,MKOK', N'*', N'*', @963_SECURE_SPECIFIC_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''MKOK'') OR (AlarmCode LIKE N''MKFL'') OR (AlarmCode LIKE N''LMKT'') OR (AlarmCode LIKE N''LKUR'') OR (AlarmCode LIKE N''HMKT'') OR (AlarmCode LIKE N''CONF'') OR (AlarmCode LIKE N''CHMK'') OR (AlarmCode LIKE N''CLMK'') OR (AlarmCode LIKE N''CLKU''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLKU')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLKU',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLMK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHMK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HMKT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LKUR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LMKT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKOK',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SECURE_SPECIFIC_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''MKOK'') OR (AlarmCode LIKE N''MKFL'') OR (AlarmCode LIKE N''LMKT'') OR (AlarmCode LIKE N''LKUR'') OR (AlarmCode LIKE N''HMKT'') OR (AlarmCode LIKE N''CONF'') OR (AlarmCode LIKE N''CHMK'') OR (AlarmCode LIKE N''CLMK'') OR (AlarmCode LIKE N''CLKU''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLKU')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLKU',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CLMK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CLMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CHMK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CHMK',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CONF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CONF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'HMKT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'HMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LKUR')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LKUR',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'LMKT')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'LMKT',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKFL')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKFL',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'MKOK')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'MKOK',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_ID_ACCESS_SYSTEM_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DRAC,DRFC,DRFS,DRHC,DRHS,DROC,DROS,DRSC,DRSF,DRVS', N'*', N'*', @963_ID_ACCESS_SYSTEM_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''DRVS'') OR (AlarmCode LIKE N''DRSF'') OR (AlarmCode LIKE N''DRSC'') OR (AlarmCode LIKE N''DROS'') OR (AlarmCode LIKE N''DROC'') OR (AlarmCode LIKE N''DRHS'') OR (AlarmCode LIKE N''DRHC'') OR (AlarmCode LIKE N''DRFS'') OR (AlarmCode LIKE N''DRFC'') OR (AlarmCode LIKE N''DRAC''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRAC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRAC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRVS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRVS',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_ID_ACCESS_SYSTEM_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DRVS'') OR (AlarmCode LIKE N''DRSF'') OR (AlarmCode LIKE N''DRSC'') OR (AlarmCode LIKE N''DROS'') OR (AlarmCode LIKE N''DROC'') OR (AlarmCode LIKE N''DRHS'') OR (AlarmCode LIKE N''DRHC'') OR (AlarmCode LIKE N''DRFS'') OR (AlarmCode LIKE N''DRFC'') OR (AlarmCode LIKE N''DRAC''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRAC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRAC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRFS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRFS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRHS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRHS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DROS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DROS',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSC')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSC',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRSF')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRSF',N'%',N'%',1,1,0)

		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'DRVS')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'DRVS',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_FAILED_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SDEV', N'*', N'*', @963_LOOP_FAILED_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''SDEV''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDEV')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDEV',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_FAILED_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SDEV''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SDEV')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SDEV',N'%',N'%',1,1,0)
	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_OK_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CSDV', N'*', N'*', @963_LOOP_OK_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''CSDV''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CSDV')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CSDV',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_LOOP_OK_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CSDV''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'CSDV')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'CSDV',N'%',N'%',1,1,0)

	END

	IF NOT EXISTS (SELECT Title FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SERVICE_PIN_ALARMS_FILTER)
	BEGIN
		INSERT INTO [dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SPIN', N'*', N'*', @963_SERVICE_PIN_ALARMS_FILTER, N'*', 0, 1, 1)

		SET @filterIndex = @@IDENTITY

		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@filterIndex ,N'((AlarmCode LIKE N''SPIN''))')

		-- insert into [dbo].[FilterMatchLookup]				
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SPIN')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SPIN',N'%',N'%',1,1,0)

	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [dbo].[ExtendedAlarmFilters] WHERE Title = @963_SERVICE_PIN_ALARMS_FILTER)

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SPIN''))')

		-- insert into [dbo].[FilterMatchLookup]		
		SET @filterIndex = @extendedFilterID
		IF NOT EXISTS (SELECT FilterIndex FROM FilterMatchLookup WHERE FilterIndex = @filterIndex AND AlarmCode = N'SPIN')
		INSERT INTO [dbo].[FilterMatchLookup] ([FilterIndex] ,[ConnectionString] ,[SiteLabel] ,[LanNumRange] ,[LanLabel] ,[OsNumRange] ,[OsLabel] ,[ModuleRefRange] ,[ModuleLabel] ,[AlarmCode] ,[AlarmText] ,[AlarmPriorityRange] ,[FilterSetAlarms] ,[FilterClearAlarms] ,[Exclude])
		VALUES (@filterIndex,N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'%',N'SPIN',N'%',N'%',1,1,0)

	END

	--
	-- Step 2
	-- insert default pre-configured alarm groups
	--

	DECLARE @printWhatText NVARCHAR(255) -- to formulate the print what text using the translatable fields passed as paramters from application
	DECLARE @actionWhenOcc_963_SERVICE_PIN_ALARMS_GROUP NVARCHAR(255) -- to formulat the action using translatable fields passed as params from application

	SET @printWhatText = N'<LABEL><TAB><ALARMDESC><TAB><TIME>' + @963_MISC_PARAM_SITE + ':<SITE><TAB>' + @963_MISC_PARAM_LAN 
		+ ': <LANLABEL><TAB>' + @963_MISC_PARAM_OS +': <OSLABEL><TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>'

	SET @actionWhenOcc_963_SERVICE_PIN_ALARMS_GROUP = N'MESSAGE' + @963_MISC_PARAM_ALARM_SPIN +',' + @963_MISC_PARAM_SPIN_RECEIVED_MESSAGE 
		+ ':<NEWLINE><NEWLINE>' + @963_MISC_PARAM_SITE + ' = <CONNECTION><NEWLINE>' + @963_MISC_PARAM_LAN + ' = (<LAN>) <LANLABEL><NEWLINE>' 
		+ @963_MISC_PARAM_OS + ' = (<OS>) <OSLABEL><NEWLINE>' + @963_MISC_PARAM_DEVICE_SERIAL_NUMBER + ' = <SERIALNO>,0,!,0,0'

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_SECURE_SPECIFIC_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_SECURE_SPECIFIC_ALARMS_GROUP, N'', 0, 255, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP, N'', 0, 255, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_STRATEGY_SPECIFIC_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_STRATEGY_SPECIFIC_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_NETWORK_COMMUNICATION_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_NETWORK_COMMUNICATION_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_DEVICE_SPECIFIC_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_DEVICE_SPECIFIC_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_CRITICAL_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_CRITICAL_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [dbo].[AlarmGroup] WHERE title = @963_SERVICE_PIN_ALARMS_GROUP)
	INSERT INTO [dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, @actionWhenOcc_963_SERVICE_PIN_ALARMS_GROUP, N'', @963_SERVICE_PIN_ALARMS_GROUP, N'', 1, 33023, 1, 1, @printWhatText, 0, 0, 0, N'')

	--
	-- Step 3
	-- inserts into AlarmFilterToAlarmGroup for pre-configured alarm filters and alarm groups
	--
	-- also, assign newly created alarm groups with default workgroup for all alarm notifications
	--

	DECLARE @alarmGroupID int
	-- DECLARE @extendedFilterID int

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_SECURE_SPECIFIC_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SECURE_SPECIFIC_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_USER_ACTIVITY_LOGIN_LOGOUT_ADJUSTMENTS_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_USER_ADJUSTMENTS_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_USER_LOGIN_LOGOUT_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_STARTUP_SHUTDOWN_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_STRATEGY_SPECIFIC_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SENSOR_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DRIVER_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DIGITAL_INPUT_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_LOOP_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_LOOP_OK_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_NETWORK_COMMUNICATION_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_NETWORK_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_DEVICE_SPECIFIC_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_GENERAL_CONTROLLER_FAULTS_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_AUTO_DIALLER_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_ID_ACCESS_SYSTEM_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_NETWORK_COMMUNICATION_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_NETWORK_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_CRITICAL_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_CRITICAL_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_SCHEDULED_ACTION_FAILED_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DIARY_DOWNLOAD_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_DATA_LOGGING_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SCHEDULER_ACTION_FAILED_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_ALARM_RETRANSMISSION_FAILURE_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = @963_SERVICE_PIN_ALARMS_GROUP)

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = @963_SERVICE_PIN_ALARMS_FILTER)
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign this alarm group to default workgroup	
	IF NOT EXISTS (SELECT operatorGroup FROM AlarmGroupToWorkgroupLink WHERE alarmGroupID = @alarmGroupID AND operatorGroup = @defaultWorkgroup)
	INSERT INTO [i96X].[dbo].[AlarmGroupToWorkgroupLink] ([alarmGroupID], [operatorGroup], [alarmAction])
	VALUES (@alarmGroupID, @defaultWorkgroup, N'')

	CLOSE alarm_filters_cursor -- close alarm filters cursor
	DEALLOCATE alarm_filters_cursor -- deallocate alarm filters cursor

	CLOSE alarm_groups_cursor -- close alarm groups cursor
	DEALLOCATE alarm_groups_cursor -- deallocate alarm groups cursor

	CLOSE alarm_miscelleneous_cursor -- close alarm miscelleneous cursor
	DEALLOCATE alarm_miscelleneous_cursor -- deallocate alarm miscelleneous cursor

	EXECUTE @retValue = sp_xml_removedocument @hXmlDocFilters -- remove handle to alarm filters and filters xml document
	IF (@retValue <> 0)
	BEGIN
		PRINT N'sp_xml_preparedocument failed for alarm group names'
		GOTO ON_ERROR
	END

	EXECUTE @retValue = sp_xml_removedocument @hXmlDocGroups -- remove handle to alarm groups and filters xml document
	IF (@retValue <> 0)
	BEGIN
		PRINT N'sp_xml_preparedocument failed for alarm group names'
		GOTO ON_ERROR
	END

	EXECUTE @retValue = sp_xml_removedocument @hXmlDocMiscelleneous -- remove handle to alarm groups and filters xml document
	IF (@retValue <> 0)
	BEGIN
		PRINT N'sp_xml_preparedocument failed for alarm miscelleneous fields'
		GOTO ON_ERROR
	END

	COMMIT TRAN DefaultAlarmConfiguration_TRAN

	RETURN @success -- zero if everything is ok

ON_ERROR:
	SET @success = 1 -- return 1 if there is an error
	PRINT N'Error occured in executing the script. Roll back transaction now'
	ROLLBACK TRAN DefaultAlarmConfiguration_TRAN
	RETURN @success
END

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