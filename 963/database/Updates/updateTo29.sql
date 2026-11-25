--
-- addition of new one off exception column to DiaryDays table
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS ON 
GO

ALTER TABLE [<96XDBNAME>].[dbo].[DiaryDays]
ADD [oneOffException] bit DEFAULT (0) NOT NULL

GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO
