USE <96XDBNAME>
GO

SET QUOTED_IDENTIFIER ON 
GO
SET ANSI_NULLS ON 
GO

--
-- make the password and user name case sensitive
-- required to implement MD5 hash algorithm
--

ALTER TABLE UserPasswords
    ALTER COLUMN [username] nvarchar(255)
    COLLATE Latin1_General_CS_AS 
GO 

ALTER TABLE UserPasswords
    ALTER COLUMN [Password] nvarchar(255) 
    COLLATE Latin1_General_CS_AS 

GO

ALTER TABLE [dbo].[Users]DROP CONSTRAINT [PK_Users]
GO

ALTER TABLE Users
    ALTER COLUMN [theLabel] nvarchar(255) COLLATE Latin1_General_CS_AS NOT NULL
GO

ALTER TABLE [dbo].[Users] ADD CONSTRAINT [PK_Users] PRIMARY KEY CLUSTERED 
(
	[theLabel] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]



SET QUOTED_IDENTIFIER OFF 
GO
SET ANSI_NULLS ON 
GO


--
-- Temp Test
--

	-- select * from UserPasswords
	-- select * from UserPasswords where [username] = N'System Administrator'
	-- select * from UserPasswords where [username] = N'system administrator'

	-- EXEC sp_help 'UserPasswords'

	-- Column Name = username
	-- Collation = SQL_Latin1_General_CP1_CI_AS
	
	-- Column Name = Password
	-- Collation = SQL_Latin1_General_CP1_CI_AS
