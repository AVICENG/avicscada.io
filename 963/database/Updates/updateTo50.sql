USE <96XDBNAME>
--USE [i96X]
GO

--
-- Created new table to stroe device extended parameters, designed to accomodate Novar Logic 1 device params
-- Modified view, added new extended paramters for devcie, modified view is AllDetailsForOutstations, Novar Logic 1
-- Modified view, added new extended paramters for devcie, modified view is LabelsFromController, Novar Logic 1
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DeviceExtendedParameters]') AND type in (N'U'))
DROP TABLE [dbo].[DeviceExtendedParameters]
GO

CREATE TABLE [dbo].[DeviceExtendedParameters](
	[DeviceID] [int] IDENTITY(1,1) NOT NULL,
	[ParameterName] [nvarchar](255) NULL,
	[ParameterValue] [sql_variant] NULL,
	[ParameterDataType] [nvarchar](255) NULL,
	[OutstationID] [int] NOT NULL,
 CONSTRAINT [PK_DeviceExtendedParameters] PRIMARY KEY CLUSTERED 
(
	[DeviceID] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

ALTER TABLE [dbo].[DeviceExtendedParameters]  WITH CHECK ADD  CONSTRAINT [FK_DeviceExtendedParameters_Outstations] FOREIGN KEY([OutstationID])
REFERENCES [dbo].[Outstations] ([outstationID])
ON DELETE CASCADE
GO

ALTER TABLE [dbo].[DeviceExtendedParameters] CHECK CONSTRAINT [FK_DeviceExtendedParameters_Outstations]
GO


--
-- Modified view, added new extended paramters for devcie, modified view is AllDetailsForOutstations, Novar Logic 1
--

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[AllDetailsForOutstations]'))
DROP VIEW [dbo].[AllDetailsForOutstations]
GO

CREATE VIEW [dbo].[AllDetailsForOutstations]
AS
SELECT     dbo.SiteDetails.siteID, dbo.SiteDetails.siteLabel, dbo.SiteDetails.siteConnectionString, dbo.SiteDetails.siteRemoteLAN, dbo.Lans.lanID, 
                      dbo.Lans.LanNo, dbo.Lans.theLabel AS LanLabel, dbo.Outstations.outstationID, dbo.Outstations.NodeAddress, dbo.Outstations.theLabel AS OSLabel, 
                      dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, dbo.Outstations.DeviceType, dbo.Outstations.deviceSubType, 
                      dbo.Outstations.theLabel, dbo.Outstations.outPin, dbo.Outstations.deviCeResponse, dbo.Outstations.nodeIpAddr, 
                      dbo.DeviceExtendedParameters.ParameterName, dbo.DeviceExtendedParameters.ParameterValue, 
                      dbo.DeviceExtendedParameters.ParameterDataType
FROM         dbo.SiteDetails INNER JOIN
                      dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID ON dbo.SiteDetails.siteID = dbo.Lans.siteID LEFT OUTER JOIN
                      dbo.DeviceExtendedParameters ON dbo.Outstations.outstationID = dbo.DeviceExtendedParameters.OutstationID
                      

GO


--
-- Modified view, added new extended paramters for devcie, modified view is LabelsFromController, Novar Logic 1
--

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[LabelsFromController]'))
DROP VIEW [dbo].[LabelsFromController]
GO

CREATE VIEW [dbo].[LabelsFromController]
AS
SELECT     dbo.StrategyList.theIndex, dbo.Lans.lanID, dbo.Lans.siteID, dbo.Lans.LanNo, dbo.StrategyList.outstationID, dbo.Outstations.NodeAddress, 
                      dbo.Outstations.deviceSubType, dbo.Outstations.deviCeResponse, dbo.Outstations.FWVersionMajor, dbo.Outstations.FWVersionMinor, 
                      dbo.SiteDetails.siteConnectionString, dbo.StrategyList.item, LEFT(dbo.StrategyList.item, LEN(dbo.StrategyList.item) - PATINDEX('%[^0-9]%', 
                      REVERSE(dbo.StrategyList.item)) + 1) AS itemtype, CAST(SUBSTRING(dbo.StrategyList.item, LEN(dbo.StrategyList.item) - PATINDEX('%[^0-9]%', 
                      REVERSE(dbo.StrategyList.item)) + 2, 10) AS int) AS itemnum, dbo.StrategyList.theValue, dbo.StrategyList.theStatus, dbo.StrategyList.theLabel, 
                      dbo.StrategyList.theUnits, dbo.StrategyList.thePasswordLevel, dbo.StrategyList.theType, dbo.Outstations.DeviceType, dbo.Outstations.batchMode, 
                      dbo.SiteDetails.siteLabel, dbo.Lans.theLabel AS lanLabel, dbo.Outstations.theLabel AS osLabel, dbo.DeviceExtendedParameters.ParameterName, 
                      dbo.DeviceExtendedParameters.ParameterValue, dbo.DeviceExtendedParameters.ParameterDataType
FROM         dbo.Lans INNER JOIN
                      dbo.Outstations ON dbo.Lans.lanID = dbo.Outstations.lanID INNER JOIN
                      dbo.SiteDetails ON dbo.Lans.siteID = dbo.SiteDetails.siteID INNER JOIN
                      dbo.StrategyList ON dbo.Outstations.outstationID = dbo.StrategyList.outstationID LEFT OUTER JOIN
                      dbo.DeviceExtendedParameters ON dbo.Outstations.outstationID = dbo.DeviceExtendedParameters.OutstationID
WHERE     (PATINDEX('%[0-9]', dbo.StrategyList.item) > 0)

GO





---------------
