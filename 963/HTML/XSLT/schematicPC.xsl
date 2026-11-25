<?xml version="1.0" encoding="utf-8"?>
<!-- XSLT VERSION 1.01 12 JULY 2006-->
<xsl:stylesheet version = "1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:msxsl = "urn:schemas-microsoft-com:xslt" 
 xmlns:ScriptSupport = "urn:objs"
 xmlns:Filter= "urn:scripts">

	<!-- Main Browser XSLT -->
	<xsl:import href="includeStrings.xsl"/>
	<xsl:import href="includeEnum.xsl"/>

	<!--
	//
	// parameters to be passed in
	//
	-->

	<xsl:param name = "SID" />
	<xsl:param name = "viewedTime" />
	<xsl:param name = "currentUserName" />
	<xsl:param name = "pageName" />
	<xsl:param name = "userPinLevel" />
	<xsl:param name = "userReadOnly" />
	
	<!--
	//
	// main entry point for xsl transformation
	// template to search all the sub elements from xml page
	//
	-->	
	
	<xsl:template match="/">

		<html>
		
			<!--
			//
			// head section of the page 
			// including meta data in it			
			//
			-->	
		
			<xsl:element name = "HEAD">
			
				<xsl:element name = "TITLE">
					<xsl:value-of select = "$pageName">
					</xsl:value-of>
				</xsl:element>
				
				<xsl:element name = "META">
					<xsl:attribute name = "content">
						<xsl:value-of select = "'text/html; charset=iso-8859-1'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "http-equiv">
						<xsl:value-of select = "'Content-Type'">
						</xsl:value-of>
					</xsl:attribute>
				</xsl:element>
				
				<xsl:element name = "STYLE">
					<xsl:attribute name = "type">
						<xsl:value-of select = "'text/css'">
						</xsl:value-of>
					</xsl:attribute>				
				</xsl:element>
				
				<xsl:element name = "LINK">
					<xsl:attribute name = "href">
						<!--<xsl:value-of select = "'/html/images/style_XSL.css'">-->
						<xsl:value-of select = "'/html/images/style.css'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "rel">
						<xsl:value-of select = "'stylesheet'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "type">
						<xsl:value-of select = "'text/css'">
						</xsl:value-of>
					</xsl:attribute>
				</xsl:element>
				
				<xsl:element name = "META">
					<xsl:attribute name = "content">
						<xsl:value-of select = "'Trend Control Systems 963'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "name">
						<xsl:value-of select = "'GENERATOR'">
						</xsl:value-of>
					</xsl:attribute>
				</xsl:element>
				
				<xsl:element name = "link">
					<xsl:attribute name = "rel">
						<xsl:value-of select = "'icon'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "href">
						<xsl:value-of select = "'/html/images/963.ico'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "type">
						<xsl:value-of select = "'image/ico'">
						</xsl:value-of>
					</xsl:attribute>
				</xsl:element>
				
				<xsl:element name = "link">
					<xsl:attribute name = "rel">
						<xsl:value-of select = "'SHORTCUT ICON'">
						</xsl:value-of>
					</xsl:attribute>
					<xsl:attribute name = "href">
						<xsl:value-of select = "'/html/images/963.ico'">
						</xsl:value-of>
					</xsl:attribute>
				</xsl:element>
				
				<xsl:element name = "script">
					<xsl:attribute name = "lang">
						<xsl:value-of select = "'JavaScript'">
						</xsl:value-of>
					</xsl:attribute>					
				</xsl:element>			
				
			</xsl:element>	
		
			<!--
			//
			// body section starts here
			//
			-->	
			
			<body bgcolor = "#ffffff" text = "#000000"  topmargin="4" leftmargin="4" rightmargin="4"> <!-- #FAEBD7 Lavender #e9f1f3-->	
			
				<!--
				//
				// formatting of the top of the page with different 963 bannaers and logos
				// also includes refresh button
				//
				-->
									
				<A NAME="PageTop"></A>				
				<table width="100%" height="72" cellspacing="0" cellpadding="0" border="0" ID="Table4">					
					<tr>
						<td rowspan="2" width="71"><img src="/html/images/963logo.gif" border="0"></img></td>
						<td width = "100%" height="41" colspan="2" bgcolor="#ff6600" valign="middle" align="left">
							<table width="100%" cellspacing="0" cellpadding="0" border = "0">
								<tr>
									<td class="mainlink">
										<A HREF="javascript:location.reload(true)">
											<xsl:element name = "IMG">
												<xsl:attribute name = "SRC">
													<xsl:value-of select = "'/html/images/refresh.gif'" />	
												</xsl:attribute>
												<xsl:attribute name = "BORDER">
													<xsl:value-of select = "'0'" />	
												</xsl:attribute>
												<xsl:attribute name = "ALIGN">
													<xsl:value-of select = "'RIGHT'" />	
												</xsl:attribute>
												<xsl:attribute name = "TITLE">
													<xsl:value-of select = "ScriptSupport:GetString($IDS_REFRESH)" />
												</xsl:attribute>
											</xsl:element>
										</A>
									</td>
								</tr>
							</table>
						</td>
					</tr>				
					<tr>						
						<td style="width: 241;"><img src="/html/images/banner-swish-left.gif"></img></td>
						<td>
							<div class="pageTitle" style="text-align: right;">
								<xsl:value-of select = "$pageName" />
							</div>
						</td>
					</tr>
					
				</table>				
				
				<!--
				//
				// display the current user name and page viewed time
				// at the right top of the page below 963 main banner
				//
				-->
				
				
				<table width="100%" height="20" cellspacing="0" cellpadding="0" border="0">
					<tr align = "right">
						<td align="right">							
							<b>
								<xsl:value-of select = "ScriptSupport:GetString($IDS_USER)"/>
								:
							</b>							
							<xsl:value-of select = "$currentUserName" />
						</td>
					</tr>	
					<tr>	
						<td align="right">							
								<b>							
									<xsl:value-of select = "ScriptSupport:GetString($IDS_VIEWED_AT_XSL)" />
									:								
								</b>
								<xsl:value-of select = "$viewedTime" />
						</td>
					</tr>
					<xsl:if test="$userReadOnly != 0"> <!-- read only web access -->
						<tr>	
							<td align="right">							
									<b>
										<I>
											<xsl:value-of select = "ScriptSupport:GetString($IDS_CANREADWEBACCESS)" />
										</I>								
									</b>
							</td>
						</tr>
					</xsl:if>				
				</table>					
				
				
				<HR />
				<A name = "liveData"></A>
				<xsl:call-template name = "PageNavigation" />
				
				<BR/>
				
				<!--
				//
				// heading of the dynamic data table
				//
				-->			
				<div class="tableTitle">
					<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_LIVEDATA)" />								
				</div>
				
				<!--text to remind the user to refresh browser to update values-->
				
				<div class="helpInformation">
					<xsl:value-of select = "ScriptSupport:GetString($IDS_TEXTMODE_PLEASE_REFRESH_PAGE)" />
				</div>
				
				<!--
				//
				// display the column headings for the dynamic data table
				// a template to fill the table with dynamic data is embedded/called from here
				//
				-->
				
				<table cellpadding="5" ID="DynamicData" width="100%" border="0">
				
					<COLGROUP span="6" width="15"></COLGROUP>
				
					<tr>
						<td class="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_LABEL)" />
						</td>
						<td class="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_VALUE)" />
						</td>
						<td class="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_UNITS)" />
						</td>								
						<td class="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_ALARMCODE)" />
						</td>
						<td class="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_ITEM)" />
						</td>							
						<td class="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_ACTION)" />
						</td>
					</tr>										
					<xsl:apply-templates select = "Schematic/Objects/DynamicObj" />
				</table>				
							
				<!--
					//
					// STATIC ACTIONS - STATIC OBJECTS WITH ACTIONS	
					// Create a table showing only static labels.
					// labels are sorted alphabetically
					//
				-->
				
				<HR />
				<A name = "actions"></A>
				<xsl:call-template name = "PageNavigation" />
				<BR/>
				
				<!--
				//
				// heading of the action data table
				//
				-->			
				<div class="tableTitle">
					<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_ACTIONS)" />								
				</div>
							
				<!--
					//
					// generate action table
					//
				-->
				<TABLE WIDTH="100%" CELLSPACING="2" CELLPADDING="0" BORDER="0">
					<TR>
						<TD CLASS="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_LABEL)" />	
						</TD>
					</TR>
					<xsl:for-each select="Schematic/Objects/StaticObj">
						<xsl:sort select="ToDisplay"/>
						<xsl:choose>
							<xsl:when test = "OnTouch != ''">
								<xsl:if test="$userPinLevel >= @Pin">
									<!--
										// Pin level is appropriate to display
									-->	    
									<xsl:variable name = "actionString" select = "./OnTouch" />							
									<xsl:variable name = "action" select = "Filter:FilterString($actionString)" />		
									<xsl:if test="$userReadOnly = 0">
										<!--
										// 
										//	only show the following if full web access has been granted
										//
										-->
										<xsl:choose>
											<xsl:when test="$action = 'SEND'">
												<xsl:call-template name = "SendTemplate"/>
											</xsl:when>
											<xsl:when test="$action = 'CONFIG'">						
												<xsl:call-template name = "ConfigTemplate"/>
											</xsl:when>
										</xsl:choose>
									</xsl:if>
									<xsl:choose>
										<!--
										// 
										//	Always show
										//
										-->
										<xsl:when test="$action = 'WEB'">
											<xsl:call-template name = "WebTemplate"/>
										</xsl:when>
										<xsl:when test="$action = 'VIEWQUERY'">
											<xsl:call-template name = "ViewQueryTemplate"/>
										</xsl:when>
										<xsl:when test="$action = 'LOGOUT'">
											<xsl:call-template name = "LogoutTemplate"/>
										</xsl:when>			
										<xsl:when test="$action = 'LOGINAS'">
											<xsl:call-template name = "LoginAsTemplate"/>
										</xsl:when>			
										<xsl:when test="$action = 'GOTO'">					
											<xsl:call-template name = "GotoTemplate"/>
										</xsl:when>				
									</xsl:choose>	
								</xsl:if>
							</xsl:when>						
						</xsl:choose>
					</xsl:for-each>
				</TABLE>
				<HR />
			
				
				<A NAME="labels"></A>
				<xsl:call-template name = "PageNavigation" />
				<BR/>
				
				<!--
				//
				// heading of additional information
				//
				-->			
				<div class="tableTitle">
					<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_ADDITIONALINFO)" />								
				</div>
				
				<!--
					//
					// STATIC LABELS - STATIC OBJECTS WITHOUT ACTIONS
					// Create a table showing only static labels (any static objects without actions)
					//
				-->
				<TABLE WIDTH="100%" CELLSPACING="2" CELLPADDING="0" BORDER="0">
					<TR>
						<TD CLASS="heading">
							<xsl:value-of select = "ScriptSupport:GetString($IDS_LABEL)" />	
						</TD>
					</TR>
					<xsl:for-each select="Schematic/Objects/StaticObj">
						<xsl:sort select="ToDisplay"/>
						<xsl:choose>
							<xsl:when test = "OnTouch = ''">
								
								<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
								<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
								<xsl:variable name = "actionString" select = "./OnTouch"/>
								<xsl:variable name = "strResult" select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)" />
							
								<xsl:choose>
									<xsl:when test = "$strResult != ''">
										<TR>
											<TD CLASS="data">
												<xsl:value-of select="$strResult"></xsl:value-of>												
											</TD>
										</TR>
									</xsl:when>
								</xsl:choose>
								
							</xsl:when>
						</xsl:choose>
					</xsl:for-each>
				</TABLE>
				<HR />
				
				<xsl:call-template name = "PageNavigation" />
				
				<BR />
				
				<!--
				//
				// applet code goes here
				// it is used to keep the logout status of the current user
				// even when closed from explorer close button
				//
				-->
				<xsl:element name = "APPLET">
					<xsl:attribute name = "CODE">
						<xsl:value-of select = "'com.novar.util.login.SessionApplet.class'">
						</xsl:value-of>						
					</xsl:attribute>
					<xsl:attribute name = "CODEBASE">
						<xsl:value-of select = "'/html/java/'">
						</xsl:value-of>						
					</xsl:attribute>
					<xsl:attribute name = "ARCHIVE">
						<xsl:value-of select = "'sessionapplet.jar'">
						</xsl:value-of>						
					</xsl:attribute>
					<xsl:attribute name = "WIDTH">
						<xsl:value-of select = "0">
						</xsl:value-of>						
					</xsl:attribute>
					<xsl:attribute name = "HEIGHT">
						<xsl:value-of select = "0">
						</xsl:value-of>						
					</xsl:attribute>

					<xsl:element name = "param">						
						<xsl:attribute name = "name">
							<xsl:value-of select = "'session.token'">
							</xsl:value-of>						
						</xsl:attribute>
						<xsl:attribute name = "value">
							<xsl:value-of select = "$SID">
							</xsl:value-of>						
						</xsl:attribute>					
					</xsl:element>
					
					<xsl:element name = "param">						
						<xsl:attribute name = "name">
							<xsl:value-of select = "'session.interval'">
							</xsl:value-of>						
						</xsl:attribute>
						<xsl:attribute name = "value">
							<xsl:value-of select = "'30'">
							</xsl:value-of>						
						</xsl:attribute>					
					</xsl:element>
					
				</xsl:element>
				
				<!--
				//
				// formatting of the bottom of the page
				// it includes the bottom line banner, trend logo and different links
				//
				-->
							
				<div align = "right">
					<img src="/html/images/logo.gif" width="141" height="25" align = "right" ></img>
					<br /><br /><br />
					<!--<a href = "http://www.trend-controls.com" align = "right">-->
						<xsl:value-of select = "ScriptSupport:GetString($IDS_COPYRIGHT)" />
					<!--</a>-->
					<br />
					<a href = "/html/WebHelp/963_manu.htm" align = "right">
						<xsl:value-of select = "ScriptSupport:GetString($IDS_VIEW_HELP)" />
					</a>
				</div>
			</body>
		</html>

	</xsl:template>

	<!--
	//
	// template implementation to get and display the dynamic data
	// from xml page generated by 963 application
	//
	-->
	
	<xsl:template match = "Schematic/Objects/DynamicObj">
	
		<tr>
			<xsl:choose>
				<xsl:when test = "substring(@Item,1,1) = 'S'">
					<td class="data" valign="1">
					<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/sensor.gif'"/>
							</xsl:attribute>
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($IDS_SENSOR)" />
							</xsl:attribute>	
						</xsl:element>	
						<xsl:element name="a">
							<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_GRAPHPOINT)" /></xsl:attribute>
							<xsl:attribute name = "href"> 
								<xsl:value-of select = "concat('/GraphRequest?PointRef=',@Tele,'L',@Lan,'O',@Os,@Item,'[-1|0|-1]&amp;SID=',$SID)" />
							</xsl:attribute>
							<xsl:value-of select = "' '" />
							<xsl:value-of select = "@Label" />
						</xsl:element>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'P'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/plots.gif'"/>
							</xsl:attribute>
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($IDS_PLOTS)" />
							</xsl:attribute>	
						</xsl:element>	
						
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				
				<xsl:when test = "substring(@Item,1,1) = 'D'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/driver.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTONDRIVER)" />
							</xsl:attribute>	
						</xsl:element>
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'J'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/driver.gif'" />
							</xsl:attribute>
							
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>
							
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTONDRIVER)" />
							</xsl:attribute>
						</xsl:element>
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>
				</xsl:when>
							
				
				<xsl:when test = "substring(@Item,1,1) = 'K'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/knob.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTONKNOB)" />
							</xsl:attribute>	
						</xsl:element>
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'I'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/digitalinputs.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTONDIGINPUT)" />
							</xsl:attribute>	
						</xsl:element>
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'W'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/switch.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTON_SWITCH)" />
							</xsl:attribute>	
						</xsl:element>
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'Z'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/timezone.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTON_ZONE)" />
							</xsl:attribute>	
						</xsl:element>			
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'X'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/internalsensor.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_INTERNALSENSOR)" />
							</xsl:attribute>	
						</xsl:element>	
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'M'">
					<td class="data">
						<xsl:element name="IMG">
							<xsl:attribute name="SRC">
								<xsl:value-of select = "'/html/images/critcalalarm.gif'" />
							</xsl:attribute>	
							<xsl:attribute name="ALIGN">
								<xsl:value-of select = "'absBottom'" />
							</xsl:attribute>	
							<xsl:attribute name="TITLE">
								<xsl:value-of select = "ScriptSupport:GetString($ID_BUTTON_CRITALARM)" />
							</xsl:attribute>	
						</xsl:element>	
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:when>
				
				<xsl:otherwise>				
					<td class="data">						
						<xsl:value-of select = "' '" />
						<xsl:value-of select = "@Label" />
					</td>			
				</xsl:otherwise>
			</xsl:choose>
					
			<td class="data">
				<xsl:value-of select = "./DynamicModuleStatus/FormattedLatestValue" />
			</td>
			
			<td class="data">
				<xsl:if test = "@Units = ''">	
					<xsl:text>
					...
					</xsl:text>
				</xsl:if>
				
				<xsl:if test = "@Units != ''">	
					<xsl:value-of select = "@Units" />
				</xsl:if>				
			</td>
			
			<!-- display the alarm cell with red background and white text if there is alarm -->
			
			<xsl:variable name = "isAlarm" select = "./DynamicModuleStatus/AlarmText" />
			
			<xsl:if test = "string-length($isAlarm) > 0"> 
				<td bgcolor = "#FF0000">
					<font size="3" color="#FFFFFF"> 
						<img src="/html/images/alarmFlash.gif" align="absBottom" title="Critical Alarm"></img>
						<xsl:value-of select = "' '" />
						<b>
						<xsl:value-of select = "./DynamicModuleStatus/AlarmText" /> 
						</b>
					</font>
				</td>	
			</xsl:if>							
			
			<xsl:if test = "string-length($isAlarm) = 0"> 
				<td class="data">
					<xsl:value-of select = "./DynamicModuleStatus/AlarmText" /> 
				</td>	
			</xsl:if>
						
			<td class="data">
				<xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" />
			</td>	
									
			<td class="data">
				
				<!-- action here ... for the specified item-->
			
				<xsl:if test="$userPinLevel >= @Pin">
					<xsl:choose>
						<xsl:when test = "substring(@Item,1,1) = 'S'">
								<xsl:call-template name = "SensorTemplate" />
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'P'">
							<xsl:call-template name = "PlotTemplate"/>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'D'">
							<xsl:call-template name = "DriverTemplate" />	
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'J'">
							<xsl:call-template name = "DriverTemplate" />	
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'K'">
							<xsl:choose>
								<xsl:when test = "@DeviceType = 'G'">
									<xsl:if test = "@DeviceSubType = 'B'">
										<xsl:call-template name = "BacnetKnobTemplate" />
									</xsl:if>
									<xsl:if test = "@DeviceSubType != 'B'">
										<xsl:call-template name = "KnobTemplate" />
									</xsl:if>
								</xsl:when>
								<xsl:when test = "@DeviceType != 'G'">
									<xsl:call-template name = "KnobTemplate" />
								</xsl:when>
							</xsl:choose>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'I'">
							<xsl:call-template name = "DigitalInputTemplate" />
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'W'">
							<xsl:choose>
								<xsl:when test = "@DeviceType = 'G'">
									<xsl:if test = "@DeviceSubType = 'B'">
										<xsl:call-template name = "BacnetSwitchTemplate" />
									</xsl:if>
									<xsl:if test = "@DeviceSubType != 'B'">
										<xsl:call-template name = "SwitchTemplate" />
									</xsl:if>
								</xsl:when>
								<xsl:when test = "@DeviceType != 'G'">
									<xsl:call-template name = "SwitchTemplate" />
								</xsl:when>
							</xsl:choose>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'Z'">
							<xsl:if test = "@DeviceType = 'G'">
								<xsl:call-template name = "BacnetZoneTemplate" />
							</xsl:if>
							<xsl:if test = "@DeviceType != 'G'">							
								<xsl:call-template name = "ZoneTemplate" />
							</xsl:if>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'X'">
							<xsl:call-template name = "XSensorTemplate" />
						</xsl:when>
						
						<!-- Added to v2.10 BETA7-->
						<xsl:when test = "contains(@Item,'(') and substring(@Item,1,1) = 'B'">
							<xsl:call-template name = "ByteTemplate" />
						</xsl:when>
						<xsl:when test = "substring(@Item,1,1) = 'A'">
							<xsl:call-template name = "AnalogueTemplate" />
						</xsl:when>
						
						<xsl:otherwise>
							<xsl:value-of select = "' '"/>
						</xsl:otherwise>
						
					</xsl:choose>
				</xsl:if>	
			</td>
		</tr>
		
	</xsl:template>
	
	<!--
	//
	// templates implementation for specific dynamic object items
	//
	-->

	<!--
	//
	// SensorTemplate
	//
	-->

	<xsl:template name = "SensorTemplate">
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>

	<!-- Plot template -->
	<xsl:template name = "PlotTemplate">
		<xsl:variable name = "lan" select = "@Lan"/>
		<xsl:variable name = "os" select = "@Os"/>
		<xsl:variable name = "tele" select = "@Tele"/>
		<xsl:variable name = "label" select = "@Label"/>
		<!-- create a seperate table row and form for each plot module associatted with the knob-->
		
		<xsl:for-each select = "./DynamicModuleStatus/plots/plot">
			<table border="0" cellspacing="0" cellpadding="0">
				<tr>
					<NOBR>
						<xsl:if test = "@precision = 'True'" >
							<td class="data" width="20px">
								<xsl:element name = "FORM">
									<xsl:attribute name = "style">margin:0px 10px 0px 0px;</xsl:attribute>
									<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
									<xsl:attribute name = "ACTION"><xsl:value-of select = "'/GraphRequest'" /></xsl:attribute>
								
									<xsl:element name = "INPUT">
										<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16px; HEIGHT: 16px;'" /></xsl:attribute>
										<xsl:attribute name = "src"><xsl:value-of select = "'/html/images/plots_precision.gif'" /></xsl:attribute>
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>
										<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_DRAWFULLPRECISIONLOG)" /></xsl:attribute>
									</xsl:element>
									
									<xsl:element name = "INPUT">
										<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>
                    <xsl:attribute name = "VALUE"><xsl:value-of select = "concat($tele,'L',$lan,'O',$os,@module_id,'[',@logging_interval,'|1|-1]')" /></xsl:attribute>
										<!-- <xsl:choose> -->
											<!-- <xsl:when test = "@timing_type = '2'" > --> <!-- triggered plot-->
												<!-- <xsl:attribute name = "VALUE"><xsl:value-of select = "concat($tele,'L',$lan,'O',$os,@module_id,'[',@logging_interval,'|1|-1]')" /></xsl:attribute> -->
                    <!-- </xsl:when>  -->
                    <!-- <xsl:otherwise> -->
                    <!--		<xsl:attribute name = "VALUE"><xsl:value-of select = "concat($tele,'L',$lan,'O',$os,@module_id,'[',@logging_interval,'|1|1000]')" /></xsl:attribute> -->
                    <!-- </xsl:otherwise> -->
                    <!-- </xsl:choose>  -->
                  </xsl:element>
									<xsl:element name = "INPUT">
										<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>			
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
										<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
									</xsl:element>	
								</xsl:element><!-- end of form -->
							</td>
						</xsl:if>
						<xsl:if test = "@precision = 'False'" >
							<td class="data" width="20px">	
								<img width="16px" height="16px" src="/html/images/plots_spacer.gif" border="0"/>
							</td>
						</xsl:if>
						<xsl:if test = "@compact = 'True'" >
							<td class="data" width="20px">	
								<xsl:element name = "FORM" >
									<xsl:attribute name = "style">margin:0px 10px 0px 0px;</xsl:attribute>
									<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
									<xsl:attribute name = "ACTION"><xsl:value-of select = "'/GraphRequest'" /></xsl:attribute>								
									<xsl:element name = "INPUT">										
										<xsl:attribute name = "src"><xsl:value-of select = "'/html/images/plots.gif'" /></xsl:attribute>
										<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_GRAPHPOINT)" /></xsl:attribute>
										<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16px; HEIGHT: 16px;'" /></xsl:attribute>
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>									
									</xsl:element>									
									<xsl:element name = "INPUT">
										<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>
										<xsl:attribute name = "VALUE"><xsl:value-of select = "concat($tele,'L',$lan,'O',$os,@module_id,'[',@logging_interval,'|0|-1]')" /></xsl:attribute>
									</xsl:element>									
									<xsl:element name = "INPUT">
										<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>			
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
										<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
									</xsl:element>						
								</xsl:element><!-- end of form -->							
							</td>
						</xsl:if>
						<xsl:if test = "@compact = 'False'" >
							<td class="data" width="20px">	
								<img width="16px" height="16px" src="/html/images/plots_spacer.gif" border="0"/>
							</td>
						</xsl:if>
						<td class="data" valign="top">
							<NOBR><xsl:value-of select = "@display_label" /></NOBR>
						</td>
					</NOBR>
				</tr>
			</table>
		</xsl:for-each>	
	</xsl:template>
	<!--
	//
	// DigitalInputTemplate
	//
	-->

	<xsl:template name = "DigitalInputTemplate" >
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>

	<!--
	//
	// DriverTemplate
	//
	-->

	<xsl:template name = "DriverTemplate" >
	
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	
	</xsl:template>

	<!--
	A standard knob template
	-->
	
	<xsl:template name = "KnobTemplate">
		<table border="0" width="100%" cellpadding="0" cellspacing="0">
			<tr>
				<xsl:element name = "FORM">
					
					<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>	
					<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
			
					<xsl:element name = "INPUT">		
						<xsl:attribute name = "style"><xsl:value-of select = "'BACKGROUND-COLOR: #ffffff'" /></xsl:attribute>
						<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 70'" /></xsl:attribute>					
						<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
					</xsl:element>
						
					<xsl:element name = "INPUT">	
						<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT: 16;'" /></xsl:attribute>
						<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/submit.gif'" /></xsl:attribute>
						<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>				
						<xsl:attribute name = "VALUE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SENDNEWVALUE)" /></xsl:attribute>
						<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SUBMIT)" />	</xsl:attribute>		
					</xsl:element>
						
					<xsl:element name = "INPUT">		
						<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>					
						<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
						<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>					
					</xsl:element>
					
					<xsl:element name = "INPUT">
						<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>					
						<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
						<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>	
					</xsl:element>	
		
					<xsl:element name = "INPUT">		
						<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>
						<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>
						<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>	
					</xsl:element>
				</xsl:element><!-- end of form -->
			</tr>
		</table>
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>
	
	<!--
	//
	// BacnetKnobTemplate
	//
	-->

	<xsl:template name = "BacnetKnobTemplate">
		
		<table border="0" width="100%" cellpadding="0">
			<tr>
				<td width="50%" class="data">
					
					<xsl:element name = "FORM">
						<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>					
						<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
							
						<table border="0" width="100%" cellpadding="0" cellspacing = "0">
							<tr>
								<td width="50%" class="data">
									<xsl:element name = "INPUT">		
										<xsl:attribute name = "style"><xsl:value-of select = "'BACKGROUND-COLOR: #ffffff'" /></xsl:attribute>
										<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 70'" /></xsl:attribute>
										<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" />	</xsl:attribute>				
									</xsl:element>
								</td>
							
								<td width="50%" class="data">
						
									<xsl:element name = "INPUT">	
										<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT: 16;'" /></xsl:attribute>				
										<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/submit.gif'" /></xsl:attribute>
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>
										<xsl:attribute name = "VALUE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SENDNEWVALUE)" /></xsl:attribute>
										<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SUBMIT)" /></xsl:attribute>
									</xsl:element>
						
									<xsl:element name = "INPUT">						
										<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>	
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
										<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>	
									</xsl:element>
			
									<xsl:element name = "INPUT">
										<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>			
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
										<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>	
									</xsl:element>	
			
									<xsl:element name = "INPUT">
										<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>
										<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>
										<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute></xsl:element>
								
								</td>
							</tr>	
						</table>

					</xsl:element>
		
		<!--
		//
		// Relinquish control form
		//
		-->
				</td>	
				<td width="50%" class="data">
					<xsl:element name = "FORM">
							<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
							<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
							
						<xsl:element name = "INPUT">	
							<xsl:attribute name = "style"><xsl:value-of select = "'BACKGROUND-COLOR: #ffffff'" /></xsl:attribute>
							<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
							<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>
							<xsl:attribute name = "VALUE"><xsl:value-of select = "'nul'"/></xsl:attribute>
						</xsl:element>
			
						<xsl:element name = "INPUT">	
							<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT:16;'" /></xsl:attribute>
							<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/relinquish_control.gif'" /></xsl:attribute>
							<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>							
							<xsl:attribute name = "VALUE"><xsl:value-of select = "'Relinquish'" /></xsl:attribute>							
							<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_CLIENT_RELINQUISHCONTROL)" /></xsl:attribute>					
						</xsl:element>
			
						<xsl:element name = "INPUT">					
							<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>			
							<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
							<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>	
						</xsl:element>
			
						<xsl:element name = "INPUT">
							<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>			
							<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
							<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>	
						</xsl:element>	
			
						<xsl:element name = "INPUT">
							<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>	
							<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>	
							<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>
						</xsl:element>
			
					</xsl:element>
				</td>
			</tr>
			</table>
			<xsl:variable name = "lan" select = "@Lan"/>
			<xsl:variable name = "os" select = "@Os"/>
			<xsl:variable name = "tele" select = "@Tele"/>
			<xsl:variable name = "label" select = "@Label"/>
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>
	
	
	<!--
	A standard switch template
	-->
	<xsl:template name = "SwitchTemplate">
		<xsl:if test="$userReadOnly = 0">
			
			
			<xsl:element name = "FORM">
				<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
				<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>

				<xsl:element name = "SELECT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
							
					<xsl:element name = "OPTION">
						<xsl:attribute name = "VALUE"><xsl:value-of select = "'I'" /></xsl:attribute>
							<!-- if not on, select -->
							<xsl:if test="./DynamicModuleStatus/@Status != $WHENON">
								<xsl:attribute name = "SELECTED"></xsl:attribute>
							</xsl:if>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_SETON)" />
					</xsl:element>
							
					<xsl:element name = "OPTION">
						<xsl:attribute name = "VALUE"><xsl:value-of select = "'O'" /></xsl:attribute>
							<!-- if not off, select -->
							<xsl:if test="./DynamicModuleStatus/@Status != $WHENOFF">
								<xsl:attribute name = "SELECTED"></xsl:attribute>
							</xsl:if>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_SETOFF)" />
					</xsl:element>
				</xsl:element>
				
				<xsl:element name = "INPUT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>						
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
					<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>			
				</xsl:element>		
			
				<xsl:element name = "INPUT">
					<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT: 16;'" /></xsl:attribute>				
					<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/submit.gif'" /></xsl:attribute>										
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>							
					<xsl:attribute name = "VALUE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SENDNEWSTATE)" /></xsl:attribute>
					<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SUBMIT)" /></xsl:attribute>
				</xsl:element>
				
				<xsl:element name = "INPUT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>							
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
					<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
				</xsl:element>
				
				<xsl:element name = "INPUT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>								
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
					<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>			
				</xsl:element>
			</xsl:element>
		</xsl:if>
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>
	
	
	<!--
	//
	// A ABACnet SwitchTemplate
	//
	-->

	<xsl:template name = "BacnetSwitchTemplate">
		<table border="0" width="100%" cellpadding="0">
			<tr>
				<xsl:if test="$userReadOnly = 0">
					<td width="50%" class="data">	
						<xsl:element name = "FORM">
								<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
								<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
	
							<xsl:element name = "SELECT">
								<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
						
								<xsl:element name = "OPTION">
									<xsl:attribute name = "VALUE"><xsl:value-of select = "'I'" /></xsl:attribute>
									<!-- if not on, select -->
									<xsl:if test="./DynamicModuleStatus/@Status != $WHENON">
										<xsl:attribute name = "SELECTED"></xsl:attribute>
									</xsl:if>
									<xsl:value-of select = "ScriptSupport:GetString($IDS_SETON)" />
								</xsl:element>
								
								<xsl:element name = "OPTION">
									<xsl:attribute name = "VALUE"><xsl:value-of select = "'O'" /></xsl:attribute>
									<!-- if not off, select -->
									<xsl:if test="./DynamicModuleStatus/@Status != $WHENOFF">
										<xsl:attribute name = "SELECTED"></xsl:attribute>
									</xsl:if>
									<xsl:value-of select = "ScriptSupport:GetString($IDS_SETOFF)" />
								</xsl:element>
							</xsl:element>
					
							<xsl:element name = "INPUT">
								<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>						
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
								<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>			
							</xsl:element>		
				
							<xsl:element name = "INPUT">
								<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT: 16;'" /></xsl:attribute>				
								<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/submit.gif'" /></xsl:attribute>										
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>							
								<xsl:attribute name = "VALUE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SENDNEWSTATE)" /></xsl:attribute>
								<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SUBMIT)" /></xsl:attribute>
							</xsl:element>
					
							<xsl:element name = "INPUT">
								<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>							
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
								<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
							</xsl:element>
							
							<xsl:element name = "INPUT">
								<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>								
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
								<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>			
							</xsl:element>
								
						</xsl:element>
					</td>
					
					<!--
					Relinquish control form
					-->
					
					<td width = "50%" valign = "top">
						<xsl:element name = "FORM">
								<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
								<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
								
							<xsl:element name = "INPUT">	
			
								<xsl:attribute name = "style"><xsl:value-of select = "'BACKGROUND-COLOR: #ffffff'" /></xsl:attribute>
								<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>				
								<xsl:attribute name = "VALUE"><xsl:value-of select = "'nul'"/></xsl:attribute>
							</xsl:element>
							
							<xsl:element name = "INPUT">	
								<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT:16;'" /></xsl:attribute>							
								<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/relinquish_control.gif'" /></xsl:attribute>							
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>
								<xsl:attribute name = "VALUE"><xsl:value-of select = "'Relinquish'" /></xsl:attribute>								
								<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_CLIENT_RELINQUISHCONTROL)" /></xsl:attribute>							
							</xsl:element>
							
							<xsl:element name = "INPUT">						
								<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>							
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>								
								<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>								
							</xsl:element>
							
							<xsl:element name = "INPUT">						
								<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>							
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
								<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>								
							</xsl:element>	
							
							<xsl:element name = "INPUT">						
								<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>								
								<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>								
								<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>							
							</xsl:element>
						</xsl:element>
					</td>
				</xsl:if>
			</tr>
		</table>
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>

	<!--
	//
	// ZoneTemplate
	//
	-->

	<xsl:template name = "ZoneTemplate">
		<xsl:if test="@DeviceType != 'q'">
			<NOBR>
				<xsl:element name = "a">						
					<xsl:attribute name = "href"> <!-- yet to do for (and with &)-->
						<xsl:value-of select = "concat('/GETZONE?PointRef=',@Tele,'L',@Lan,'O',@Os,@Item,'&amp;','Week=','C','&amp;','SID=',$SID)" />
					</xsl:attribute>
					<xsl:value-of select = "ScriptSupport:GetString($IDS_NEXT7DAYS)" />			
				</xsl:element>
			</NOBR>	
			<br />
		</xsl:if>
		<NOBR>
			<xsl:element name = "a">						
				<xsl:attribute name = "href"> <!-- yet to do for (and with &)-->
					<xsl:value-of select = "concat('/GETZONE?PointRef=',@Tele,'L',@Lan,'O',@Os,@Item,'&amp;','Week=','S','&amp;','SID=',$SID)" />
				</xsl:attribute>
				<xsl:value-of select = "ScriptSupport:GetString($IDS_EVERYWEEK)" />
			</xsl:element>
		</NOBR>
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>	

	<!-- bacnet zone template -->
	<xsl:template name = "BacnetZoneTemplate">
		<NOBR>
			<xsl:element name = "a">
				<xsl:attribute name = "href">
					<xsl:value-of select = "concat('/GETZONE?PointRef=',@Tele,'L',@Lan,'O',@Os,@Item,'&amp;','Week=','C','&amp;','SID=',$SID)" />
				</xsl:attribute>
				<xsl:value-of select = "ScriptSupport:GetString($IDS_NEXT7DAYS)" />
			</xsl:element>
		</NOBR>
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
	</xsl:template>

	<!--
	//
	// XSensorTemplate
	//
	-->

	<xsl:template name = "XSensorTemplate">

		<xsl:element name = "FORM">
							
			<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
			<xsl:attribute name = "ACTION"><xsl:value-of select = "'/GraphRequest'" /></xsl:attribute>

			<xsl:element name = "INPUT">
				<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 34; HEIGHT: 18;'" /></xsl:attribute>
				<xsl:attribute name = "src"><xsl:value-of select = "'/html/images/graph.gif'" /></xsl:attribute>
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>
				<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_GRAPHPOINT)" /></xsl:attribute>
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>			
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
				<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>							
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
				<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
			</xsl:element>
		</xsl:element>	
			<!-- check whether the plot is graphable -->
		<xsl:if test = "./DynamicModuleStatus/@Graphable = '1'" >
			<xsl:call-template name = "PlotTemplate" />
		</xsl:if>
		
	</xsl:template>				
	
	<!--
	//
	// templates implementation for specific static object actions
	//
	-->

	<!--
	//
	// WebTemplate
	//
	-->

	<xsl:template name = "WebTemplate">
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
		<TR>
			<TD CLASS="data">
				<xsl:element name="a">
					<xsl:attribute name="href">
						<xsl:value-of select="substring-after(./OnTouch, 'WEB ')" />
					</xsl:attribute>
					<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
					<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>	
				</xsl:element>
			</TD>
		</TR>
	</xsl:template>

	<!--
	//
	// GotoTemplate
	//
	-->

	<xsl:template name = "GotoTemplate">
		
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
				
				
		<xsl:choose>			
				<xsl:when test="substring(./OnTouch,1,9) = 'GOTO NEXT'">
					<!-- not valid for text mode schematics -->
					<!--
					<TR>
						<TD CLASS="data">
							<xsl:element name="a">
								<xsl:attribute name="href">
									<xsl:value-of select="concat('/',substring-after(./OnTouch, 'GOTO '),'?SID=',$SID)" />
								</xsl:attribute>
								<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>
							</xsl:element>
						</TD>
					</TR>
					-->
				</xsl:when>			
			
				<xsl:when test="substring(./OnTouch,1,13) = 'GOTO PREVIOUS'">
					<!-- not valid for text mode schematics -->
					<!--
					<TR>
						<TD CLASS="data">
							<xsl:element name="a">
								<xsl:attribute name="href">
									<xsl:value-of select="concat('/',substring-after(./OnTouch, 'GOTO '),'?SID=',$SID)" />
								</xsl:attribute>
								<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)" />							</xsl:element>
						</TD>
					</TR>
					-->
				</xsl:when>		
	
				
				<xsl:otherwise>
					<TR>
						<TD CLASS="data">
							<xsl:element name="a">
								<xsl:attribute name="href">			
									<xsl:value-of select="concat('/',substring-after(./OnTouch, 'GOTO '),'?SID=',$SID)" />
								</xsl:attribute>
								<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
								<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)" />
							</xsl:element>
						</TD>
					</TR>
				</xsl:otherwise>

		</xsl:choose>
	</xsl:template>

	<!--
	//
	// ViewQueryTemplate
	//
	-->

	<xsl:template name = "ViewQueryTemplate">
		
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
	
		<TR>
			<TD CLASS="data">
				<xsl:element name="a">
					<xsl:attribute name="href">			
						<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)" />
					</xsl:attribute>
					
					<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
					<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>
				</xsl:element>
			</TD>
		</TR>
		
	</xsl:template>

	<!--
	//
	// SendTemplate
	//
	-->

	<xsl:template name = "SendTemplate">
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
		<TR>
			<TD CLASS="data">
				<xsl:element name="a">
					<xsl:attribute name="href">			
						<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)" />
					</xsl:attribute>
					<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
					<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>
				</xsl:element>
			</TD>
		</TR>
	</xsl:template>

	<!--
	//
	// LogoutTemplate
	//
	-->

	<xsl:template name = "LogoutTemplate">
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
		<TR>
			<TD CLASS="data">
				<xsl:element name="a">
					<xsl:attribute name="href">			
						<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)" />
					</xsl:attribute>				
					<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
					<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>
				</xsl:element>
			</TD>
		</TR>
	</xsl:template>

	<!--
	//
	// LoginAsTemplate
	//
	-->

	<xsl:template name = "LoginAsTemplate">
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
		<TR>
			<TD CLASS="data">
				<xsl:element name="a">
					<xsl:attribute name="href">			
						<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)" />
					</xsl:attribute>
					
					<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
					<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>
					
				</xsl:element>
			</TD>
		</TR>
	</xsl:template>

	<!--
	//
	// ConfigTemplate
	//
	-->

	<xsl:template name = "ConfigTemplate">
	
		<!-- get variables that are required for additional display filtering-->
		<xsl:variable name = "strDisplay" select = "./ToDisplay"/>
		<xsl:variable name = "strToolTip" select = "./@Tooltip"/>
		<xsl:variable name = "actionString" select = "./OnTouch"/>
		
		<TR>
			<TD CLASS="data">
				<xsl:element name="a">
					<xsl:attribute name="href">			
						<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)" />
					</xsl:attribute>
					<!-- Determine what should be displayed (i.e. what makes most sense to the operator-->
					<xsl:value-of select = "Filter:chooseDisplay($strDisplay,$strToolTip,$actionString)"/>			
				</xsl:element>
			</TD>
		</TR>
	</xsl:template>


	<!--
	//
	// Page Navigation Template
	//
	-->
	<xsl:template name = "PageNavigation">
		<DIV>
			<SMALL>
				<A HREF="#PageTop">
					<nobr>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_TOPOFPAGE)" />
					</nobr>
				</A> | 
				<A HREF="#liveData">
					<nobr>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_LIVEDATA)" />
					</nobr>
				</A> | 
				<A HREF="#actions">
					<nobr>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_ACTIONS)" />
					</nobr>
				</A> | 
				<A HREF="#labels">
					<nobr>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_XSL_ADDITIONALINFO)" />
					</nobr>
				</A> | 
				<xsl:element name = "A">
					<xsl:attribute name="href">
						<xsl:value-of select="concat('/LOGOUT?SID=',$SID)"/>
					</xsl:attribute>
					<nobr>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_LOG_OFF)" />
					</nobr>
				</xsl:element> | 
				<A HREF="javascript:location.reload(true)">
					<nobr>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_REFRESH)" />
					</nobr>
				</A>
				
			</SMALL>
		</DIV>
	</xsl:template>
	
	<!--
	//
	// AnalogueTemplate
	//
	-->

	<xsl:template name = "AnalogueTemplate">

		<xsl:element name = "FORM">
							
			<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
			<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
			
			<xsl:element name = "INPUT">		
				<xsl:attribute name = "style"><xsl:value-of select = "'BACKGROUND-COLOR: #ffffff'" /></xsl:attribute>
				<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
			</xsl:element>
			
			<xsl:element name = "INPUT">			
				<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 100'" /></xsl:attribute>
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'submit'" /></xsl:attribute>				
				<xsl:attribute name = "VALUE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SENDNEWVALUE)" /></xsl:attribute>				
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>			
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
				<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>					
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>						
				<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
			</xsl:element>	
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>								
				<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
				<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>			
			</xsl:element>	
		</xsl:element>
	
	</xsl:template>
			
	
	
	<!--
	//
	// ByteTemplate - used for adjusting Byte bits
	//
	-->
	
	<xsl:template name = "ByteTemplate">
		<xsl:if test="$userReadOnly = 0">
				
			<xsl:element name = "FORM">
				<xsl:attribute name = "METHOD"><xsl:value-of select = "'GET'" /></xsl:attribute>
				<xsl:attribute name = "ACTION"><xsl:value-of select = "'/AdjustIQParameter'" /></xsl:attribute>
					
				<xsl:element name = "SELECT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'NewState'" /></xsl:attribute>
					<xsl:element name = "OPTION">
						<xsl:attribute name = "VALUE"><xsl:value-of select = "'I'" /></xsl:attribute>
						<!-- if not on, select -->
						<xsl:if test="./DynamicModuleStatus/@Status != $WHENON">
							<xsl:attribute name = "SELECTED"></xsl:attribute>
						</xsl:if>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_SETON)" />
					</xsl:element>
					
					<xsl:element name = "OPTION">
						<xsl:attribute name = "VALUE"><xsl:value-of select = "'O'" /></xsl:attribute>
						<!-- if not off, select -->
						<xsl:if test="./DynamicModuleStatus/@Status != $WHENOFF">
							<xsl:attribute name = "SELECTED"></xsl:attribute>
						</xsl:if>
						<xsl:value-of select = "ScriptSupport:GetString($IDS_SETOFF)" />
					</xsl:element>
				</xsl:element>
										
				<xsl:element name = "INPUT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'PointRef'" /></xsl:attribute>						
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
					<xsl:attribute name = "VALUE"><xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)" /></xsl:attribute>			
				</xsl:element>			
				
				<xsl:element name = "INPUT">
					<xsl:attribute name = "style"><xsl:value-of select = "'WIDTH: 16; HEIGHT: 16;'" /></xsl:attribute>				
					<xsl:attribute name = "SRC"><xsl:value-of select = "'/html/images/submit.gif'" /></xsl:attribute>										
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'image'" /></xsl:attribute>							
					<xsl:attribute name = "VALUE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SENDNEWSTATE)" /></xsl:attribute>
					<xsl:attribute name = "TITLE"><xsl:value-of select = "ScriptSupport:GetString($IDS_SUBMIT)" /></xsl:attribute>
				</xsl:element>				
				
				<xsl:element name = "INPUT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'SID'" /></xsl:attribute>							
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>							
					<xsl:attribute name = "VALUE"><xsl:value-of select = "$SID" /></xsl:attribute>			
				</xsl:element>
				
				<xsl:element name = "INPUT">
					<xsl:attribute name = "NAME"><xsl:value-of select = "'Label'" /></xsl:attribute>								
					<xsl:attribute name = "TYPE"><xsl:value-of select = "'hidden'" /></xsl:attribute>			
					<xsl:attribute name = "VALUE"><xsl:value-of select = "@Label" /></xsl:attribute>			
				</xsl:element>			
			</xsl:element>
		</xsl:if>
	</xsl:template>
	

	<!--
	//
	// embedded code using c# goes here
	// it works when called using .net framework
	// it will not generate any output when reference to xsl file is used in xml file to quick view output in the explorer
	//
	-->

	<msxsl:script language = "C#" implements-prefix = "Filter">
	public string FilterString(string actionString)
	{	
		string [] split = actionString.Split(new Char [] {' '});

		return split[0];
	}
	
	public string replaceEmbeddedCommands(string szText)
	{
		return szText.Replace("&lt;NEWLINE&gt;"," ");
	}
	
	public string chooseDisplay( string strDisplay, string strTooltip, string strAction )
	{
		//
		// This function determines what to display for a static item with an action
		// by examining the Display, Tooltip and Action values.  As graphics cannot be 
		// displayed, a text alternative is required.
		// 
		
		string strUpper = strDisplay.ToUpper();
		bool blnIsFileSpec = false;
		
		if( strUpper.EndsWith(".BMP") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".JPG") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".JPEG") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".GIF") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".WMF") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".EMF") ) blnIsFileSpec = true;
		
		else if( strUpper.EndsWith(".TSS") ) blnIsFileSpec = true;
		
		else if( strUpper.EndsWith(".HTML") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".HTM") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".DOC") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".XLS") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".XML") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".PPT") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".PDF") ) blnIsFileSpec = true;
		else if( strUpper.EndsWith(".ANIMATION") ) blnIsFileSpec = true;
					
		else if( strUpper.StartsWith("HTTP://") ) blnIsFileSpec = true;
		
		if( blnIsFileSpec )
		{
			if( strTooltip.Length > 0 )
				return strTooltip;
			else
				return strAction;
		}
		return replaceEmbeddedCommands(strDisplay);
	}
	</msxsl:script>

</xsl:stylesheet>