--USE i96X
USE <96XDBNAME>
GO

--
-- Add new columns in user workgroups table to implement new rights for alarm handling
-- can acknowledge alarms
-- can clear alarms
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Workgroups' AND COLUMN_NAME = N'canClearAlarms') )
BEGIN
	ALTER TABLE [dbo].[Workgroups] ADD [canClearAlarms] [bit] NOT NULL  DEFAULT 0
END

GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Workgroups' AND COLUMN_NAME = N'canAcknowledgeAlarms') )
BEGIN
	ALTER TABLE [dbo].[Workgroups] ADD [canAcknowledgeAlarms] [bit] NOT NULL  DEFAULT 0
END

GO
SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO




