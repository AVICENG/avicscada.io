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

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[usp_checkAndCreateLogin]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[usp_checkAndCreateLogin]
GO


INSERT INTO ##ScriptErrorLog (ErrorCode) VALUES (@@ERROR)
GO

CREATE PROCEDURE [dbo].[usp_checkAndCreateLogin]

@loginName NVARCHAR(255),
@loginPassword NVARCHAR(255)

AS

-- See if the log in exists
SELECT name FROM master..syslogins WHERE name = @loginName

IF @@ROWCOUNT < 1
BEGIN

	-- If the log in does not exist then create it
	PRINT N'Log in NOT found. Adding new user log in'
	
	--EXEC sp_addlogin @loginName, @loginPassword, N'master'	
	
	DECLARE @sqlCommand NVARCHAR(500)	
	
	-- create database login
	SET @sqlCommand = N'CREATE LOGIN TEMP_LOGIN_NAME WITH PASSWORD = N''TEMP_PASSWORD'''
	SET @sqlCommand = REPLACE(@sqlCommand, N'TEMP_LOGIN_NAME', @loginName)
	SET @sqlCommand = REPLACE(@sqlCommand, N'TEMP_PASSWORD', @loginPassword)
	PRINT @sqlCommand
	
	EXECUTE sp_executesql @sqlCommand
	
	-- Grant access to the user to the 963 database
	--EXEC sp_grantdbaccess @loginName, @loginName 
	
	SET @sqlCommand = N'CREATE USER TEMP_USER_NAME FOR LOGIN TEMP_LOGIN_NAME'
	SET @sqlCommand = REPLACE(@sqlCommand, N'TEMP_USER_NAME', @loginName)
	SET @sqlCommand = REPLACE(@sqlCommand, N'TEMP_LOGIN_NAME', @loginName)
	PRINT @sqlCommand
	
	EXECUTE sp_executesql @sqlCommand
	
	PRINT N'Granted access to 963 database'
	
	-- Add the fixed server role to the log in
	EXEC sp_addsrvrolemember @loginName, N'sysadmin'
	PRINT N'Added fixed server role to log in'

END
ELSE
BEGIN
	PRINT N'Log in found'
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