--
-- This is a template to write update scripts for 963
-- This process applies to all future scripts above updateTo74.sql
-- Note: In your actual script code (see section below) ensure that you log the @@ERROR into temp table i.e. ##ScriptErrorLog
-- at the end of each sql statement
--
--------------------------------------------------------------------------------------
----------------- Guidline to make changes in Alarm database -------------------------
-- 1. Create the new alarm database update file using this template.
-- 2. Do code changes to execute the new database update in BOOL CDatabaseStartup::UpdateDatabaseToLatestVersion() function.
-- 3. Do code changes to execute the new update when clicked on setup tab of Alarm Viewer in void CAlarmsSetupPP::PrepareAlarmUpdateList().
--------------------------------------------------------------------------------------

USE <96XDBNAME>
--USE [i96X]
GO

--
-- 963 version: v3.60
-- Description: Add a new column "canAddRemoveDiaryGroups" to table "Workgroups" default to 0; its value is set to the same with "canConfigureDiaryGroups" when the column is created
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

DECLARE @canAddRemoveDiaryGroupColumnExists BIT
SET @canAddRemoveDiaryGroupColumnExists = 1
IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Workgroups' AND COLUMN_NAME = N'canAddRemoveDiaryGroups') )
BEGIN
	EXECUTE ('ALTER TABLE [dbo].[Workgroups] ADD [canAddRemoveDiaryGroups] [bit] NOT NULL DEFAULT 0')
	EXECUTE ('UPDATE [dbo].[Workgroups] SET [canAddRemoveDiaryGroups] = [canConfigureDiaryGroups]')
	-- Upgrade the existing WorkgroupsToDiaryGroupLink table
	-- If user workgroup has the access to view the diary, associate all the diary group
	-- Else no diary groups will be associated with the user workgroup
	EXECUTE ('INSERT INTO [dbo].[WorkgroupsToDiaryGroupLink]([WorkgroupLabel], [DiaryGroupID]) (SELECT [dbo].[workgroups].[theLabel], [dbo].[DiaryGroups].[theIndex] FROM [dbo].[Workgroups], [dbo].[DiaryGroups] WHERE [dbo].[Workgroups].[canViewDiary] = 1)')
END

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

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