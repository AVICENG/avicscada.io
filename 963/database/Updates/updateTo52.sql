USE <96XDBNAME>
--USE [i96X]
GO

--
-- Modified to get SourceModuleItem from StrategyList along with point id
-- S1, D1 etc
--

/****** Object:  View [dbo].[PlotsForModule]    Script Date: 07/03/2008 15:01:32 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

ALTER VIEW [dbo].[PlotsForModule]
AS
SELECT     dbo.ModuleToPlotLink.ModuleID, dbo.PlotDetails.PointID, dbo.PlotDetails.TimingType, dbo.PlotDetails.SourceModuleValue, 
                      dbo.PlotDetails.NumberOfRecords, dbo.PlotDetails.SourceModuleID, dbo.PlotDetails.LastTotalRecordCount, dbo.PlotDetails.TimeOfLastRecord, 
                      dbo.PlotDetails.LoggingInterval, dbo.PlotDetails.TimeOfLastDownload,
                      dbo.StrategyList.item AS N'SourceModuleItem'			
FROM         dbo.ModuleToPlotLink INNER JOIN dbo.PlotDetails 
			ON dbo.ModuleToPlotLink.PlotID = dbo.PlotDetails.PlotID			
			INNER JOIN dbo.StrategyList ON
			dbo.StrategyList.theIndex = dbo.ModuleToPlotLink.ModuleID



GO


