--
-- TAG_ALARM_SCRIPT
-- new alarm codes for BACnet devices
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF
GO

	--
	-- change of bit string
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FBST') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FBST',N'Fault change of bit string',1,1,1,-1,N'',NULL,154)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'RBST') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'RBST',N'Clear fault change of bit string',0,0,1,-1,N'',@@IDENTITY,155)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BBST') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BBST',N'Change of bit string',1,1,1,-1,N'',NULL,156)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'CBST') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'CBST',N'Clear change of bit string',0,0,1,-1,N'',@@IDENTITY,157)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UBST') -- User  acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UBST',N'User acknowledge change of bit string',0,0,1,-1,N'',NULL,158)

	--
	-- change of state
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FCOS') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FCOS',N'Fault change of state',1,1,1,-1,N'',NULL,159)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'RCOS') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'RCOS',N'Clear fault change of state',0,0,1,-1,N'',@@IDENTITY,160)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BCOS') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BCOS',N'Change of state',1,1,1,-1,N'',NULL,161)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'CCOS') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'CCOS',N'Clear change of state',0,0,1,-1,N'',@@IDENTITY,162)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UCOS') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UCOS',N'User acknowledge change of state',0,0,1,-1,N'',NULL,163)

	--
	-- change of value
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FCOV') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FCOV',N'Fault change of value',0,1,1,-1,N'',NULL,164)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BCOV') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BCOV',N'Change of value',0,1,1,-1,N'',NULL,165)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UCOV') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UCOV',N'User acknowledge change of value',0,0,1,-1,N'',NULL,166)

	--
	-- command failure
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FCMF') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FCMF',N'Fault command failure',1,1,1,-1,N'',NULL,167)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'RCMF') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'RCMF',N'Clear fault command failure',0,0,1,-1,N'',@@IDENTITY,168)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BCMF') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BCMF',N'Command failure',1,1,1,-1,N'',NULL,169)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'CCMF') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'CCMF',N'Clear command failure',0,0,1,-1,N'',@@IDENTITY,170)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UCMF') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UCMF',N'User acknowledge command failure',0,0,1,-1,N'',NULL,171)

	--
	-- floating limit
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FFLT') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FFLT',N'Fault floating limit',1,1,1,-1,N'',NULL,172)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'RFLT') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'RFLT',N'Clear fault floating limit',0,0,1,-1,N'',@@IDENTITY,173)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BFLT') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BFLT',N'Floating limit',1,1,1,-1,N'',NULL,174)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'CFLT') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'CFLT',N'Clear floating limit',0,0,1,-1,N'',@@IDENTITY,175)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UFLT') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UFLT',N'User acknowledge floating limit',0,0,1,-1,N'',NULL,176)

	--
	-- out of range
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FOOR') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FOOR',N'Fault value out of range',1,1,1,-1,N'',NULL,177)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'ROOR') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'ROOR',N'Clear fault value out of range',0,0,1,-1,N'',@@IDENTITY,178)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BOOR') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BOOR',N'Value out of range',1,1,1,-1,N'',NULL,179)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'COOR') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'COOR',N'Clear value out of range',0,0,1,-1,N'',@@IDENTITY,180)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BOHI') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BOHI',N'High value out of range',1,1,1,-1,N'',NULL,181)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'COHI') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'COHI',N'Clear high value out of range',0,0,1,-1,N'',@@IDENTITY,182)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BOLO') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BOLO',N'Low value out of range',1,1,1,-1,N'',NULL,183)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'COLO') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'COLO',N'Clear low value out of range',0,0,1,-1,N'',@@IDENTITY,184)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UOOR') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UOOR',N'User acknowledge value out of range',0,0,1,-1,N'',NULL,185)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UOHI') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UOHI',N'User acknowledge high value out of range',0,0,1,-1,N'',NULL,186)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UOLO') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UOLO',N'User acknowledge low value out of range',0,0,1,-1,N'',NULL,187)


	--
	-- log buffer ready
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FBUF') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FBUF',N'Fault log buffer ready',0,1,1,-1,N'',NULL,188)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BBUF') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BBUF',N'Log buffer ready',0,1,1,-1,N'',NULL,189)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UBUF') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UBUF',N'User acknowledge log buffer ready',0,0,1,-1,N'',NULL,190)

	--
	-- change of life safety
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FLIF') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FLIF',N'Fault life safety change',1,1,1,-1,N'',NULL,191)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'RLIF') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'RLIF',N'Clear fault life safety change',0,0,1,-1,N'',@@IDENTITY,192)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BLIF') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BLIF',N'Life safety change',1,1,1,-1,N'',NULL,193)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'CLIF') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'CLIF',N'Clear life safety change',0,0,1,-1,N'',@@IDENTITY,194)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'ULIF') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'ULIF',N'User acknowledge life safety change',0,0,1,-1,N'',NULL,195)

	--
	-- unsigned out of range
	--

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'FUOR') -- Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'FUOR',N'Fault unsigned out of range',1,1,1,-1,N'',NULL,196)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'RUOR') -- Clear Fault alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'RUOR',N'Clear fault unsigned out of range',0,0,1,-1,N'',@@IDENTITY,197)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'BUOR') -- Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'BUOR',N'Unsigned out of range',1,1,1,-1,N'',NULL,198)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'CUOR') -- Clear Set alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'CUOR',N'Clear unsigned out of range',0,0,1,-1,N'',@@IDENTITY,199)

	IF NOT EXISTS (SELECT 1 FROM [Lookup] WHERE [AlarmCode] = N'UUOR') -- User acknowledge alarm
	INSERT INTO Lookup (AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID)
	VALUES(N'UUOR',N'User acknowledge unsigned out of range',0,0,1,-1,N'',NULL,200)

GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO