--
-- at 963 startup make sure that correct data file is in use
--

USE <96XDBNAME>
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_dbInfo]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_dbInfo]
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS OFF 
GO

CREATE  PROCEDURE dbo.usp_dbInfo  AS
BEGIN
	EXEC sp_helpfile
END
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO

