--
-- fix for IQ2 zone day times reload
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


/****** Object:  View dbo.DiaryAllExceptionsInTheNextSixDays    Script Date: 14:23 11/10/2006 ******/

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[DiaryAllExceptionsInTheNextSixDays]') and OBJECTPROPERTY(id, N'IsView') = 1)
drop view [dbo].[DiaryAllExceptionsInTheNextSixDays]
GO

CREATE  VIEW dbo.DiaryAllExceptionsInTheNextSixDays
AS
SELECT     TOP 100 PERCENT dbo.DiaryExceptions.label, dbo.DiaryExceptions.startDate, dbo.DiaryExceptions.groupID, dbo.DiaryExceptions.sameEveryYear, 
                      dbo.DiaryYearlyExceptNextStartAndEnds.currentTime, dbo.DiaryYearlyExceptNextStartAndEnds.startYear, 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart, dbo.DiaryExceptions.theIndex, dbo.DiaryExceptions.downloaded, 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd
FROM         dbo.DiaryYearlyExceptNextStartAndEnds INNER JOIN
                      dbo.DiaryExceptions ON dbo.DiaryYearlyExceptNextStartAndEnds.theIndex = dbo.DiaryExceptions.theIndex
WHERE     (dbo.DiaryExceptions.sameEveryYear = 0) AND (dbo.DiaryYearlyExceptNextStartAndEnds.currentTime BETWEEN dbo.DiaryExceptions.startDate AND 
                      DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 0) AND (DATEADD(day, 1, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryExceptions.startDate AND DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 0) AND (DATEADD(day, 2, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryExceptions.startDate AND DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 0) AND (DATEADD(day, 3, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryExceptions.startDate AND DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 0) AND (DATEADD(day, 4, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryExceptions.startDate AND DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 0) AND (DATEADD(day, 5, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryExceptions.startDate AND DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 0) AND (DATEADD(day, 6, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryExceptions.startDate AND DATEADD(minute, 1435, dbo.DiaryExceptions.endDate)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (dbo.DiaryYearlyExceptNextStartAndEnds.currentTime BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (DATEADD(day, 1, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (DATEADD(day, 2, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (DATEADD(day, 3, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (DATEADD(day, 4, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (DATEADD(day, 5, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd)) OR
                      (dbo.DiaryExceptions.sameEveryYear = 1) AND (DATEADD(day, 6, dbo.DiaryYearlyExceptNextStartAndEnds.currentTime) BETWEEN 
                      dbo.DiaryYearlyExceptNextStartAndEnds.nextStart AND DATEADD(minute, 1435, dbo.DiaryYearlyExceptNextStartAndEnds.nextEnd))
ORDER BY dbo.DiaryExceptions.startDate
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO
