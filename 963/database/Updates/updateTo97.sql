USE <96XDBNAME>
--USE [i96X]
GO

--
-- MoSCoW Ref: SA720A
-- Product version: 963 v3.40 ALPHA-2
-- Description: Microsoft has deprecated some of the features and functionality which is being 
-- used by 963. The rcommendation from Microsoft is to remove these deprecated features/APIs/procedures 
-- from your code and replace them with supported ones as the depreated ones will be a part of their 
-- discontinued list from next versions of SQL Server.
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

--///////////////////////////////////////////////////////////////////////////////////
-- Your script code starts here
--///////////////////////////////////////////////////////////////////////////////////

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_isDataLoggedForPointID]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_isDataLoggedForPointID]
GO

INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_isDataLoggedForPointID]

@pointID INT,			-- The point ID to check whether there is any data for
@dbname NVARCHAR(123),	-- The db name
@datalogged BIT OUTPUT	-- An output parameter to get the result

AS

--
-- usp_isDataLoggedForPointID - A stored procedure to query whether there is any data logged for the given point id. Returns 1 or 0 in an OUTPUT parameter.
--

-- Please note: any changes made need to be also made in usp_createArchiveDatabase

SET @datalogged = 0

DECLARE @foundID INT -- A temporary variable to hold the index of the first logged value we find for the given point
SET @foundID = -1

-- Look for the first record for this point

DECLARE @sqlstr NVARCHAR(4000)

SET @sqlstr = N'SELECT TOP 1 @foundID = PointID
FROM <DBNAME>.dbo.PointValue WHERE PointID = @pointID'

SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @dbname)

EXECUTE sp_executesql @sqlstr, N'@foundID INT OUTPUT, @pointID INT', @foundID OUTPUT, @pointID

IF (@foundID <> -1)
BEGIN
	-- We found a logged value for this point, so return TRUE

	SET @datalogged = 1
END

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

GO