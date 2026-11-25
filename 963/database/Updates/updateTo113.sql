USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: ST1DDA
-- 963 version: 963 v3.51 WIP-1
-- Description: Add new column isBeingRecorded to PlotDetails table
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

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'PlotDetails' AND COLUMN_NAME = N'isBeingRecorded') )
BEGIN
	ALTER TABLE [dbo].[PlotDetails] ADD [isBeingRecorded] [bit] NOT NULL  DEFAULT 0
END

GO

ALTER VIEW [dbo].[AllDetailsForPlots]

AS
	SELECT

	LFC.[theIndex], LFC.[lanID], LFC.[siteID], LFC.[LanNo], LFC.[outstationID], LFC.[NodeAddress], 
	LFC.[deviceSubType], LFC.[deviCeResponse], LFC.[FWVersionMajor], LFC.[FWVersionMinor], 
	LFC.[siteConnectionString], LFC.[item], LFC.[itemtype], LFC.[itemnum], LFC.[theValue], LFC.[theStatus], LFC.[theLabel], 
	LFC.[theUnits], LFC.[thePasswordLevel], LFC.[theType], LFC.[DeviceType], LFC.[batchMode], 
	LFC.[siteLabel], LFC.[lanLabel], LFC.[osLabel],

	PD.[PlotID],PD.[PointID], PD.[TimingType], PD.[SourceModuleValue], PD.[SourceModuleID], PD.[NumberOfRecords], PD.[LastTotalRecordCount], PD.[TimeOfLastRecord],
	PD.[LoggingInterval], PD.[TimeOfLastDownload], PD.[isBeingRecorded]

	FROM [dbo].[LabelsFromController] LFC INNER JOIN [dbo].[PlotDetails] PD
	ON LFC.[theIndex] = PD.[PointID]


GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO


INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO
-- sample code ends

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