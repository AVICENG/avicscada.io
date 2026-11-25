--
-- Set the maximum limit for SQL Server memory to grow
--

USE master
GO

EXEC sp_configure 'show advanced options',1
GO
RECONFIGURE
GO


EXEC sp_configure 'max server memory', 512
RECONFIGURE
GO
