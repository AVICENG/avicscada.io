--
-- count of alarms in the alarm panel hopefully will be same as in database now
--
USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_CountAlarmsForPanel]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_CountAlarmsForPanel]
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS OFF 
GO

CREATE PROCEDURE [dbo].[usp_CountAlarmsForPanel]

@alarmGroupIndex int

AS

BEGIN
	SELECT COUNT( AlarmGroupIndex)  AS theCount
	FROM dbo.AlarmsToPanelLookup WHERE AlarmGroupIndex = @alarmGroupIndex
END

GO
SET QUOTED_IDENTIFIER OFF 

GO
SET ANSI_NULLS ON 
GO