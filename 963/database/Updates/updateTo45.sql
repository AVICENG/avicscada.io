USE <96XDBNAME>
GO

--
-- Creation date: 01 May 2008
-- Creation of PlotDetails table
-- to store all the plots detail
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

--
-- Drop all links before dropping and creating new tables
--

IF  EXISTS (SELECT * FROM sys.foreign_keys WHERE object_id = OBJECT_ID(N'[dbo].[FK_PlotDetails_StrategyList]') AND parent_object_id = OBJECT_ID(N'[dbo].[PlotDetails]'))
ALTER TABLE [dbo].[PlotDetails] DROP CONSTRAINT [FK_PlotDetails_StrategyList]
GO

IF  EXISTS (SELECT * FROM sys.foreign_keys WHERE object_id = OBJECT_ID(N'[dbo].[FK_ModuleToPlotLink_PlotDetails]') AND parent_object_id = OBJECT_ID(N'[dbo].[ModuleToPlotLink]'))
ALTER TABLE [dbo].[ModuleToPlotLink] DROP CONSTRAINT [FK_ModuleToPlotLink_PlotDetails]
GO

IF  EXISTS (SELECT * FROM sys.foreign_keys WHERE object_id = OBJECT_ID(N'[dbo].[FK_ModuleToPlotLink_StrategyList]') AND parent_object_id = OBJECT_ID(N'[dbo].[ModuleToPlotLink]'))
ALTER TABLE [dbo].[ModuleToPlotLink] DROP CONSTRAINT [FK_ModuleToPlotLink_StrategyList]
GO

-- Drop table named Plot Details, first check if it does exist

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PlotDetails]') AND type in (N'U'))
DROP TABLE [dbo].[PlotDetails]
GO

CREATE TABLE [dbo].[PlotDetails](
	[PlotID] [int] IDENTITY(1,1) NOT NULL,
	[PointID] [int] NOT NULL,
	[TimingType] [int] NOT NULL,
	[SourceModuleValue] [nvarchar](255) NOT NULL,
	[SourceModuleID] [nvarchar](255) NOT NULL,
	[NumberOfRecords] [int] NOT NULL,
	[LastTotalRecordCount] [bigint] NOT NULL,
	[TimeOfLastRecord] [datetime] NULL,
	[LoggingInterval] [int] NOT NULL,
	[TimeOfLastDownload] [datetime] NULL,
 CONSTRAINT [PK_PlotDetails] PRIMARY KEY CLUSTERED 
(
	[PlotID] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

ALTER TABLE [dbo].[PlotDetails]  WITH CHECK ADD  CONSTRAINT [FK_PlotDetails_StrategyList] FOREIGN KEY([PointID])
REFERENCES [dbo].[StrategyList] ([theIndex])
ON DELETE CASCADE
GO

ALTER TABLE [dbo].[PlotDetails] CHECK CONSTRAINT [FK_PlotDetails_StrategyList]
GO

EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Links Plots from StrategyList table to Plots in PlotsDetail table' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'PlotDetails', @level2type=N'CONSTRAINT',@level2name=N'FK_PlotDetails_StrategyList'
GO

--
-- Creation of ModuleToPlotLink table
-- to store link between Plots from StrategyList table and Plots in PlotDetails table
--

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ModuleToPlotLink]') AND type in (N'U'))
DROP TABLE [dbo].[ModuleToPlotLink]
GO

CREATE TABLE [dbo].[ModuleToPlotLink](
	[ModuleID] [int] NOT NULL,
	[PlotID] [int] NOT NULL,
 CONSTRAINT [IX_ModuleToPlotLink] UNIQUE NONCLUSTERED 
(
	[ModuleID] ASC,
	[PlotID] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

ALTER TABLE [dbo].[ModuleToPlotLink]  WITH CHECK ADD  CONSTRAINT [FK_ModuleToPlotLink_PlotDetails] FOREIGN KEY([PlotID])
REFERENCES [dbo].[PlotDetails] ([PlotID])
ON DELETE CASCADE
GO

ALTER TABLE [dbo].[ModuleToPlotLink] CHECK CONSTRAINT [FK_ModuleToPlotLink_PlotDetails]
GO

ALTER TABLE [dbo].[ModuleToPlotLink]  WITH CHECK ADD  CONSTRAINT [FK_ModuleToPlotLink_StrategyList] FOREIGN KEY([ModuleID])
REFERENCES [dbo].[StrategyList] ([theIndex])
GO

ALTER TABLE [dbo].[ModuleToPlotLink] CHECK CONSTRAINT [FK_ModuleToPlotLink_StrategyList]
GO

--
-- Creation of view named PlotsForModule
--

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[PlotsForModule]'))
DROP VIEW [dbo].[PlotsForModule]
GO

CREATE VIEW [dbo].[PlotsForModule]
AS
SELECT     dbo.ModuleToPlotLink.ModuleID, dbo.PlotDetails.PointID, dbo.PlotDetails.TimingType, dbo.PlotDetails.SourceModuleValue, 
                      dbo.PlotDetails.NumberOfRecords, dbo.PlotDetails.SourceModuleID, dbo.PlotDetails.LastTotalRecordCount, dbo.PlotDetails.TimeOfLastRecord, 
                      dbo.PlotDetails.LoggingInterval, dbo.PlotDetails.TimeOfLastDownload
FROM         dbo.ModuleToPlotLink INNER JOIN
                      dbo.PlotDetails ON dbo.ModuleToPlotLink.PlotID = dbo.PlotDetails.PlotID

GO

--
-- Creation of view named PlotsForModuleDetails
-- this does have all the details about site, lan, outstation etc
--

IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[PlotsForModuleDetails]'))
DROP VIEW [dbo].[PlotsForModuleDetails]
GO

CREATE VIEW [dbo].[PlotsForModuleDetails]
AS
	SELECT * FROM dbo.LabelsFromController
	INNER JOIN dbo.PlotsForModule ON dbo.LabelsFromController.theIndex = dbo.PlotsForModule.PointID

GO







