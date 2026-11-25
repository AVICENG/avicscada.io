USE <96XDBNAME>
GO

--
-- TAG_ALARM_SCRIPT
-- 963 V3.20
-- REFERENCE: MoSCoW ID DH5C7A
-- 4 DEC 2008
-- Add new alarm code DVMS (DeVice MiSsing)
-- Add new alarm code DVNW (DeVice NeW)
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT Lookup.AlarmCode FROM Lookup WHERE Lookup.AlarmCode = N'DVMS')
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
			(N'DVMS',
			N'Device Missing',
			0,
			0,
			1,
			-1,
			N'',
			NULL,
			30789)
GO

IF NOT EXISTS (SELECT Lookup.AlarmCode FROM Lookup WHERE Lookup.AlarmCode = N'DVNW')
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
			(N'DVNW',
			N'Device New',
			0,
			0,
			1,
			-1,
			N'',
			NULL,
			30790)
GO

SET QUOTED_IDENTIFIER OFF
GO




