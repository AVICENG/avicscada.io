--USE i96X
USE <96XDBNAME>
GO

--
-- 27 Feb 2009
-- 1. Add new column "TimeMasterStatus" [JB1F52]
-- 2. Modify AllDetailsForOutstationsView to include:
--	2.1 TimeMasterStatus column from OutstationsTable [JB1F52]
--	2.2 overviewDevCommsResponse from OutstationsTable [DH5DEE]
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

--
-- 1. Add TimeMasterStatus column
-- 
IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Outstations' AND COLUMN_NAME = N'TimeMasterStatus') )
BEGIN
	ALTER TABLE [dbo].[Outstations] ADD [TimeMasterStatus] [smallint] NOT NULL  DEFAULT 0
END

GO

--
-- 2 Modify AllDetailsForOutstation View
--	2.1 TimeMasterStatus column from OutstationsTable
--	2.2 overviewDevCommsResponse from OutstationsTable
--
ALTER VIEW [dbo].[AllDetailsForOutstations]
AS
SELECT     dbo.SiteDetails.siteID, dbo.SiteDetails.siteLabel, dbo.SiteDetails.siteConnectionString, dbo.SiteDetails.siteRemoteLAN, dbo.Lans.lanID, 
                      dbo.Lans.LanNo, dbo.Lans.theLabel AS LanLabel, dbo.Outstations.outstationID, dbo.Outstations.NodeAddress, dbo.Outstations.theLabel AS OSLabel, 
                      dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, dbo.Outstations.DeviceType, dbo.Outstations.deviceSubType, 
                      dbo.Outstations.theLabel, dbo.Outstations.outPin, dbo.Outstations.deviCeResponse, dbo.Outstations.nodeIpAddr, dbo.Outstations.PlotsDiscoveryAttempted, dbo.Outstations.overviewDevCommsResponse, dbo.Outstations.TimeMasterStatus
FROM         dbo.SiteDetails INNER JOIN
                      dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID ON dbo.SiteDetails.siteID = dbo.Lans.siteID

GO
					  
					  
SET ANSI_NULLS OFF
GO

SET QUOTED_IDENTIFIER OFF
GO
