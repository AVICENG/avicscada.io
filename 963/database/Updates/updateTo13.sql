--
-- added to new columns to Workgroup table for additional user access rights
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO


ALTER TABLE Workgroups
	ADD canMenuBar BIT NOT NULL DEFAULT 1
GO

ALTER TABLE Workgroups
	ADD canViewHelp BIT NOT NULL DEFAULT 1
GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO