USE <96XDBNAME>
GO

--
-- TAG_ALARM_SCRIPT
-- Creation date: 13 May 2008
-- Creation/Modification of BBUF alarm code for attribute alarm
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT Lookup.AlarmCode FROM Lookup WHERE Lookup.AlarmCode = N'BBUF')
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
			(N'BBUF',
			N'Log buffer ready',
			0,
			1,
			1,
			0,
			N'P',
			NULL,
			189)
GO

-- if already exists then modify the attribute lookup parameters
UPDATE [i96X].[dbo].[Lookup]
SET
[attributeCodeLookup] = 0,
[attributeCodeLookupItem] = N'P'
WHERE [AlarmCode] = N'BBUF'

GO

SET QUOTED_IDENTIFIER OFF
GO




