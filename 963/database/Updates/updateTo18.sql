--
-- added new field DeviceType to views named dbo.DiaryAllDetailsForUnAllocatedZones and dbo.DiaryAllDetailsForUnAllocatedZoneAllowZoneReuse
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


/****** Object:  View dbo.DiaryAllDetailsForUnAllocatedZones    Script Date: 10/11/2004 15:18:53 ******/
ALTER  VIEW dbo.DiaryAllDetailsForUnAllocatedZones
AS
SELECT     TOP 100 PERCENT dbo.StrategyList.theIndex, dbo.StrategyList.theLabel AS itemLabel, dbo.Outstations.theLabel AS outstationLabel, 
                      dbo.Lans.theLabel AS lanLabel, dbo.SiteDetails.siteLabel, dbo.SiteDetails.siteConnectionString, dbo.Lans.LanNo, dbo.Outstations.NodeAddress, 
                      dbo.StrategyList.item, dbo.Outstations.DeviceType
FROM         dbo.SiteDetails INNER JOIN
                      dbo.Lans ON dbo.SiteDetails.siteID = dbo.Lans.siteID INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID INNER JOIN
                      dbo.StrategyList ON dbo.Outstations.outstationID = dbo.StrategyList.outstationID
WHERE     (dbo.StrategyList.theIndex NOT IN
                          (SELECT     StrategyList.theIndex
                            FROM          DiaryGroupedZones INNER JOIN
                                                   StrategyList ON DiaryGroupedZones.pointID = StrategyList.theIndex
                            WHERE      item LIKE 'Z%')) AND (dbo.StrategyList.item LIKE 'Z%')
ORDER BY dbo.SiteDetails.siteLabel, dbo.Lans.theLabel, dbo.Outstations.theLabel, dbo.StrategyList.theLabel

GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


/****** Object:  View dbo.DiaryAllDetailsForUnAllocatedZoneAllowZoneReuse    Script Date: 10/11/2004 15:18:53 ******/
ALTER  VIEW dbo.DiaryAllDetailsForUnAllocatedZoneAllowZoneReuse
AS
SELECT     TOP 100 PERCENT dbo.StrategyList.theIndex, dbo.StrategyList.theLabel AS itemLabel, dbo.Outstations.theLabel AS outstationLabel, 
                      dbo.Lans.theLabel AS lanLabel, dbo.SiteDetails.siteLabel, dbo.SiteDetails.siteConnectionString, dbo.Lans.LanNo, dbo.Outstations.NodeAddress, 
                      dbo.StrategyList.item, dbo.Outstations.DeviceType
FROM         dbo.SiteDetails INNER JOIN
                      dbo.Lans ON dbo.SiteDetails.siteID = dbo.Lans.siteID INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID INNER JOIN
                      dbo.StrategyList ON dbo.Outstations.outstationID = dbo.StrategyList.outstationID
WHERE     (dbo.StrategyList.item LIKE 'Z%')
ORDER BY dbo.SiteDetails.siteLabel, dbo.Lans.theLabel, dbo.Outstations.theLabel, dbo.StrategyList.theLabel


GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO


