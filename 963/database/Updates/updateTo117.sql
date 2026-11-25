USE <96XDBNAME>
--USE [i96X]
GO

--
-- 963 version: v3.60
-- Description: Create a new table WorkgroupsToDiaryGroupLink
--

-- Create Temp table to store errors from this script
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

CREATE TABLE ##ScriptErrorLog( [ErrorCode] [int] NOT NULL) ON [PRIMARY]
GO


-- Encapsulate the whole script into one transaction
BEGIN TRAN Script_TRAN
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[WorkgroupsToDiaryGroupLink]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[WorkgroupsToDiaryGroupLink](
	[WorkgroupLabel] [nvarchar](255) NOT NULL,
	[DiaryGroupID] [int] NOT NULL,	
	CONSTRAINT [PK_WorkgroupsToDiaryGroupLink] PRIMARY KEY CLUSTERED 
(
	[WorkgroupLabel], [DiaryGroupID]
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]

ALTER TABLE [dbo].[WorkgroupsToDiaryGroupLink]  WITH CHECK ADD  CONSTRAINT [FK_WorkgroupsToDiaryGroupLink_DiaryGroups] FOREIGN KEY([DiaryGroupID])
REFERENCES [dbo].[DiaryGroups] ([theIndex])
ON DELETE CASCADE


ALTER TABLE [dbo].[WorkgroupsToDiaryGroupLink] CHECK CONSTRAINT [FK_WorkgroupsToDiaryGroupLink_DiaryGroups]

EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Links diary groups from DiaryGroups table to diary groups in WorkgroupsToDiaryGroupLink table' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'WorkgroupsToDiaryGroupLink', @level2type=N'CONSTRAINT',@level2name=N'FK_WorkgroupsToDiaryGroupLink_DiaryGroups'

ALTER TABLE [dbo].[WorkgroupsToDiaryGroupLink]  WITH CHECK ADD  CONSTRAINT [FK_WorkgroupsToDiaryGroupLink_Workgroups] FOREIGN KEY([WorkgroupLabel])
REFERENCES [dbo].[Workgroups] ([theLabel])
ON DELETE CASCADE

ALTER TABLE [dbo].[WorkgroupsToDiaryGroupLink] CHECK CONSTRAINT [FK_WorkgroupsToDiaryGroupLink_Workgroups]

EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Links work groups from Workgroups table to work groups in WorkgroupsToDiaryGroupLink table' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'WorkgroupsToDiaryGroupLink', @level2type=N'CONSTRAINT',@level2name=N'FK_WorkgroupsToDiaryGroupLink_Workgroups'

END

GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO
-- sample code ends

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code ends here
--///////////////////////////////////////////////////////////////////////////////////


-- at the end of whole script code, check the execution status of this sql script
-- commit transaction if successful and log the Success message into 963 version table
-- otherwise roll back the transaction and log the failure message into 963 version table

DECLARE @VersionNumber int
SET @VersionNumber = (SELECT TOP 1 VersionNum FROM Version ORDER BY VersionNum DESC)

IF ( (SELECT COUNT(ErrorCode) FROM  ##ScriptErrorLog WHERE ErrorCode != 0) > 0)
BEGIN
	-- script failed
	-- Update Version table in 963 database with script execution end date and success status
	-- and roll back the transaction
	ROLLBACK TRAN Script_TRAN
	PRINT N'Script Failed'

	UPDATE Version SET RunFinished = GETDATE(), Result = N'Failed' WHERE VersionNum = @VersionNumber
END
ELSE
BEGIN
	-- script successful
	-- Update Version table in 963 database with script execution end date and success status
	-- and commit the transaction
	COMMIT TRAN Script_TRAN
	PRINT N'Script Successful'
	
	UPDATE Version SET RunFinished = GETDATE(), Result = N'Success' WHERE VersionNum = @VersionNumber
END
GO

-- delete temp error log table
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

GO