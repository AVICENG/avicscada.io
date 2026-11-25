--
-- no change just alter the same
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


/****** Object:  View dbo.AlarmsForPanelsLink    Script Date: 10/11/2004 15:18:53 ******/
ALTER  VIEW dbo.AlarmsForPanelsLink
AS
SELECT     *
FROM         dbo.LastAlarmDetailsByTime INNER JOIN
             dbo.AlarmsToPanelLookup ON dbo.LastAlarmDetailsByTime.theIndex = dbo.AlarmsToPanelLookup.AlarmIndex
GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

