--
-- Create TraceDataTmp table in database
--

USE [i96X]
GO

/****** Object:  Table [dbo].[TraceDataTmp]    Script Date: 04/22/2008 12:15:36 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[TraceDataTmp]') and OBJECTPROPERTY(id, N'IsTable') = 1)
drop table [dbo].[TraceDataTmp]
GO

CREATE TABLE [dbo].[TraceDataTmp](
	[PointID] [int] IDENTITY(1,1) NOT NULL,
	[DataTime] [datetime] NOT NULL,
	[DataValue] [float] NOT NULL
) ON [PRIMARY]

GO

SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO