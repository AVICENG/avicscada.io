--
-- TAG_ALARM_SCRIPT
-- handle new J module types for DiJita drivers from TOPS mapped devices
--

USE <96XDBNAME>
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

UPDATE Lookup
SET attributeCodeLookupItem = N'D,J'
WHERE attributeCodeLookupItem = N'D'
AND theDescription LIKE N'Driver%'

GO

SET QUOTED_IDENTIFIER OFF
GO