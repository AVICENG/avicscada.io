--USE i96X
USE <96XDBNAME>
GO

--
-- Add new column in outstations table named PlotsDiscoveryAttempted
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


IF NOT EXISTS ( SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = N'Outstations' AND COLUMN_NAME = N'PlotsDiscoveryAttempted') )
BEGIN
	ALTER TABLE [dbo].[Outstations] ADD [PlotsDiscoveryAttempted] [bit] NOT NULL DEFAULT 0
END

GO

--
-- Alter view [AllDetailsForOutstations]
-- include PlotsDiscoveryAttempted in select statement
--

ALTER VIEW [dbo].[AllDetailsForOutstations]
AS
SELECT     dbo.SiteDetails.siteID, dbo.SiteDetails.siteLabel, dbo.SiteDetails.siteConnectionString, dbo.SiteDetails.siteRemoteLAN, dbo.Lans.lanID, 
                      dbo.Lans.LanNo, dbo.Lans.theLabel AS LanLabel, dbo.Outstations.outstationID, dbo.Outstations.NodeAddress, dbo.Outstations.theLabel AS OSLabel, 
                      dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, dbo.Outstations.DeviceType, dbo.Outstations.deviceSubType, 
                      dbo.Outstations.theLabel, dbo.Outstations.outPin, dbo.Outstations.deviCeResponse, dbo.Outstations.nodeIpAddr, dbo.Outstations.PlotsDiscoveryAttempted
FROM         dbo.SiteDetails INNER JOIN
                      dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID ON dbo.SiteDetails.siteID = dbo.Lans.siteID
GO


SET QUOTED_IDENTIFIER OFF
GO
