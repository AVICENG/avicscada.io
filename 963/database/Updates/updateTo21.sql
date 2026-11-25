--
-- TAG_ALARM_SCRIPT
-- addition of new entries into lookup table for H/O/A states
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF
GO
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKDA',N'Network duplicate address found',0,0,1,-1,N'',NULL,41433)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKSV',N'Network Service PIN',0,0,1,-1,N'',NULL,41434)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKHD',N'Deaf Ethernet node',0,0,1,-1,N'',NULL,41435)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKUR',N'Unreachable Ethernet node',0,0,1,-1,N'',NULL,41436)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKBL',N'Battery Low',0,0,1,-1,N'',NULL,41437)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKFL',N'Network failed',0,0,1,-1,N'',NULL,41438)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKAA',N'DHCP System switched to auto-addressing',0,0,1,-1,N'',NULL,41439)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'NKAL',N'DHCP system switched to link-local mode',0,0,1,-1,N'',NULL,41440)
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO