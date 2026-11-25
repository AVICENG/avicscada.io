--
-- solution of "unable to delete diary exception from diary setup page"
-- removed FK link here, as its required by IQ3 to keep records for FK table
-- even if PK table records have been deleted
--

USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[FK_DiaryExceptionsNumberLookup_DiaryDays]') and OBJECTPROPERTY(id, N'IsForeignKey') = 1)
ALTER TABLE [dbo].[DiaryExceptionsNumberLookup] DROP CONSTRAINT FK_DiaryExceptionsNumberLookup_DiaryDays
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[FK_DiaryGroupToDayIdExceptionLink_DiaryDays]') and OBJECTPROPERTY(id, N'IsForeignKey') = 1)
ALTER TABLE [dbo].[DiaryGroupToDayIdExceptionLink] DROP CONSTRAINT FK_DiaryGroupToDayIdExceptionLink_DiaryDays
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO