USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref:LT432A, ME716A
-- 963 version: v3.30 ALPHA-4
-- Description: To solve the issue of 963 crash when deleting a point from device viewer which has some associated plots
-- and to delete all the asscoiated RECORD actions from schedular database when deleting a point, device, lan or site
--
-- Drop exisiting FK constraints from ModuleToPlotLink table and create new one with CASCADE to STrategyList table
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- Create Temp table to store errors from this script
IF EXISTS(SELECT * FROM tempdb.dbo.sysobjects WHERE ID = OBJECT_ID(N'tempdb..##ScriptErrorLog'))
DROP TABLE ##ScriptErrorLog
GO

CREATE TABLE ##ScriptErrorLog( [ErrorCode] [int] NOT NULL) ON [PRIMARY]
GO


-- Encapsulate the whole script into one transaction
BEGIN TRAN Script_TRAN
GO

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code starts here
--///////////////////////////////////////////////////////////////////////////////////

-- Drop constratints from ModuleToPlotLink table
IF EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE CONSTRAINT_SCHEMA='dbo' AND CONSTRAINT_NAME='FK_ModuleToPlotLink_PlotDetails' AND TABLE_NAME='ModuleToPlotLink')
BEGIN
  ALTER TABLE [dbo].[ModuleToPlotLink] 
  DROP CONSTRAINT FK_ModuleToPlotLink_PlotDetails
END
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

IF EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE CONSTRAINT_SCHEMA='dbo' AND CONSTRAINT_NAME='FK_ModuleToPlotLink_StrategyList' AND TABLE_NAME='ModuleToPlotLink')
BEGIN
  ALTER TABLE [dbo].[ModuleToPlotLink] 
  DROP CONSTRAINT [FK_ModuleToPlotLink_StrategyList]
END
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

-- Now add new constratints to ModuleToPlotLink table which cascades with StrategyList table
ALTER TABLE [dbo].[ModuleToPlotLink] 
WITH CHECK ADD CONSTRAINT [FK_ModuleToPlotLink_StrategyList] FOREIGN KEY([ModuleID])
REFERENCES [dbo].[StrategyList] ([theIndex])
ON DELETE CASCADE
ON UPDATE CASCADE
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

ALTER TABLE [dbo].[ModuleToPlotLink] CHECK CONSTRAINT [FK_ModuleToPlotLink_StrategyList]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

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

SET ANSI_NULLS OFF
GO
SET QUOTED_IDENTIFIER OFF
GO