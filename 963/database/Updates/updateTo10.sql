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

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_AddHOAStates]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_AddHOAStates]
GO

CREATE PROCEDURE [dbo].[usp_AddHOAStates]

AS

BEGIN
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N' HOA',N'HOA Override',1,1,1,3,N'D',NULL,41531)	
	
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CHOA',N'Clear HOA Override',0,0,1,3,N'D',@@identity,41532)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N' SWO',N'Software Override',1,1,1,2,N'?',NULL,41533)

	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
	VALUES(N'CSWO',N'Clear Software Override',0,0,1,2,N'?',@@identity,41534)

END
GO

exec [dbo].[usp_AddHOAStates]
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO