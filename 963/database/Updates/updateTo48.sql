USE <96XDBNAME>
GO

--
-- Update value data type from empty to Integer for value type 10
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

UPDATE [i96X].[dbo].[PointValueTypeLookup]
   SET [ValueDataType] = N'Integer'
 WHERE [ValueType] = 10 AND [ValueName] = N'Any'
GO


