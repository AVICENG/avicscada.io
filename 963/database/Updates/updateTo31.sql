--
-- this view is modified not to display the one off exceptions
--
 
USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


ALTER VIEW [dbo].[DiaryAllExceptionDaysForGroup]
AS
SELECT     dbo.DiaryGroupToDayIdExceptionLink.groupID, dbo.DiaryGroupToDayIdExceptionLink.dayID, dbo.DiaryDays.theLabel, 
           dbo.DiaryDays.displayColour
FROM       dbo.DiaryGroupToDayIdExceptionLink INNER JOIN dbo.DiaryDays 
ON		   dbo.DiaryGroupToDayIdExceptionLink.dayID = dbo.DiaryDays.theIndex
AND			dbo.DiaryDays.oneOffException = 0

GO

GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

