--
-- Added new fields to retrieve
-- deviceSubType, DeviCeResponse,FWVersionMajor, FWVersionMinor
--

USE <96XDBNAME>
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/****** Object:  View dbo.LabelsFromController    Script Date: 10/11/2004 15:18:53 ******/
ALTER VIEW [dbo].[LabelsFromController]
AS
SELECT     dbo.StrategyList.theIndex, dbo.Lans.lanID, dbo.Lans.siteID, dbo.Lans.LanNo, dbo.StrategyList.outstationID, dbo.Outstations.NodeAddress, dbo.Outstations.deviceSubType, dbo.Outstations.DeviCeResponse,dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor,
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

SET ANSI_NULLS OFF
GO
SET QUOTED_IDENTIFIER OFF
GO