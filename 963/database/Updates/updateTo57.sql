USE <96XDBNAME>
GO

--
-- TAG_ALARM_SCRIPT
-- Add new alarm code DLGP (data logging gap)
-- Add new alarm code DLRC (Data logging record count)
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT Lookup.AlarmCode FROM Lookup WHERE Lookup.AlarmCode = N'DLGP')
INSERT INTO [i96X].[dbo].[Lookup]
           ([AlarmCode]
           ,[theDescription]
           ,[IsRestorable]
           ,[displaysInRed]
           ,[alarmRequiresAction]
           ,[attributeCodeLookup]
           ,[attributeCodeLookupItem]
           ,[clearToID]
           ,[stringResID])
     VALUES
			(N'DLGP',
			N'Data logging gap',
			0,
			1,
			1,
			-1,
			N'',
			NULL,
			31)
GO

IF NOT EXISTS (SELECT Lookup.AlarmCode FROM Lookup WHERE Lookup.AlarmCode = N'DLRC')
INSERT INTO [i96X].[dbo].[Lookup]
           ([AlarmCode]
           ,[theDescription]
           ,[IsRestorable]
           ,[displaysInRed]
           ,[alarmRequiresAction]
           ,[attributeCodeLookup]
           ,[attributeCodeLookupItem]
           ,[clearToID]
           ,[stringResID])
     VALUES
			(N'DLRC',
			N'Data logging record count',
			0,
			1,
			1,
			-1,
			N'',
			NULL,
			32)
GO

SET QUOTED_IDENTIFIER OFF
GO




