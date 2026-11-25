--
-- changed to solve problem with finding out the critical alarm module reference from it's text
--

USE <96XDBNAME>
GO

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[usp_queryPointID]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[usp_queryPointID]
GO

SET QUOTED_IDENTIFIER ON 
GO

SET ANSI_NULLS OFF 
GO

CREATE PROCEDURE dbo.usp_queryPointID
@connectionstr NVARCHAR(255),	-- Telephone number or IP address.
@lanaddress INT,			-- LAN address of point
@nodeaddress INT,			-- Outstation address.
@item NVARCHAR(255),			-- Same size as the field in the StrategyList table for safety. it was 50 in old
@pointID INT OUTPUT,			-- Point id as an OUTPUT parameter.
@createifnfound BIT = 0,		-- Boolean specifying whether the site, lan and os records should be created if not found.
@defaultModlabel NVARCHAR(255),		-- Default label when missing records are created, something like 'Unknown'.
@defaultModUnits NVARCHAR(255),		-- Default label when missing records are created, something like 'Unknown'.
@defaultOSlabel NVARCHAR(255),		-- Default label when missing records are created, something like 'Unknown'.
@defaultLANlabel NVARCHAR(255),		-- Default label when missing records are created, something like 'Unknown'.
@defaultSitelabel NVARCHAR(255),		-- Default label when missing records are created, something like 'Unknown'.
@dbname NVARCHAR(123),		-- The name of the database we are trying to use
@isCriticalAlarm BIT, 			-- Whether it is a critical alarm
@theSiteLabel NVARCHAR(255) OUTPUT, -- The site label output
@theLanLabel NVARCHAR(255) OUTPUT, -- The lan label output
@theOsLabel NVARCHAR(255) OUTPUT, -- The outstation label output
@theModuleLabel NVARCHAR(255) OUTPUT, -- The module label output
@theCriticalAlarmModule NVARCHAR(255) OUTPUT -- The critical alarm module associated with this alarm text

AS

-- If the connection string is null, make it an empty string for convenience

SET @connectionstr = COALESCE(@connectionstr, N'')
SET @dbname = COALESCE(@dbname, N'')

SET @pointID = NULL

-- First off, query whether the point 

DECLARE @sqlstr NVARCHAR(4000)

IF (@connectionstr = '')
BEGIN

	SET @sqlstr = N'SELECT <DBNAME>.dbo.StrategyList.theIndex, <DBNAME>.dbo.Lans.lanID, <DBNAME>.dbo.Lans.siteID, <DBNAME>.dbo.Lans.LanNo, <DBNAME>.dbo.StrategyList.outstationID, <DBNAME>.dbo.Outstations.NodeAddress, 
                      <DBNAME>.dbo.SiteDetails.siteConnectionString, <DBNAME>.dbo.StrategyList.item, 
                      <DBNAME>.dbo.StrategyList.theValue, <DBNAME>.dbo.StrategyList.theStatus, <DBNAME>.dbo.StrategyList.theLabel, <DBNAME>.dbo.StrategyList.theUnits, <DBNAME>.dbo.StrategyList.thePasswordLevel, 
                      <DBNAME>.dbo.StrategyList.theType, <DBNAME>.dbo.Outstations.DeviceType,
	        <DBNAME>.dbo.SiteDetails.siteLabel, <DBNAME>.dbo.Lans.theLabel AS lanLabel, <DBNAME>.dbo.Outstations.theLabel AS osLabel 
	         INTO #TempPointTable 
	         FROM         <DBNAME>.dbo.Lans INNER JOIN
                      <DBNAME>.dbo.Outstations ON <DBNAME>.dbo.Lans.lanID = <DBNAME>.dbo.Outstations.lanID INNER JOIN
                      <DBNAME>.dbo.SiteDetails ON <DBNAME>.dbo.Lans.siteID = <DBNAME>.dbo.SiteDetails.siteID INNER JOIN
                      <DBNAME>.dbo.StrategyList ON <DBNAME>.dbo.Outstations.outstationID = <DBNAME>.dbo.StrategyList.outstationID
	WHERE ((siteConnectionString IS NULL) OR (siteConnectionString = '''')) AND (LanNo = @lanaddress) AND (NodeAddress = @nodeaddress) AND (<DBNAME>.dbo.StrategyList.<DBITEM> = @item)

	SELECT @pointID = theIndex, @theSiteLabel = siteLabel, @theLanLabel = lanLabel, @theOsLabel = osLabel, @theModuleLabel = theLabel, @theCriticalAlarmModule  = item FROM #TempPointTable

	DROP TABLE #TempPointTable'

	SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @dbname)

	IF (@isCriticalAlarm = 1)
	BEGIN
		SET @sqlstr = REPLACE(@sqlstr, N'<DBITEM>', N'theLabel')
	END
	ELSE

	BEGIN
		SET @sqlstr = REPLACE(@sqlstr, N'<DBITEM>', N'item')
	END

	EXECUTE sp_executesql @sqlstr,
	N'@pointID INT OUTPUT, @lanaddress INT, @nodeaddress INT, @item NVARCHAR(50), @theSiteLabel NVARCHAR(255) OUTPUT,  @theLanLabel NVARCHAR(255) OUTPUT, @theOsLabel NVARCHAR(255) OUTPUT, @theModuleLabel NVARCHAR(255) OUTPUT,@theCriticalAlarmModule NVARCHAR(255) OUTPUT',
	@pointID OUTPUT, @lanaddress, @nodeaddress, @item, @theSiteLabel OUTPUT, @theLanLabel OUTPUT, @theOsLabel OUTPUT, @theModuleLabel OUTPUT,@theCriticalAlarmModule OUTPUT

END
ELSE
BEGIN
	SET @sqlstr = N'SELECT    <DBNAME>.dbo.StrategyList.theIndex, <DBNAME>.dbo.Lans.lanID, <DBNAME>.dbo.Lans.siteID, <DBNAME>.dbo.Lans.LanNo, <DBNAME>.dbo.StrategyList.outstationID, <DBNAME>.dbo.Outstations.NodeAddress, 
                      <DBNAME>.dbo.SiteDetails.siteConnectionString, <DBNAME>.dbo.StrategyList.item, 
                      <DBNAME>.dbo.StrategyList.theValue, <DBNAME>.dbo.StrategyList.theStatus, <DBNAME>.dbo.StrategyList.theLabel, <DBNAME>.dbo.StrategyList.theUnits, <DBNAME>.dbo.StrategyList.thePasswordLevel, 
                      <DBNAME>.dbo.StrategyList.theType, <DBNAME>.dbo.Outstations.DeviceType,
	        <DBNAME>.dbo.SiteDetails.siteLabel, <DBNAME>.dbo.Lans.theLabel AS lanLabel, <DBNAME>.dbo.Outstations.theLabel AS osLabel 
	         INTO #TempPointTable 
	         FROM         <DBNAME>.dbo.Lans INNER JOIN
                      <DBNAME>.dbo.Outstations ON <DBNAME>.dbo.Lans.lanID = <DBNAME>.dbo.Outstations.lanID INNER JOIN
                      <DBNAME>.dbo.SiteDetails ON <DBNAME>.dbo.Lans.siteID = <DBNAME>.dbo.SiteDetails.siteID INNER JOIN
                      <DBNAME>.dbo.StrategyList ON <DBNAME>.dbo.Outstations.outstationID = <DBNAME>.dbo.StrategyList.outstationID
	WHERE (siteConnectionString = @connectionstr) AND (LanNo = @lanaddress) AND (NodeAddress = @nodeaddress) AND (<DBNAME>.dbo.StrategyList.<DBITEM> = @item)

	SELECT @pointID = theIndex, @theSiteLabel = siteLabel, @theLanLabel = lanLabel, @theOsLabel = osLabel, @theModuleLabel = theLabel, @theCriticalAlarmModule  = item FROM #TempPointTable

	DROP TABLE #TempPointTable'

	SET @sqlstr = REPLACE(@sqlstr, N'<DBNAME>', @dbname)

	IF (@isCriticalAlarm = 1)
	BEGIN
		SET @sqlstr = REPLACE(@sqlstr, N'<DBITEM>', N'theLabel')
	END
	ELSE
	BEGIN
		SET @sqlstr = REPLACE(@sqlstr, N'<DBITEM>', N'item')
	END

	EXECUTE sp_executesql @sqlstr,
	N'@pointID INT OUTPUT, @lanaddress INT, @nodeaddress INT, @item NVARCHAR(50), @theSiteLabel NVARCHAR(255) OUTPUT,  @theLanLabel NVARCHAR(255) OUTPUT, @theOsLabel NVARCHAR(255) OUTPUT, @theModuleLabel NVARCHAR(255) OUTPUT,@theCriticalAlarmModule NVARCHAR(255) OUTPUT, @connectionstr NVARCHAR(255)',
	@pointID OUTPUT, @lanaddress, @nodeaddress, @item, @theSiteLabel OUTPUT, @theLanLabel OUTPUT, @theOsLabel OUTPUT, @theModuleLabel OUTPUT,@theCriticalAlarmModule OUTPUT, @connectionstr
 
END

-- Check whether the point ID was found
-- Only do this check and create if we are working with the main database!

IF (@pointID IS NULL) AND (@createifnfound = 1) AND (@dbname = N'')
BEGIN
	-- Declare and set these values so they are not NULL
	DECLARE @siteIndex int
	SET @siteIndex = 0

	DECLARE @lanIndex int
	SET @lanIndex = 0

	DECLARE @osIndex int
	SET @osIndex = 0

	-- Not found, so add the site, LAN, node and point items if required to do so.

	-- Look for @connectionstr in the site details table. If it is not found... add it

	IF (@connectionstr = N'')
	BEGIN
		SELECT @siteIndex = siteID
		FROM SiteDetails
		WHERE (siteConnectionString = N'') OR (siteConnectionString IS NULL) 
	END
	ELSE
	BEGIN
		SELECT @siteIndex = siteID
		FROM SiteDetails
		WHERE siteConnectionString = @connectionstr
	END

	PRINT N'Point not found creating it on the fly'

	IF @siteIndex = 0
	BEGIN
		-- Insert a new item into the sites table. If the siteConnectionString is NULL or empty, the site type is 0 (local), else it is 1 for
		-- a remote site. Should the remote LAN default to 126??

		DECLARE @remotelan int

		IF (@connectionstr = N'')
		BEGIN
			SET @remotelan = 0
		END
		ELSE
		BEGIN
			SET @remotelan = 126
		END

		INSERT INTO SiteDetails(siteLabel, siteConnectionString, siteRemoteLAN)
		VALUES (@defaultSitelabel, @connectionstr, @remotelan)

		-- Make a note of the index of the newly created record

		SET @siteIndex = @@IDENTITY

		PRINT N'Site index not found. Creating site on the fly'
		
	END

	-- Now look in the lans table for a lan record with the address @lanaddress and the same site id as found above. Add it if it isn't there.

	SELECT @lanIndex = lanID
	FROM Lans
	WHERE (siteID = @siteIndex) AND (LanNo = @lanaddress)

	IF @lanIndex = 0
	BEGIN
		-- Not there, so add a record

		INSERT INTO Lans(siteID, LanNo, DeviceType, theLabel)
		VALUES (@siteIndex, @lanaddress, N'?', @defaultLANlabel)

		-- Make a note of the newly created record

		SET @lanIndex = @@IDENTITY

		PRINT N'Lan index not found. Creating lan on the fly'
	END

	-- Look in the outstations table for a node with the correct site id, lan id and node address

	SELECT @osIndex = outstationID
	FROM Outstations
	WHERE (lanID = @lanIndex) AND (NodeAddress = @nodeaddress)

	IF @osIndex = 0
	BEGIN
		-- Not found, so add it

		INSERT INTO Outstations(lanID, NodeAddress, FWVersionMajor, FWVersionMinor, DeviceType, theLabel, outPin, deviCeResponse, nodeIpAddr)
		VALUES(@lanIndex, @nodeaddress, 0, 0, N'?', @defaultOSlabel, 0, N'?', N'#N/A#')

		SET @osIndex = @@IDENTITY

		PRINT N'Outstation index not found. Creating outstation on the fly'
	END

	-- Now we should have site, lan and outstation indices, insert the new point record


	INSERT INTO StrategyList(outstationID, item, theValue, theStatus, theLabel, theUnits, thePasswordLevel, theType)
	VALUES(@osIndex, @item, N'', N'', @defaultModlabel, @defaultModUnits, 0, 0)

	SET @pointID = @@IDENTITY

	-- Get the labels for the point details
	SELECT @theSiteLabel = siteLabel, @theLanLabel = LanLabel, @theOsLabel =  OSLabel,  @theModuleLabel=PointLabel FROM GetAllLabelsFromPoint WHERE pointID = @pointID

	PRINT N'Created point on the fly'
END
GO

SET QUOTED_IDENTIFIER OFF 
GO

SET ANSI_NULLS ON 
GO