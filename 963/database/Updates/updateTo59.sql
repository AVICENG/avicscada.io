USE <96XDBNAME>
GO

--
-- rename the primary key column from DeviceExtendedParameters.DeviceID to DeviceExtendedParameters.ParameterID
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = N'DeviceExtendedParameters' AND COLUMN_NAME = N'DeviceID') )
BEGIN
	EXEC sp_rename N'DeviceExtendedParameters.DeviceID', N'ParameterID', N'COLUMN';    
END
ELSE
BEGIN
	PRINT N'Column not exists'
END

GO

--
-- alter view [AllDetailsForOutstations]
-- remove the selection offields from DeviceExtendedParameters
-- ParameterName, ParameterValue, ParameterDataType
--

ALTER VIEW [dbo].[AllDetailsForOutstations]
AS
SELECT     dbo.SiteDetails.siteID, dbo.SiteDetails.siteLabel, dbo.SiteDetails.siteConnectionString, dbo.SiteDetails.siteRemoteLAN, dbo.Lans.lanID, 
                      dbo.Lans.LanNo, dbo.Lans.theLabel AS LanLabel, dbo.Outstations.outstationID, dbo.Outstations.NodeAddress, dbo.Outstations.theLabel AS OSLabel, 
                      dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, dbo.Outstations.DeviceType, dbo.Outstations.deviceSubType, 
                      dbo.Outstations.theLabel, dbo.Outstations.outPin, dbo.Outstations.deviCeResponse, dbo.Outstations.nodeIpAddr
FROM         dbo.SiteDetails INNER JOIN
                      dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID ON dbo.SiteDetails.siteID = dbo.Lans.siteID
GO

--
-- alter view [LabelsFromController]
-- remove the selection of fields from DeviceExtendedParameters
-- ParameterName, ParameterValue, ParameterDataType
--


ALTER VIEW [dbo].[LabelsFromController]
AS
SELECT     dbo.StrategyList.theIndex, dbo.Lans.lanID, dbo.Lans.siteID, dbo.Lans.LanNo, dbo.StrategyList.outstationID, dbo.Outstations.NodeAddress, 
                      dbo.Outstations.deviceSubType, dbo.Outstations.deviCeResponse, dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, 
                      dbo.SiteDetails.siteConnectionString, dbo.StrategyList.item, LEFT(dbo.StrategyList.item, LEN(dbo.StrategyList.item) - PATINDEX('%[^0-9]%', 
                      REVERSE(dbo.StrategyList.item)) + 1) AS itemtype, CAST(SUBSTRING(dbo.StrategyList.item, LEN(dbo.StrategyList.item) - PATINDEX('%[^0-9]%', 
                      REVERSE(dbo.StrategyList.item)) + 2, 10) AS int) AS itemnum, dbo.StrategyList.theValue, dbo.StrategyList.theStatus, dbo.StrategyList.theLabel, 
                      dbo.StrategyList.theUnits, dbo.StrategyList.thePasswordLevel, dbo.StrategyList.theType, dbo.Outstations.DeviceType, dbo.Outstations.batchMode, 
                      dbo.SiteDetails.siteLabel, dbo.Lans.theLabel AS lanLabel, dbo.Outstations.theLabel AS osLabel
FROM         dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID INNER JOIN
                      dbo.SiteDetails ON dbo.Lans.siteID = dbo.SiteDetails.siteID INNER JOIN
                      dbo.StrategyList ON dbo.Outstations.outstationID = dbo.StrategyList.outstationID
WHERE     (PATINDEX('%[0-9]', dbo.StrategyList.item) > 0)
GO

--
-- drop and re-create view [PlotsForModuleDetails]
--

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[PlotsForModuleDetails]'))
DROP VIEW [dbo].[PlotsForModuleDetails]
GO

CREATE VIEW [dbo].[PlotsForModuleDetails]
AS
SELECT * FROM dbo.LabelsFromController
	INNER JOIN dbo.PlotsForModule ON dbo.LabelsFromController.theIndex = dbo.PlotsForModule.PointID
GO


SET QUOTED_IDENTIFIER OFF
GO




