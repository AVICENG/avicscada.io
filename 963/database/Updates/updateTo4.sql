--
-- addition of id columns to Workgroup and Users table for audit trail purpose
--
USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

ALTER TABLE [<96XDBNAME>].[dbo].[Workgroups] ADD [WorkgroupID] [int] IDENTITY (1, 1) NOT NULL
GO
ALTER TABLE [<96XDBNAME>].[dbo].[Users] ADD [UserID] [int] IDENTITY (1, 1) NOT NULL
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

--
--to remove the id columns from workgroup and users
--
--ALTER TABLE [<96XDBNAME>].[dbo].[Workgroups] DROP COLUMN WorkgroupID
--ALTER TABLE [<96XDBNAME>].[dbo].[Users] DROP COLUMN UserID