USE <96XDBNAME>
--USE i96X
GO

--
-- TAG_ALARM_SCRIPT
-- 30 Jan 2009
-- MoSCoW Ref: SA5A2E
-- 963 v3.20
-- New alarm codes for IQEYE
-- total 41
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CDBN')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CDBN', N'Created new DB', 0, 0, 1, -1, N'', NULL, 33006)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CFBD')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CFBD', N'Config Backup File Error', 0, 0, 1, -1, N'', NULL, 33007)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CFGC')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CFGC', N'Config Copied from CF Card', 0, 0, 1, -1, N'', NULL, 33008)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CFGE')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CFGE', N'Config File Error', 0, 0, 1, -1, N'', NULL, 33009)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CFGL')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CFGL', N'New Config Loaded', 0, 0, 1, -1, N'', NULL, 33010)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CFGR')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CFGR', N'Config Rollback OK', 0, 0, 1, -1, N'', NULL, 33011)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CINH')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CINH', N'Collector Inhibited', 0, 0, 1, -1, N'', NULL, 33012)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'CONL')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'CONL', N'Collector Online', 0, 0, 1, -1, N'', NULL, 33013)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'F_CF')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'F_CF', N'CF Card Failure', 0, 0, 1, -1, N'', NULL, 33014)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'F_DB')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'F_DB', N'Database Failure', 0, 0, 1, -1, N'', NULL, 33015)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'F_OF')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'F_OF', N'OS Reload Reqd (OF)', 0, 0, 1, -1, N'', NULL, 33016)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'F_RS')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'F_RS', N'OS Reload Reqd (RS)', 0, 0, 1, -1, N'', NULL, 33017)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FACT')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FACT', N'Actions Failure', 0, 0, 1, -1, N'', NULL, 33018)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FACW')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FACW', N'Action Wdog Reset', 0, 0, 1, -1, N'', NULL, 33019)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FBAT')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FBAT', N'Battery Failure', 0, 0, 1, -1, N'', NULL, 33020)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FCMW')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FCMW', N'Comms Wdog Reset', 0, 0, 1, -1, N'', NULL, 33021)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FCOM')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FCOM', N'No Comms Connection', 0, 0, 1, -1, N'', NULL, 33022)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDB1')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDB1', N'Unrecoverable Database Error', 0, 0, 1, -1, N'', NULL, 33023)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDB2')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDB2', N'Recoverable Database Error', 0, 0, 1, -1, N'', NULL, 33024)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDBC')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDBC', N'Database Corrupted', 0, 0, 1, -1, N'', NULL, 33025)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDBN')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDBN', N'Unable to Recreate DB', 0, 0, 1, -1, N'', NULL, 33026)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDBP')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDBP', N'Database Purge Error', 0, 0, 1, -1, N'', NULL, 33027)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDBW')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDBW', N'Database Wdog Reset', 0, 0, 1, -1, N'', NULL, 33028)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDX1')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDX1', N'Report Creation Failure 1', 0, 0, 1, -1, N'', NULL, 33029)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDX2')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDX2', N'Report Creation Failure 2', 0, 0, 1, -1, N'', NULL, 33030)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDX3')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDX3', N'Report Creation Failure 3', 0, 0, 1, -1, N'', NULL, 33031)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FDXC')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FDXC', N'Report Compression Failure', 0, 0, 1, -1, N'', NULL, 33032)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FFTW')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FFTW', N'Ftp Wdog Reset', 0, 0, 1, -1, N'', NULL, 33033)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FLOG')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FLOG', N'Logging Failure', 0, 0, 1, -1, N'', NULL, 33034)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FMOD')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FMOD', N'Modem Not Responding', 0, 0, 1, -1, N'', NULL, 33035)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FNOC')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FNOC', N'No Comms Data', 0, 0, 1, -1, N'', NULL, 33036)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FNOM')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FNOM', N'No Monitoring Data', 0, 0, 1, -1, N'', NULL, 33037)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'FRAM')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'FRAM', N'OS Reload Reqd (RAM)', 0, 0, 1, -1, N'', NULL, 33038)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'NCFG')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'NCFG', N'No Config File', 0, 0, 1, -1, N'', NULL, 33039)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTA')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTA', N'RESET.COLLECTOR Action', 0, 0, 1, -1, N'', NULL, 33040)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTC')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTC', N'CF Detect Reset', 0, 0, 1, -1, N'', NULL, 33041)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTD')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTD', N'Downgrade Requested', 0, 0, 1, -1, N'', NULL, 33042)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTF')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTF', N'New Config File', 0, 0, 1, -1, N'', NULL, 33043)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTT')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTT', N'Time Changed', 0, 0, 1, -1, N'', NULL, 33044)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTU')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTU', N'Upgrade Requested', 0, 0, 1, -1, N'', NULL, 33045)
GO

IF NOT EXISTS (SELECT dbo.Lookup.AlarmCode FROM dbo.Lookup WHERE dbo.Lookup.AlarmCode = N'RSTZ')
	INSERT INTO [i96X].[dbo].[Lookup] ([AlarmCode],[theDescription],[IsRestorable],[displaysInRed],[alarmRequiresAction],[attributeCodeLookup],[attributeCodeLookupItem],[clearToID],[stringResID])
	VALUES (N'RSTZ', N'Reset Requested', 0, 0, 1, -1, N'', NULL, 33046)
GO


SET QUOTED_IDENTIFIER OFF
GO