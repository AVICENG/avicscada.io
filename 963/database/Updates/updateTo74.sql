--USE i96X
USE <96XDBNAME>
GO

--
-- MOSCOW ID SA5EDA
--
-- Add two new columns into Version table
-- RunFinshed, it will store the end time of script execution
-- Result, it will store the susscess or failure status of the script execution
-- Result column will have values "NA" = results not applicable, "Success" = script ran successfully, "Failed" = script failed
--
-- Modify the name of existing columns
-- modify from runLast to RunStarted
-- modify from fileName to FileName
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- Add two new columns
IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Version' AND COLUMN_NAME = N'RunFinished') )
BEGIN
	ALTER TABLE [dbo].[Version] ADD [RunFinished] [datetime] NULL
END
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = N'Version' AND COLUMN_NAME = N'Result') )
BEGIN
	ALTER TABLE [dbo].[Version] ADD [Result] nvarchar(255) NOT NULL  DEFAULT N'NA'
END
GO

-- Modify the name of existing columns
EXEC sp_rename 'Version.runLast', 'RunStarted', 'COLUMN'
GO

EXEC sp_rename 'Version.versionNum', 'VersionNum', 'COLUMN'
GO

EXEC sp_rename 'Version.fileName', 'FileName', 'COLUMN'
GO
				  
SET ANSI_NULLS OFF
GO

SET QUOTED_IDENTIFIER OFF
GO
