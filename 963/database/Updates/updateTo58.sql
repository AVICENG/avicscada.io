USE <96XDBNAME>
GO

--
-- Alter data type from varchar to int for ParameterDataType field
--

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

ALTER TABLE DeviceExtendedParameters
    ALTER COLUMN [ParameterDataType] int NULL
    
GO

SET QUOTED_IDENTIFIER OFF
GO




