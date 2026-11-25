USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: JK778A 
-- 963 version: 963 v3.51 ALPHA - 1
-- Description: Altering the LabelsFromController view to consider only the ASCII characters identifying the module name and module number.
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

ALTER VIEW [dbo].[LabelsFromController]
AS
SELECT     dbo.StrategyList.theIndex, dbo.Lans.lanID, dbo.Lans.siteID, dbo.Lans.LanNo, dbo.StrategyList.outstationID, dbo.Outstations.NodeAddress, 
                      dbo.Outstations.deviceSubType, dbo.Outstations.deviCeResponse, dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, 
                      dbo.SiteDetails.siteConnectionString, dbo.StrategyList.item, LEFT(dbo.StrategyList.item, LEN(dbo.StrategyList.item) - PATINDEX('%[^0-9]%', 
                      REVERSE(dbo.StrategyList.item) COLLATE Latin1_General_Bin) + 1) AS itemtype, CAST(SUBSTRING(dbo.StrategyList.item, LEN(dbo.StrategyList.item) - PATINDEX('%[^0-9]%', 
                      REVERSE(dbo.StrategyList.item) COLLATE Latin1_General_Bin) + 2, 9) AS int) AS itemnum, dbo.StrategyList.theValue, dbo.StrategyList.theStatus, dbo.StrategyList.theLabel, 
                      dbo.StrategyList.theUnits, dbo.StrategyList.thePasswordLevel, dbo.StrategyList.theType, dbo.Outstations.DeviceType, dbo.Outstations.batchMode, 
                      dbo.SiteDetails.siteLabel, dbo.Lans.theLabel AS lanLabel, dbo.Outstations.theLabel AS osLabel
FROM         dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID INNER JOIN
                      dbo.SiteDetails ON dbo.Lans.siteID = dbo.SiteDetails.siteID INNER JOIN
                      dbo.StrategyList ON dbo.Outstations.outstationID = dbo.StrategyList.outstationID
WHERE     (PATINDEX('%[0-9]', dbo.StrategyList.item COLLATE Latin1_General_Bin) > 0)

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