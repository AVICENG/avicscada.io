--
-- database modification to support different Lan types (see TOPS Lans)
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

-- add new column into Lans table to have sub type

IF NOT EXISTS (  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME = 'Lans' AND COLUMN_NAME = 'deviceSubType') )
ALTER TABLE Lans ADD deviceSubType nvarchar(1) NOT NULL DEFAULT N''
GO

SET QUOTED_IDENTIFIER OFF
GO
