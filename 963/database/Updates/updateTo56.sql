USE <96XDBNAME>
--USE [i96X]
GO

--
-- This view gives all the plots details, it don't care whther these plots have been associated to some source modules or not
-- if you need association of plots adn modules then, refer to other view named PlotsForModuleDetails
--

/****** Object:  View [dbo].[PlotsForModule]    Script Date: 08/20/2008 12:29:03 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dbo].[AllDetailsForPlots]'))
DROP VIEW [dbo].[AllDetailsForPlots]
GO


CREATE VIEW [dbo].[AllDetailsForPlots]
AS

  SELECT * FROM LabelsFromController INNER JOIN PlotDetails
  ON LabelsFromController.theIndex = PlotDetails.PointID

GO


