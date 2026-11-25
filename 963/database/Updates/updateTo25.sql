--
-- TAG_ALARM_SCRIPT
-- addition of new IQ3 general alarm
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF
GO

DELETE FROM Lookup WHERE AlarmCode = N'FLER'

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'FLER',N'File Error',0,0,1,15,N'G',NULL,61449)
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO