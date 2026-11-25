--
-- Include 2 new parameter columns in the RetransmissionDestinations table
--

USE <96XDBNAME>
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- add new columns into RetransmissionDestinations table; to support extra email parameters

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = 'RetransmissionDestinations' AND COLUMN_NAME = 'parameter9') )
ALTER TABLE RetransmissionDestinations
	ADD parameter9 nvarchar(255) NOT NULL DEFAULT N''
GO

IF NOT EXISTS (
	SELECT COLUMN_NAME
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE (TABLE_NAME = 'RetransmissionDestinations' AND COLUMN_NAME = 'parameter10') )
ALTER TABLE RetransmissionDestinations
	ADD parameter10 nvarchar(255) NOT NULL DEFAULT N''
GO

-- alter the transmission message view 
ALTER VIEW [dbo].[AllDetailsForRetransmissionMessages]
AS
SELECT     TOP 100 PERCENT dbo.RetransmissionTypes.theCommandCode, dbo.RetransmissionDestinations.alternateDestn, 
                      dbo.RetransmissionDestinations.parameter1, dbo.RetransmissionDestinations.parameter2, dbo.RetransmissionDestinations.parameter3, 
                      dbo.RetransmissionDestinations.parameter4, dbo.RetransmissionDestinations.parameter5, dbo.RetransmissionDestinations.parameter6, 
                      dbo.RetransmissionDestinations.parameter7, dbo.RetransmissionDestinations.parameter8, dbo.RetransmissionDestinations.parameter9, 
					  dbo.RetransmissionDestinations.parameter10, dbo.RetransmissionActiveMessages.message, 
                      dbo.RetransmissionActiveMessages.retries, dbo.RetransmissionActiveMessages.nextAttemptAt, dbo.RetransmissionActiveMessages.theInterval, 
                      dbo.RetransmissionDestinations.numberOfRetries, dbo.RetransmissionDestinations.theInterval AS alternateInterval, 
                      dbo.RetransmissionActiveMessages.theIndex, dbo.RetransmissionDestinations.theLabel, 
                      dbo.RetransmissionDestinations.theIndex AS theDestnIndex
FROM         dbo.RetransmissionDestinations INNER JOIN
                      dbo.RetransmissionTypes ON dbo.RetransmissionDestinations.typeID = dbo.RetransmissionTypes.theIndex INNER JOIN
                      dbo.RetransmissionActiveMessages ON dbo.RetransmissionDestinations.theIndex = dbo.RetransmissionActiveMessages.destinationID
WHERE     (dbo.RetransmissionActiveMessages.nextAttemptAt <= GETDATE())
ORDER BY dbo.RetransmissionDestinations.theIndex

GO

SET QUOTED_IDENTIFIER OFF
GO
