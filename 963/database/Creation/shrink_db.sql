-- check the space used by 963 database
USE <96XDBNAME>
exec sp_spaceused
GO

USE master
GO

--DECLARE @spid int
--SELECT spid FROM master.dbo.sysprocesses WHERE DB_NAME(dbid) = N'<96XDBNAME>' AND spid > 50 AND spid <> @@SPID
--SELECT @@SPID
--PRINT @spid

-- detach 963 database
--EXEC sp_detach_db <96XDBNAME>
--GO

-- attach 963 database
--EXEC sp_attach_db <96XDBNAME>, N'C:\963 Enterprise Source Code\Test System\Database\<96XDBNAME>_data.mdf', N'C:\963 Enterprise Source Code\Test System\Database\<96XDBNAME>_log.ldf'
--GO

-- shrik the database data file only to maxmimum possible limit
DBCC SHRINKDATABASE (<96XDBNAME>, 0,TRUNCATEONLY)
GO

USE <96XDBNAME>
GO

-- shrink the 963 log file separately
DBCC SHRINKFILE (<96XDBNAME>_log, 0)
GO

-- shrink the 963 data file separately
DBCC SHRINKFILE (<96XDBNAME>_data, 0)
GO

USE master
GO

-- shrink to leave only 5 % unused free space if already not shrinked to minimum level
DBCC SHRINKDATABASE (<96XDBNAME>, 5)
GO

-- correct inaccuracies in the sysindexes table
DBCC UPDATEUSAGE (N'<96XDBNAME>') WITH NO_INFOMSGS 
GO

USE <96XDBNAME>
GO

-- check the database space after shrink
exec sp_spaceused
GO
