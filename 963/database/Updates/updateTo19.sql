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

DELETE FROM Lookup WHERE AlarmCode LIKE N'XI_A' OR AlarmCode LIKE N'CXI_'

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'XI1A',N'TCL User-defined alarm occurred',1,1,1,1,N't',NULL,30762)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CXI1',N'TCL User-defined alarm cleared',0,0,1,1,N't',@@identity,30763)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'XI2A',N'TCL User-defined alarm occurred',1,1,1,2,N't',NULL,30762)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CXI2',N'TCL User-defined alarm cleared',0,0,1,2,N't',@@identity,30763)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'XI3A',N'TCL User-defined alarm occurred',1,1,1,3,N't',NULL,30762)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CXI3',N'TCL User-defined alarm cleared',0,0,1,3,N't',@@identity,30763)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'XI4A',N'TCL User-defined alarm occurred',1,1,1,4,N't',NULL,30762)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CXI4',N'TCL User-defined alarm cleared',0,0,1,4,N't',@@identity,30763)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'XI5A',N'TCL User-defined alarm occurred',1,1,1,5,N't',NULL,30762)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CXI5',N'TCL User-defined alarm cleared',0,0,1,5,N't',@@identity,30763)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'XI6A',N'TCL User-defined alarm occurred',1,1,1,6,N't',NULL,30762)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CXI6',N'TCL User-defined alarm cleared',0,0,1,6,N't',@@identity,30763)

GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO