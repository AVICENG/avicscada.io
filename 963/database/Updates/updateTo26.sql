--
-- addition of id columns to users table to keep number of password retries for individual users
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS ON 
GO

ALTER TABLE [<96XDBNAME>].[dbo].[Users]
ADD [loginAttempts] int DEFAULT (0) NOT NULL

GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO

--ALTER TABLE [i96X].[dbo].[Users] DROP COLUMN [loginAttempts]