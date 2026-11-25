--
-- insert default alarm groups and alarm filters
-- and assign alarm filters to alarm groups
--

USE <96XDBNAME>
--USE i96x
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
	-- insert default pre-configured filters
	--

	DECLARE @extendedFilterID int

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Sensor Alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'OUTL, LOW, O/K,CHIH,CLOW,HIGH,READ', N'*', N'*', N'963 - Sensor Alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''READ'') OR (AlarmCode LIKE N''HIGH'') OR (AlarmCode LIKE N''CLOW'') OR (AlarmCode LIKE N''CHIH'') OR (AlarmCode LIKE N'' O/K'') OR (AlarmCode LIKE N'' LOW'') OR (AlarmCode LIKE N''OUTL''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Sensor Alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''READ'') OR (AlarmCode LIKE N''HIGH'') OR (AlarmCode LIKE N''CLOW'') OR (AlarmCode LIKE N''CHIH'') OR (AlarmCode LIKE N'' O/K'') OR (AlarmCode LIKE N'' LOW'') OR (AlarmCode LIKE N''OUTL''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Driver Alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CDGT,CMNT,SDGT,MINT', N'*', N'*', N'963 - Driver Alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''MINT'') OR (AlarmCode LIKE N''SDGT'') OR (AlarmCode LIKE N''CMNT'') OR (AlarmCode LIKE N''CDGT''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Driver Alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''MINT'') OR (AlarmCode LIKE N''SDGT'') OR (AlarmCode LIKE N''CMNT'') OR (AlarmCode LIKE N''CDGT''))')
	END
		
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Digital Input Alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DI=0,DI=1,CDI0,CDI1', N'*', N'*', N'963 - Digital Input Alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''CDI1'') OR (AlarmCode LIKE N''CDI0'') OR (AlarmCode LIKE N''DI=1'') OR (AlarmCode LIKE N''DI=0''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Digital Input Alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CDI1'') OR (AlarmCode LIKE N''CDI0'') OR (AlarmCode LIKE N''DI=1'') OR (AlarmCode LIKE N''DI=0''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Critical Alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SCRI,CCRI', N'*', N'*', N'963 - Critical Alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''CCRI'') OR (AlarmCode LIKE N''SCRI''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Critical Alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CCRI'') OR (AlarmCode LIKE N''SCRI''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Network Alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'NKBK,NKCH,NKDA,NKFL,NKHD,NKOK,NKSV,NKUR,DVDD,DVOK', N'*', N'*', N'963 - Network Alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''DVOK'') OR (AlarmCode LIKE N''DVDD'') OR (AlarmCode LIKE N''NKUR'') OR (AlarmCode LIKE N''NKSV'') OR (AlarmCode LIKE N''NKOK'') OR (AlarmCode LIKE N''NKHD'') OR (AlarmCode LIKE N''NKFL'') OR (AlarmCode LIKE N''NKDA'') OR (AlarmCode LIKE N''NKCH'') OR (AlarmCode LIKE N''NKBK''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Network Alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DVOK'') OR (AlarmCode LIKE N''DVDD'') OR (AlarmCode LIKE N''NKUR'') OR (AlarmCode LIKE N''NKSV'') OR (AlarmCode LIKE N''NKOK'') OR (AlarmCode LIKE N''NKHD'') OR (AlarmCode LIKE N''NKFL'') OR (AlarmCode LIKE N''NKDA'') OR (AlarmCode LIKE N''NKCH'') OR (AlarmCode LIKE N''NKBK''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - General controller faults')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CONL,FDRT,FLER,FPIA,FPRM,FRAM,FRTC,FSWR,FTKA,FTKP,HELP,NKBL', N'*', N'*', N'963 - General controller faults', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''NKBL'') OR (AlarmCode LIKE N''HELP'') OR (AlarmCode LIKE N''FTKP'') OR (AlarmCode LIKE N''FTKA'') OR (AlarmCode LIKE N''FSWR'') OR (AlarmCode LIKE N''FRTC'') OR (AlarmCode LIKE N''FRAM'') OR (AlarmCode LIKE N''FPRM'') OR (AlarmCode LIKE N''FPIA'') OR (AlarmCode LIKE N''FLER'') OR (AlarmCode LIKE N''FDRT'') OR (AlarmCode LIKE N''CONL''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - General controller faults')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''NKBL'') OR (AlarmCode LIKE N''HELP'') OR (AlarmCode LIKE N''FTKP'') OR (AlarmCode LIKE N''FTKA'') OR (AlarmCode LIKE N''FSWR'') OR (AlarmCode LIKE N''FRTC'') OR (AlarmCode LIKE N''FRAM'') OR (AlarmCode LIKE N''FPRM'') OR (AlarmCode LIKE N''FPIA'') OR (AlarmCode LIKE N''FLER'') OR (AlarmCode LIKE N''FDRT'') OR (AlarmCode LIKE N''CONL''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Alarm retransmission failure')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'TXFL', N'*', N'*', N'963 - Alarm retransmission failure', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''TXFL''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Alarm retransmission failure')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''TXFL''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - User adjustments')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'ADJF,ADJU', N'*', N'*', N'963 - User adjustments', N'*', 0, 1, 1)
		
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''ADJU'') OR (AlarmCode LIKE N''ADJF''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - User adjustments')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''ADJU'') OR (AlarmCode LIKE N''ADJF''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Catch all')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'*', N'*', N'963 - Catch all', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'*')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Catch all')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'*')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - User login/logout')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'LGOF,LGON', N'*', N'*', N'963 - User login/logout', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''LGON'') OR (AlarmCode LIKE N''LGOF''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - User login/logout')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''LGON'') OR (AlarmCode LIKE N''LGOF''))')
	END
	
	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Data logging OK')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DLOK', N'*', N'*', N'963 - Data logging OK', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''DLOK''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Data logging OK')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DLOK''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Diary download OK')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DYOK', N'*', N'*', N'963 - Diary download OK', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''DYOK''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Diary download OK')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DYOK''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Diary download failed')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DYFL', N'*', N'*', N'963 - Diary download failed', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''DYFL''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Diary download failed')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DYFL''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Data logging failed')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DLFL', N'*', N'*', N'963 - Data logging failed', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''DLFL''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Data logging failed')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DLFL''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Scheduler action failed')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'Scheduler command failed*', N'*', N'963 - Scheduler action failed', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((theDescription LIKE N''Scheduler command failed%''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Scheduler action failed')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((theDescription LIKE N''Scheduler command failed%''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Scheduler action completed')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'*', N'Scheduler command completed*', N'*', N'963 - Scheduler action completed', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((theDescription LIKE N''Scheduler command completed%''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Scheduler action completed')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((theDescription LIKE N''Scheduler command completed%''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Autodialler alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'AANR,AONL,BTNR,LINR,MONR,PGNR', N'*', N'*', N'963 - Autodialler alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''PGNR'') OR (AlarmCode LIKE N''MONR'') OR (AlarmCode LIKE N''LINR'') OR (AlarmCode LIKE N''BTNR'') OR (AlarmCode LIKE N''AONL'') OR (AlarmCode LIKE N''AANR''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Autodialler alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''PGNR'') OR (AlarmCode LIKE N''MONR'') OR (AlarmCode LIKE N''LINR'') OR (AlarmCode LIKE N''BTNR'') OR (AlarmCode LIKE N''AONL'') OR (AlarmCode LIKE N''AANR''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Alarm retransmission OK')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'TXOK', N'*', N'*', N'963 - Alarm retransmission OK', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''TXOK''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Alarm retransmission OK')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''TXOK''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Startup/shutdown')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SHDN,STUP', N'*', N'*', N'963 - Startup/shutdown', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''STUP'') OR (AlarmCode LIKE N''SHDN''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Startup/shutdown')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''STUP'') OR (AlarmCode LIKE N''SHDN''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Internal system alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SYST', N'*', N'*', N'963 - Internal system alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''SYST''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Internal system alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SYST''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Secure-specific alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CLKU,CLMK,CHMK,CONF,HMKT,LKUR,LMKT,MKFL,MKOK', N'*', N'*', N'963 - Secure-specific alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''MKOK'') OR (AlarmCode LIKE N''MKFL'') OR (AlarmCode LIKE N''LMKT'') OR (AlarmCode LIKE N''LKUR'') OR (AlarmCode LIKE N''HMKT'') OR (AlarmCode LIKE N''CONF'') OR (AlarmCode LIKE N''CHMK'') OR (AlarmCode LIKE N''CLMK'') OR (AlarmCode LIKE N''CLKU''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Secure-specific alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''MKOK'') OR (AlarmCode LIKE N''MKFL'') OR (AlarmCode LIKE N''LMKT'') OR (AlarmCode LIKE N''LKUR'') OR (AlarmCode LIKE N''HMKT'') OR (AlarmCode LIKE N''CONF'') OR (AlarmCode LIKE N''CHMK'') OR (AlarmCode LIKE N''CLMK'') OR (AlarmCode LIKE N''CLKU''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - ID Access system alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'DRAC,DRFC,DRFS,DRHC,DRHS,DROC,DROS,DRSC,DRSF,DRVS', N'*', N'*', N'963 - ID Access system alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''DRVS'') OR (AlarmCode LIKE N''DRSF'') OR (AlarmCode LIKE N''DRSC'') OR (AlarmCode LIKE N''DROS'') OR (AlarmCode LIKE N''DROC'') OR (AlarmCode LIKE N''DRHS'') OR (AlarmCode LIKE N''DRHC'') OR (AlarmCode LIKE N''DRFS'') OR (AlarmCode LIKE N''DRFC'') OR (AlarmCode LIKE N''DRAC''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - ID Access system alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''DRVS'') OR (AlarmCode LIKE N''DRSF'') OR (AlarmCode LIKE N''DRSC'') OR (AlarmCode LIKE N''DROS'') OR (AlarmCode LIKE N''DROC'') OR (AlarmCode LIKE N''DRHS'') OR (AlarmCode LIKE N''DRHC'') OR (AlarmCode LIKE N''DRFS'') OR (AlarmCode LIKE N''DRFC'') OR (AlarmCode LIKE N''DRAC''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Loop failed alarms')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'SDEV', N'*', N'*', N'963 - Loop failed alarms', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''SDEV''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Loop failed alarms')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''SDEV''))')
	END

	IF NOT EXISTS (SELECT Title FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Loop OK')
	BEGIN
		INSERT INTO [i96X].[dbo].[ExtendedAlarmFilters]([ConnectionString], [Lan], [Os], [AlarmCode], [AlarmText], [Item], [Title],[Priority], [ExcludeMode],[FilterSetAlarms], [FilterClearAlarms])
		VALUES (N'*', N'*', N'*', N'CSDV', N'*', N'*', N'963 - Loop OK', N'*', 0, 1, 1)

		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@@IDENTITY ,N'((AlarmCode LIKE N''CSDV''))')
	END
	ELSE
	BEGIN
		SET @extendedFilterID = (SELECT theIndex FROM [i96X].[dbo].[ExtendedAlarmFilters] WHERE Title = N'963 - Loop OK')

		IF NOT EXISTS (SELECT extendedAlarmFilterID FROM [i96X].[dbo].[AlarmFilterSQL] WHERE extendedAlarmFilterID = @extendedFilterID)
		INSERT INTO [i96X].[dbo].[AlarmFilterSQL] ([extendedAlarmFilterID] ,[filterSQL])
		VALUES (@extendedFilterID ,N'((AlarmCode LIKE N''CSDV''))')
	END

	--
	-- insert default pre-configured alarm groups
	--

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - 963 Secure specific')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - 963 Secure specific', N'', 0, 255, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - User activity (login/logout/adjustments)')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - User activity (login/logout/adjustments)', N'', 0, 255, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - Strategy specific')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - Strategy specific', N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - Network communication')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - Network communication', N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - Device specific')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - Device specific', N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - Critical alarms')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - Critical alarms', N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - Scheduled action failed')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - Scheduled action failed', N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	IF NOT EXISTS (SELECT title FROM [i96X].[dbo].[AlarmGroup] WHERE title = N'963 - Alarm retransmission failure')
	INSERT INTO [i96X].[dbo].[AlarmGroup]([backgroundColour], [diaryGroupID], [displayMsg], [actionWhenOcc], [actionWhenNoc], [title], [wavForWrkgrp], [DisplayPanel], [PanelColour], [PrintOptionsUpdated], [PrintAlarms], [PrintWhat], [PanelPosX], [PanelPosY], [BeepPanel], [userCommand])
	VALUES(255, -1, 0, N'', N'', N'963 - Alarm retransmission failure', N'', 1, 33023, 1, 1, N'<LABEL><TAB><ALARMDESC><TAB><TIME>  Site: <SITE><TAB>LAN: <LANLABEL><TAB>OS: <OSLABEL>  <TELE>L<LAN>O<OS> <MODULE> <ALARMCODE>', 0, 0, 0, N'')

	--
	-- inserts into AlarmFilterToAlarmGroup for pre-configured alarm filters and alarm groups
	--

	DECLARE @alarmGroupID int
	-- DECLARE @extendedFilterID int

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - 963 Secure specific')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Secure-specific alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - User activity (login/logout/adjustments)')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - User adjustments')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - User login/logout')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Startup/shutdown')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Strategy specific')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Sensor Alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Driver Alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Digital Input Alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Loop failed alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Loop OK')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Network communication')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Network Alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Device specific')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - General controller faults')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Autodialler alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - ID Access system alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Network communication')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Network Alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Critical alarms')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Critical Alarms')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Scheduled action failed')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Diary download failed')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Data logging failed')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Scheduler action failed')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--

	-- assign alarm filters to this alarm group
	SELECT @alarmGroupID = (SELECT theIndex FROM AlarmGroup WHERE title = N'963 - Alarm retransmission failure')

	SELECT @extendedFilterID = (SELECT theIndex FROM ExtendedAlarmFilters WHERE Title = N'963 - Alarm retransmission failure')
	IF NOT EXISTS (SELECT alarmGroupID FROM AlarmFilterToAlarmGroupLink WHERE alarmGroupID = @alarmGroupID AND extendedFilterID = @extendedFilterID)
	INSERT INTO [i96X].[dbo].[AlarmFilterToAlarmGroupLink]([alarmGroupID], [extendedFilterID])
	VALUES(@alarmGroupID, @extendedFilterID)
	PRINT	@alarmGroupID
	PRINT	@extendedFilterID
	--
END
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO



