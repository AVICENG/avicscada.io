--
-- added one more column to select in this view named dbo.DiaryDays.oneOffException
--
 
USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


ALTER VIEW [dbo].[DiaryAllTimesForDay]
AS
SELECT     TOP 100 PERCENT dbo.DiaryDays.theIndex, dbo.DiaryDays.theLabel, dbo.DiaryDays.displayColour, dbo.DiaryDayTimes.theTime, 
                      dbo.DiaryDayTimes.theValue, dbo.DiaryDays.downloaded, dbo.DiaryDayTimes.theIndex AS dayTimeIndex, dbo.DiaryDays.oneOffException
FROM         dbo.DiaryDays INNER JOIN
                      dbo.DiaryDayTimes ON dbo.DiaryDays.theIndex = dbo.DiaryDayTimes.dayID
ORDER BY dbo.DiaryDays.theIndex, dbo.DiaryDayTimes.theTime

GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

