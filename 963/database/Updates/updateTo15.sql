USE <96XDBNAME>
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_countAlarmsInLastPeriod]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_countAlarmsInLastPeriod]
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS OFF 
GO


/****** Object:  Stored Procedure dbo.usp_countAlarmsInLastPeriod    Script Date: 10/11/2004 15:18:53 ******/

/*
--
-- this stored procedure counts the total number of alarms during the last hour
-- it counts only TXOK alarms for specified retransmission destination
--
*/

CREATE PROCEDURE usp_countAlarmsInLastPeriod

@theModule NVARCHAR(255), -- identification of retransmission destination .. RT%d where %d is the retransmission destination id
@alarmCode NVARCHAR(255), -- alarm code to be found ... TXOK in this case
@numOfHours INT    -- number of hours to check the alarms

AS

BEGIN

	DECLARE @startTime DATETIME -- The start time from which counting of alarms to be started
	
	--
	-- testing code
	--
	
	-- DECLARE @theModule NVARCHAR(255)
	-- DECLARE @alarmCode NVARCHAR(255)
	-- DECLARE @numOfHours INT
	
	--SET @theModule = N'RT3'
	--SET @alarmCode = N'TXOK'
	--SET @numOfHours = 1
	
	-- Set up the time
	-- start date time and end date time
	-- using the @numofHours parameter
	
	SET @startTime = CONVERT(NVARCHAR(5),DATEPART(yyyy,GETDATE())) + N'-' + CONVERT(NVARCHAR(5),DATEPART(mm,GETDATE()))+ N'-' 
	+ CONVERT(NVARCHAR(5),DATEPART(dd,GETDATE()))+ N' ' + CONVERT(NVARCHAR(5),(CONVERT(int,DATEPART(hh,GETDATE()))-@numOfHours))+ N':' 
	+ CONVERT(NVARCHAR(5),DATEPART(mi,GETDATE()))+ N':' + CONVERT(NVARCHAR(5),DATEPART(ss,GETDATE()))
	
	--PRINT @startTime
	--PRINT GETDATE()
	
	SELECT COUNT(*) AS N'theCount' FROM LastAlarmDetailsByTime
	WHERE (theModule = @theModule AND AlarmCode = @alarmCode) AND
	      ((originalAlarmTime BETWEEN @startTime AND GETDATE()) OR 
	      (clearAlarmTime BETWEEN @startTime AND GETDATE()))

END

GO
SET QUOTED_IDENTIFIER OFF 

GO
SET ANSI_NULLS ON 

GO