USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: SA720A
-- Product version: 963 v3.40 ALPHA-2
-- Description: Microsoft has deprecated some of the features and functionality which is being 
-- used by 963. The rcommendation from Microsoft is to remove these deprecated features/APIs/procedures 
-- from your code and replace them with supported ones as the depreated ones will be a part of their 
-- discontinued list from next versions of SQL Server.
--

-- Create Temp table to store errors from this script
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

CREATE TABLE ##ScriptErrorLog( [ErrorCode] [int] NOT NULL) ON [PRIMARY]
GO


-- Encapsulate the whole script into one transaction
BEGIN TRAN Script_TRAN
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code starts here
--///////////////////////////////////////////////////////////////////////////////////

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_setupAlarmLookupTable]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_setupAlarmLookupTable]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_setupAlarmLookupTable] AS

BEGIN TRAN

/*
	Called to set up the default values for the alarm look up table
*/

-- Disable all constraints and triggers
ALTER TABLE Lookup NOCHECK CONSTRAINT all
ALTER TABLE Lookup DISABLE TRIGGER all

-- Delete all data from the Lookup table
DELETE FROM Lookup

-- Allow insert of explicit identities
SET IDENTITY_INSERT Lookup ON

-- Insert all the default alarm codes in the alarm lookup table
INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(1,N' LOW',N'Sensor Low',-1,-1,-1,1,N'S',NULL,41345)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(2,N' O/K',N'Sensor Read Alarm Cleared',0,0,-1,3,N'S',74,41346)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(3,N'945',N'945 Retransmitted Alarm',0,0,-1,-1,N'',3,41347)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(4,N'AANR',N'Autodial Not Responding',-1,-1,-1,-1,N'',NULL,41348)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(5,N'ADJF',N'Adjusment Failed',-1,-1,-1,-1,N'',NULL,41358)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(6,N'ADJU',N'User Adjustment',0,0,-1,-1,N'',5,41349)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(7,N'AONL',N'Autodial On Line',0,0,-1,-1,N'',4,41350)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(8,N'BTNR',N'BT Not Responding',0,0,-1,-1,N'',NULL,41351)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(9,N'CCRI',N'Clear Critical Alarm',0,0,-1,-1,N'',75,41352)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(10,N'CDGT',N'Driver Readback Alarm Cleared',0,0,-1,0,N'D',77,41353)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(11,N'CDI0',N'Clear Digital Input',0,0,-1,0,N'I',24,41354)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(12,N'CDI1',N'Clear Digital Input',0,0,-1,1,N'I',25,41354)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(13,N'CHIH',N'Clear Sensor High Alarm',0,0,-1,0,N'S',52,41355)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(14,N'CHMK',N'Clear High MKT Calculation',0,0,-1,-1,N'',53,41356)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(15,N'CLKU',N'User lockout cleared',0,0,-1,-1,N'',60,41357)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(16,N'CLMK',N'Clear Low MKT Calculation OK',0,0,-1,-1,N'',61,41359)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(17,N'CLOW',N'Clear Sensor Low Alarm',0,0,-1,1,N'S',1,41360)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(18,N'CMNT',N'Driver Maintenance Cleared',0,0,-1,1,N'D',62,41361)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(19,N'CONF',N'Config',0,0,-1,-1,N'',NULL,41362)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(20,N'CONL',N'Clear Controller OnLine',0,0,-1,0,N'G',NULL,41363)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(21,N'COUT',N'Clear Out of limits',0,0,-1,2,N'S',71,41364)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(22,N'CPVF',N'Clear Process Variable Fail',0,0,-1,0,N'L',73,41365)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(23,N'CSDV',N'Clear Set Point Deviation',0,0,-1,1,N'L',76,41366)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(24,N'DI=0',N'Digital Input OFF - should be on',-1,-1,-1,0,N'I',NULL,41367)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(25,N'DI=1',N'Digital Input ON - should be off',-1,-1,-1,1,N'I',NULL,41368)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(26,N'DLFL',N'Data logging failed',-1,-1,-1,-1,N'',NULL,41369)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(27,N'DLOK',N'Data logging OK',0,0,-1,-1,N'',26,41370)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(28,N'DRAC',N'Door Accessed',0,0,-1,-1,N'',NULL,41371)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(29,N'DRFC',N'Door Forced Clear',0,0,-1,-1,N'',30,41372)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(30,N'DRFS',N'Door Forced',-1,-1,-1,-1,N'',NULL,41373)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(31,N'DRHC',N'Door Held Clear',0,0,-1,-1,N'',32,41374)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(32,N'DRHS',N'Door Held',-1,-1,-1,-1,N'',NULL,41375)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(33,N'DROC',N'Door Open Clear',0,0,-1,-1,N'',34,41376)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(34,N'DROS',N'Door Open',-1,-1,-1,-1,N'',NULL,41377)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(35,N'DRSC',N'Door Frame Clear',0,0,-1,-1,N'',36,41378)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(36,N'DRSF',N'Door Frame Fail',-1,-1,-1,-1,N'',NULL,41379)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(37,N'DRVS',N'Door Override',0,0,-1,-1,N'',NULL,41380)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(38,N'DVDD',N'Device Dead',-1,-1,-1,-1,N'',NULL,41381)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(39,N'DVOK',N'Device OK',0,0,-1,-1,N'',38,41382)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(40,N'DYFL',N'Diary download Failed',-1,-1,-1,-1,N'',NULL,41383)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(41,N'DYOK',N'Diary download OK',0,0,-1,-1,N'',40,41384)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(42,N'FDRT',N'Dart chip failed self test',0,0,-1,6,N'G',NULL,41385)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(43,N'FPIA',N'PIA Chip failed self test',0,0,-1,2,N'G',NULL,41386)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(44,N'FPRM',N'PROM chip failed self test',0,0,-1,7,N'G',NULL,41387)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(45,N'FRAM',N'RAM failed self test',0,0,-1,4,N'G',NULL,41388)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(46,N'FREE',N'Free Format Alarm',0,0,-1,-1,N'',NULL,41389)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(47,N'FRTC',N'RTC clock failed',0,0,-1,3,N'G',NULL,41390)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(48,N'FSWR',N'IQ strategy corrupt',0,0,-1,5,N'G',NULL,41391)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(49,N'FTKA',N'Time keeper alarm',0,0,-1,-1,N'',NULL,41392)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(50,N'FTKP',N'Time keeper failed',0,0,-1,-1,N'',NULL,41393)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(51,N'HELP',N'IQ in Help',0,0,-1,1,N'G',NULL,41394)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(52,N'HIGH',N'Sensor High Alarm',-1,-1,-1,0,N'S',NULL,41395)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(53,N'HMKT',N'High MKT Alarm Occurred',-1,-1,-1,-1,N'',NULL,41396)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(54,N'IPHI',N'Input High',-1,-1,-1,-1,N'',NULL,41397)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(55,N'IPLO',N'Input Low',0,0,-1,-1,N'',NULL,41398)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(56,N'IPTP',N'Input Tamper',0,0,-1,-1,N'',NULL,41399)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(57,N'LGOF',N'User logged out',0,0,-1,-1,N'',58,41400)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(58,N'LGON',N'User logged on',-1,-1,-1,-1,N'',NULL,41401)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(59,N'LINR',N'Tele. Line Not responding',0,0,-1,-1,N'',NULL,41402)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(60,N'LKUR',N'User locked out',-1,-1,-1,-1,N'',NULL,41403)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(61,N'LMKT',N'Low MKT Alarm Occurred',-1,-1,-1,-1,N'',NULL,41404)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(62,N'MINT',N'Driver Maintenance Alarm',-1,-1,-1,1,N'D',NULL,41405)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(63,N'MKFL',N'MKT calculation error - see alarm log',-1,-1,-1,-1,N'',NULL,41406)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(64,N'MKOK',N'MKT calculation completed OK',0,0,-1,-1,N'',63,41407)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(65,N'MONR',N'Modem not responding',0,0,-1,-1,N'',NULL,41408)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(66,N'NKBK',N'Network Broken',-1,-1,-1,-1,N'',68,41409)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(67,N'NKCH',N'Network Changed',0,0,-1,-1,N'',NULL,41410)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(68,N'NKOK',N'Network OK',0,0,-1,-1,N'',66,41411)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(69,N'OPOF',N'Output Off',0,0,-1,-1,N'',NULL,41412)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(70,N'OPON',N'Output On',0,0,-1,-1,N'',NULL,41413)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(71,N'OUTL',N'Sensor Out of Limits',-1,-1,-1,2,N'S',NULL,41414)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(72,N'PGNR',N'Pager Not Responding',0,0,-1,-1,N'',NULL,41415)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(73,N'PVFL',N'Process Variable Fail',-1,-1,-1,0,N'L',NULL,41416)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(74,N'READ',N'Sensor Read Alarm',-1,-1,-1,3,N'S',NULL,41417)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(75,N'SCRI',N'Set Critical Alarm',-1,-1,-1,-1,N'',NULL,41418)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(76,N'SDEV',N'Loop Setpoint Deviation Alarm',-1,-1,-1,1,N'L',NULL,41419)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(77,N'SDGT',N'Driver Readback Alarm',-1,-1,-1,0,N'D',NULL,41420)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(78,N'SHDN',N'963 System Shutdown',0,0,-1,-1,N'',79,41421)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(79,N'STUP',N'963 System Startup',-1,-1,-1,-1,N'',NULL,41422)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(80,N'SYST',N'Internal Event',0,0,-1,-1,N'',NULL,41423)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(81,N'TXFL',N'Retransmission Failed',-1,-1,-1,-1,N'',NULL,41424)

INSERT INTO Lookup(theIndex,AlarmCode,theDescription,IsRestorable,displaysInRed,alarmRequiresAction,attributeCodeLookup,attributeCodeLookupItem,clearToID,stringResID) 
VALUES(82,N'TXOK',N'Retransmission OK',0,0,-1,-1,N'',81,41425)

-- Turn off insertation of explicit identities
SET IDENTITY_INSERT Lookup OFF

-- Disable all constraints and triggers
ALTER TABLE Lookup CHECK CONSTRAINT all
ALTER TABLE Lookup ENABLE TRIGGER all

IF @@ERROR <> 0 GOTO anError

COMMIT TRAN

GOTO FINISH

anError:
IF @@TRANCOUNT > 0
BEGIN
	PRINT N'Error adding data to look up table'
	ROLLBACK TRAN
END

FINISH:

GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code ends here
--///////////////////////////////////////////////////////////////////////////////////


-- at the end of whole script code, check the execution status of this sql script
-- commit transaction if successful and log the Success message into 963 version table
-- otherwise roll back the transaction and log the failure message into 963 version table

DECLARE @VersionNumber int
SET @VersionNumber = (SELECT TOP 1 VersionNum FROM Version ORDER BY VersionNum DESC)

IF ( (SELECT COUNT(ErrorCode) FROM  ##ScriptErrorLog WHERE ErrorCode != 0) > 0)
BEGIN
	-- script failed
	-- Update Version table in 963 database with script execution end date and success status
	-- and roll back the transaction
	ROLLBACK TRAN Script_TRAN
	PRINT N'Script Failed'

	UPDATE Version SET RunFinished = GETDATE(), Result = N'Failed' WHERE VersionNum = @VersionNumber
END
ELSE
BEGIN
	-- script successful
	-- Update Version table in 963 database with script execution end date and success status
	-- and commit the transaction
	COMMIT TRAN Script_TRAN
	PRINT N'Script Successful'
	
	UPDATE Version SET RunFinished = GETDATE(), Result = N'Success' WHERE VersionNum = @VersionNumber
END
GO

-- delete temp error log table
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

GO