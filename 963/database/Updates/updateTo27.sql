--
-- insert default print templates
--

USE <96XDBNAME>

--USE i96X

GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS ON 
GO

	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\Welcome\Trend Print Template.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\Welcome\Trend Print Template.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Graph.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Graph.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative half high ruler.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative half high ruler.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Graph extra large info.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Graph extra large info.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Graph large info.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Graph large info.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative half high.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative half high.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative left.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative left.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative maths grid.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative maths grid.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative ruler.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative ruler.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative standard.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative standard.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative top.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative top.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative top half high.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative top half high.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative top half high ruler.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative top half high ruler.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Informative top ruler.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Informative top ruler.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Just logo.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Just logo.tss')
	
	IF NOT EXISTS (SELECT SchematicPage FROM PrintTemplates WHERE SchematicPage = N'Pages\963 Folder\Print Templates\Just ruler.tss')
	INSERT INTO [i96X].[dbo].[PrintTemplates]([SchematicPage])
	VALUES(N'Pages\963 Folder\Print Templates\Just ruler.tss')

GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO