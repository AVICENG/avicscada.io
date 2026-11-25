<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version = "1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:msxsl = "urn:schemas-microsoft-com:xslt" 
 xmlns:Filter= "urn:scripts">

	<!--
	//
	// parameters to be passed in
	//
	-->

	<xsl:param name = "SID">
	</xsl:param>
	
	<xsl:param name = "viewedTime">
	</xsl:param>
	
	<xsl:param name = "currentUserName">
	</xsl:param>
	
	<xsl:param name = "pageName">
	</xsl:param>
	
	<xsl:param name = "userPinLevel">
	</xsl:param>
	
	<!--
	// parameters
	// resource strings from application for globalaziation
	-->
	
	<xsl:param name = "IDS1_CURRENT_USER_NAME">
	</xsl:param>
	<xsl:param name = "IDS1_VIEWED_AT">
	</xsl:param>
	<xsl:param name = "IDS1_DYNAMIC_DATA">
	</xsl:param>
	<xsl:param name = "IDS1_CLICK_REFRESH">
	</xsl:param>
	<xsl:param name = "IDS1_JUMP_TO_STATIC">
	</xsl:param>
	<xsl:param name = "IDS1_LABEL_TEXT">
	</xsl:param>
	<xsl:param name = "IDS1_VALUE">
	</xsl:param>
	<xsl:param name = "IDS1_UNITS">
	</xsl:param>
	<xsl:param name = "IDS1_ALARM_CODE">
	</xsl:param>
	<xsl:param name = "IDS1_ITEM">
	</xsl:param>
	<xsl:param name = "IDS1_ACTION">
	</xsl:param>
	<xsl:param name = "IDS1_NO_ACTION">
	</xsl:param>
	<xsl:param name = "IDS1_STATIC_DATA">
	</xsl:param>
	<xsl:param name = "IDS1_JUMP_TO_DYNAMIC">
	</xsl:param>
	<xsl:param name = "IDS1_DISPLAY_TEXT">
	</xsl:param>
	<xsl:param name = "IDS1_VIEW_HELP">
	</xsl:param>
	<xsl:param name = "IDS1_COPY_RIGHT">
	</xsl:param>	
	<xsl:param name = "IDS1_SEND_NEW_STATE">
	</xsl:param>
	<xsl:param name = "IDS1_GRAPH">
	</xsl:param>
	<xsl:param name = "IDS1_SEND_NEW_VALUE">
	</xsl:param>
	<xsl:param name = "IDS1_TODAY_AND_NEXT6_DAYS">
	</xsl:param>
	<xsl:param name = "IDS1_DEFAULT_WEEK_TIMES">
	</xsl:param>
	<xsl:param name = "IDS1_SET_ON">
	</xsl:param>
	<xsl:param name = "IDS1_SET_OFF">
	</xsl:param>
	
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
						<xsl:value-of select = "'/html/images/style_XSL.css'">
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
						<td rowspan="2" width="71" valign="top"><img src="/html/images/963logo.gif" border="0"></img></td>
						<td width = "100%" height="41" colspan="2" bgcolor="#ff6600" valign="middle" align="left">
							<table width="100%" cellspacing="0" cellpadding="0" border = "0">
								<tr>
									<td class="mainlink">										
										<a href="javascript:location.reload(true)">
											<img src="/html/images/refresh.gif" border="0" title="Refresh Page" align = "right"></img>
										</a>										
									</td>
								</tr>
							</table>
						</td>
					</tr>				
					<tr>						
						<td width="241" valign="top"><img src="/html/images/banner-swish-left.gif"></img></td>
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
								<xsl:value-of select = "$IDS1_CURRENT_USER_NAME">
								</xsl:value-of>
								:
							</b>							
							<xsl:value-of select = "$currentUserName">
							</xsl:value-of>							
						</td>
					</tr>	
					<tr>	
						<td align="right">							
								<b>							
									<xsl:value-of select = "$IDS1_VIEWED_AT">
									</xsl:value-of>	
									:								
								</b>
								<xsl:value-of select = "$viewedTime">
								</xsl:value-of>
						</td>
					</tr>					
				</table>					
				
				<!--
				//
				// heading of the dynamic data table
				//
				-->			
				
				<table>
					<tr>						
						<td valign="middle">
							<div class="pageTitle">
								<a name = "DynamicData">
									<xsl:value-of select = "$IDS1_DYNAMIC_DATA">
									</xsl:value-of>										
								</a>
							</div>
						</td>						
					</tr>
				</table>
				
				<!--
				//
				// line break between the heading and data table
				//
				-->
				
				<br></br>
				
				<!--
				//
				// display the column headings for the dynamic data table
				// a template to fill the table with dynamic data is embedded/called from here
				//
				-->
				
				<table cellpadding="5" ID="DynamicData" width="100%">
				
					<COLGROUP span="6" width="15"></COLGROUP>
				
					<tr>
						<td class="heading">
							<xsl:value-of select = "$IDS1_LABEL_TEXT">
							</xsl:value-of>								
						</td>
						<td class="heading">
							<xsl:value-of select = "$IDS1_VALUE">
							</xsl:value-of>
						</td>						
						
						<td class="heading">
							<xsl:value-of select = "$IDS1_UNITS">
							</xsl:value-of>
						</td>						
						
						<td class="heading">
							<xsl:value-of select = "$IDS1_ALARM_CODE">
							</xsl:value-of>
						</td>	
						
						<td class="heading">
							<xsl:value-of select = "$IDS1_ITEM">
							</xsl:value-of>
						</td>											
						
						<td class="heading">
							<xsl:value-of select = "$IDS1_ACTION">
							</xsl:value-of>
						</td>					
						
					</tr>
																							
					<xsl:apply-templates select = "Schematic/Objects/DynamicObj">					
					</xsl:apply-templates>
				</table>				
				
				<!--
				//
				// keep a short distance between first table and the next data heading
				//
				-->
									
				<br></br>
				
				<!--
				//
				// display the heading of static data
				//
				-->		
				
				<table>
					<tr>						
						<td valign="middle">
							<div class="pageTitle">
								<a name = "StaticData">
									<xsl:value-of select = "$IDS1_STATIC_DATA">
									</xsl:value-of>										
								</a>
							</div>
						</td>						
					</tr>
				</table>
				
				<!--
				//
				// line break between the heading and data table
				//
				-->
				
				<br></br>
								
				<!--
				//
				// display the column headings for the static data table
				// a template to fill the table with static data is embedded/called from here
				//
				-->
				
				<table cellpadding="5" ID="StaticData" width="100%"> <!-- white -->
						
					<COLGROUP span="2" width="50%"></COLGROUP>
					<tr>
						<td class="heading">
							<xsl:value-of select = "$IDS1_DISPLAY_TEXT">
							</xsl:value-of>
						</td>
						
						<td class="heading">
							<xsl:value-of select = "$IDS1_ACTION">
							</xsl:value-of>
						</td>
					</tr>
																							
					<xsl:apply-templates select = "Schematic/Objects/StaticObj">					
					</xsl:apply-templates>
				</table>
								
				
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
				
				<!--
				<br></br>
				<img src="/html/images/mainheader_bottom1.gif" width="100%" height="20">
				</img>	
				-->	
				
				<table width="100%" height="9" cellspacing="0" cellpadding="0" border="0" ID="Table4">					
					<tr>						
						<td width = "100%" height="20" bgcolor="#ff6600" valign="middle" align="left">
						</td>
					</tr>	
				</table>				
				
				<div>
					<a href = "#StaticData">
						<xsl:value-of select = "$IDS1_JUMP_TO_STATIC">
						</xsl:value-of>
					</a> | 
					<a href = "#DynamicData">
						<xsl:value-of select = "$IDS1_JUMP_TO_DYNAMIC">
						</xsl:value-of>										
					</a>
				</div>		
				
				
				<div align = "right">
				
					<a href = "http://www.trend-controls.com" align = "right">
						<xsl:value-of select = "$IDS1_COPY_RIGHT">
						</xsl:value-of>
					</a>
					<br></br>
					
					<a href = "/html/WebHelp/963_manu.htm" align = "right">
						<xsl:value-of select = "$IDS1_VIEW_HELP">
						</xsl:value-of>
					</a>
					<br></br>
										
					<img src="/html/images/Trend.gif" width="150" align = "right" ></img>
						
				</div>
							
				
				<!--
				//
				// add a link to display the web help for 963 application using javascript
				//
				-->
				
				<!--
				<xsl:element name = "p">						
						<xsl:attribute name = "align">
							<xsl:value-of select = "'center'">
							</xsl:value-of>						
						</xsl:attribute>								
						
						<xsl:element name = "a">
							<xsl:attribute name = "href">								
								<xsl:value-of select = "concat('javascript:launchPopup(','&quot;','/html/WebHelp/963_manu.htm','&quot;',',','&quot;','status,resizable,scrollbars','&quot;)')">
								</xsl:value-of>						
							</xsl:attribute>												
							
							<xsl:value-of select = "$IDS1_VIEW_HELP">
							</xsl:value-of>
						</xsl:element>
				
				</xsl:element>
				-->		
				
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
					<td class="data">
						<img src="/html/images/sensor.gif" align="absBottom" title="Sensor"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'D'">
					<td class="data">
						<img src="/html/images/driver.gif" align="absBottom" title="Driver"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'K'">
					<td class="data">
						<img src="/html/images/knob.gif" align="absBottom" title="Knob"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>		
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'I'">
					<td class="data">
						<img src="/html/images/digitalinputs.gif" align="absBottom" title="Digital Input"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'W'">
					<td class="data">
						<img src="/html/images/switch.gif" align="absBottom" title="Switch"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'Z'">
					<td class="data">					
						<img src="/html/images/timezone.gif" align="absBottom" title="Time Zone"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'X'">
					<td class="data">		
						<img src="/html/images/internalsensor.gif" align="absBottom" title="Internal Sensor"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>		
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:when test = "substring(@Item,1,1) = 'M'">
					<td class="data">		
						<img src="/html/images/critcalalarm.gif" align="absBottom" title="Internal Sensor"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>		
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:when>
				
				<xsl:otherwise>				
					<td class="data">						
						<img src="/html/images/critcalalarm.gif" align="absBottom" title="Internal Sensor"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>		
						<xsl:value-of select = "@Label">
						</xsl:value-of>
					</td>			
				</xsl:otherwise>
			</xsl:choose>
					
			<td class="data">
				<xsl:value-of select = "./DynamicModuleStatus/FormattedLatestValue">
				</xsl:value-of>
			</td>
			
			<td class="data">
				<xsl:if test = "@Units = ''">	
					<xsl:text>
					...
					</xsl:text>
				</xsl:if>
				
				<xsl:if test = "@Units != ''">	
					<xsl:value-of select = "@Units">
					</xsl:value-of>					
				</xsl:if>				
			</td>
			
			<!-- display the alarm cell with red background and white text if there is alarm -->
			
			<xsl:variable name = "isAlarm" select = "./DynamicModuleStatus/AlarmText">
			</xsl:variable>		
			
			<xsl:if test = "string-length($isAlarm) > 0"> 
				<td bgcolor = "#FF0000">
					<font size="3" color="#FFFFFF"> 
						<img src="/html/images/alarmFlash.gif" align="absBottom" title="Critical Alarm"></img>
						<xsl:value-of select = "' '">
						</xsl:value-of>
						<b>
						<xsl:value-of select = "./DynamicModuleStatus/AlarmText"> 
						</xsl:value-of>
						</b>
					</font>
				</td>	
			</xsl:if>							
			
			<xsl:if test = "string-length($isAlarm) = 0"> 
				<td class="data">
					<xsl:value-of select = "./DynamicModuleStatus/AlarmText"> 
					</xsl:value-of>
				</td>	
			</xsl:if>
			
			
			<td class="data">
				<xsl:value-of select = "concat(@Tele,'L',@Lan,'O',@Os,@Item)">
				</xsl:value-of>
			</td>	
						
			
			<td class="data">
				
				<!-- action here ... for the specified item-->
				
				<xsl:if test="$userPinLevel >= @Pin">
				
					<xsl:choose>
						
						<xsl:when test = "substring(@Item,1,1) = 'S'">
							<xsl:call-template name = "SensorTemplate">
							</xsl:call-template>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'D'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'K'">
							<xsl:call-template name = "KnobTemplate">
							</xsl:call-template>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'I'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'W'">
							<xsl:call-template name = "SwitchTemplate">
							</xsl:call-template>
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'Z'">
							<xsl:call-template name = "ZoneTemplate">
							</xsl:call-template>						
						</xsl:when>
						
						<xsl:when test = "substring(@Item,1,1) = 'X'">
							<xsl:call-template name = "XSensorTemplate">
							</xsl:call-template>
						</xsl:when>
						
						<xsl:otherwise>
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>
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

		<xsl:element name = "FORM">
							
			<xsl:attribute name = "METHOD">
				<xsl:value-of select = "'GET'">
				</xsl:value-of>
			</xsl:attribute>
			<xsl:attribute name = "ACTION">
				<xsl:value-of select = "'/GraphRequest'">
				</xsl:value-of>
			</xsl:attribute>
			
			<xsl:element name = "INPUT">
			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'WIDTH: 100'">
					</xsl:value-of>
				</xsl:attribute>				
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'Graph'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'Submit'">
					</xsl:value-of>
				</xsl:attribute>			
							
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$IDS1_GRAPH">
					</xsl:value-of>
				</xsl:attribute>							
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'PointRef'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "concat('L',@Lan,'O',@Os,@Item)">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'SID'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$SID">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
		</xsl:element>
							
	</xsl:template>

	<!--
	//
	// DigitalInputTemplate
	//
	-->

	<xsl:template name = "DigitalInputTemplate">
	</xsl:template>

	<!--
	//
	// DriverTemplate
	//
	-->

	<xsl:template name = "DriverTemplate">
	</xsl:template>

	<!--
	//
	// KnobTemplate
	//
	-->

	<xsl:template name = "KnobTemplate">

		<xsl:element name = "FORM">
							
			<xsl:attribute name = "METHOD">
				<xsl:value-of select = "'GET'">
				</xsl:value-of>
			</xsl:attribute>
			<xsl:attribute name = "ACTION">
				<xsl:value-of select = "'/AdjustAnalogue'">
				</xsl:value-of>
			</xsl:attribute>
			
			<xsl:element name = "INPUT">
			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'BACKGROUND-COLOR: #ffffff'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'NewValue'">
					</xsl:value-of>
				</xsl:attribute>
			</xsl:element>
			
			<xsl:element name = "INPUT">			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'WIDTH: 100'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'submit'">
					</xsl:value-of>
				</xsl:attribute>		
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$IDS1_SEND_NEW_VALUE">
					</xsl:value-of>
				</xsl:attribute>				
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'PointRef'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "concat('L',@Lan,'O',@Os,@Item,'(v=')">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'SID'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$SID">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'OldValue'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "@Waiting">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
		</xsl:element>
		
	</xsl:template>

	<!--
	//
	// SwitchTemplate
	//
	-->

	<xsl:template name = "SwitchTemplate">

		<xsl:element name = "FORM">
		
			<xsl:attribute name = "METHOD">
				<xsl:value-of select = "'GET'">
				</xsl:value-of>
			</xsl:attribute>
			<xsl:attribute name = "ACTION">
				<xsl:value-of select = "'/AdjustDigital'">
				</xsl:value-of>
			</xsl:attribute>
			
			<xsl:element name = "INPUT">
			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'BACKGROUND-COLOR: #e9f1f3'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'NewState'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'radio'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "'I'">
					</xsl:value-of>									
				</xsl:attribute>	
				
				<xsl:value-of select = "$IDS1_SET_ON">
				</xsl:value-of>
			</xsl:element>
			
			<xsl:element name = "INPUT">
			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'BACKGROUND-COLOR: #e9f1f3'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'NewState'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'radio'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "'O'">
					</xsl:value-of>					
				</xsl:attribute>	
				
				<xsl:attribute name="checked">
					<xsl:value-of select = "'checked'">
					</xsl:value-of>					
				</xsl:attribute>	
				
				<xsl:value-of select = "$IDS1_SET_OFF">
				</xsl:value-of>
				
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'PointRef'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "concat('L',@Lan,'O',@Os,@Item,'(S=')">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'WIDTH: 100'">
					</xsl:value-of>
				</xsl:attribute>
												
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'submit'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$IDS1_SEND_NEW_STATE">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'SID'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$SID">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'OldState'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "O">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
		</xsl:element>
		
	</xsl:template>

	<!--
	//
	// ZoneTemplate
	//
	-->

	<xsl:template name = "ZoneTemplate">
		
		<xsl:element name = "a">						
			<xsl:attribute name = "href"> <!-- yet to do for (and with &)-->
				<xsl:value-of select = "concat('/GETZONE?PointRef=','L',@Lan,'O',@Os,@Item,'&amp;','Week=','C','&amp;','SID=',$SID)">
				</xsl:value-of>								
			</xsl:attribute>
			<xsl:value-of select = "$IDS1_TODAY_AND_NEXT6_DAYS">
			</xsl:value-of>			
		</xsl:element>							
		
		|
		
		<xsl:element name = "a">						
			<xsl:attribute name = "href"> <!-- yet to do for (and with &)-->
				<xsl:value-of select = "concat('/GETZONE?PointRef=','L',@Lan,'O',@Os,@Item,'&amp;','Week=','S','&amp;','SID=',$SID)">
				</xsl:value-of>								
			</xsl:attribute>
			<xsl:value-of select = "$IDS1_DEFAULT_WEEK_TIMES">
			</xsl:value-of>
		</xsl:element>	
		
	</xsl:template>			

	<!--
	//
	// XSensorTemplate
	//
	-->

	<xsl:template name = "XSensorTemplate">

		<xsl:element name = "FORM">
							
			<xsl:attribute name = "METHOD">
				<xsl:value-of select = "'GET'">
				</xsl:value-of>
			</xsl:attribute>
			<xsl:attribute name = "ACTION">
				<xsl:value-of select = "'/GraphRequest'">
				</xsl:value-of>
			</xsl:attribute>
			
			<xsl:element name = "INPUT">
			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'WIDTH: 100'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'Graph'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'Submit'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$IDS1_GRAPH">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'PointRef'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "concat('L',@Lan,'O',@Os,@Item)">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
			<xsl:element name = "INPUT">
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'SID'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'hidden'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "VALUE">
					<xsl:value-of select = "$SID">
					</xsl:value-of>
				</xsl:attribute>			
			</xsl:element>
			
		</xsl:element>
								
	</xsl:template>				

	<!--
	//
	// template implementation to get and display the static data
	// from xml page generated by 963 application
	//
	-->
	
	<xsl:template match = "Schematic/Objects/StaticObj">
	
		<tr>
			<td class="data">
				<xsl:value-of select = "./ToDisplay">
				</xsl:value-of>				
			</td>
				
			<td class="data">
			
				<xsl:if test="$userPinLevel >= @Pin">			    
					<xsl:variable name = "actionString" select = "./OnTouch">
					</xsl:variable>				
					
					<!--
					//
					// filter the string using embedded c# code	
					//
					-->
					
					<xsl:variable name = "action" select = "Filter:FilterString($actionString)">
					</xsl:variable>
						
					<!--
					//
					// specific templates to format the links for different actions
					//
					-->
								
					<xsl:choose>
					
						<xsl:when test="$action = 'WEB'">
							<xsl:call-template name = "WebTemplate">
							</xsl:call-template>						
						</xsl:when>			
										
						<xsl:when test="$action = 'VIEWGRAPH'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>			
						
						<xsl:when test="$action = 'VIEWPOINTS'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>			
					
						<xsl:when test="$action = 'VIEWQUERY'">
							<xsl:call-template name = "ViewQueryTemplate">
							</xsl:call-template>					
						</xsl:when>			
					
						<xsl:when test="$action = 'SEND'">
							<xsl:call-template name = "SendTemplate">
							</xsl:call-template>					
						</xsl:when>			
					
						<xsl:when test="$action = 'SETGENERIC'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>			
					
						<xsl:when test="$action = 'LOGOUT'">
							<xsl:call-template name = "LogoutTemplate">
							</xsl:call-template>					
						</xsl:when>			
					
						<xsl:when test="$action = 'MESSAGE'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>			
					
						<xsl:when test="$action = 'PLAY'">
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:when>			
					
						<xsl:when test="$action = 'LOGINAS'">
							<xsl:call-template name = "LoginAsTemplate">
							</xsl:call-template>
						</xsl:when>			
					
						<xsl:when test="$action = 'GOTO'">					
							<xsl:call-template name = "GotoTemplate">
							</xsl:call-template>						
						</xsl:when>			
					
						<xsl:when test="$action = 'CONFIG'">						
							<xsl:call-template name = "ConfigTemplate">
							</xsl:call-template>
						</xsl:when>			
					
						<xsl:otherwise>
							<xsl:value-of select = "$IDS1_NO_ACTION">
							</xsl:value-of>						
						</xsl:otherwise>
						
					</xsl:choose>
				
				</xsl:if>
								
			</td>
		</tr>
		
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
		<xsl:element name="a">
			<xsl:attribute name="href">
				<xsl:value-of select="substring-after(./OnTouch, 'WEB ')">
				</xsl:value-of>
			</xsl:attribute>
			
			<xsl:value-of select = "./ToDisplay">
			</xsl:value-of>
					
		</xsl:element>
	</xsl:template>

	<!--
	//
	// GotoTemplate
	//
	-->

	<xsl:template name = "GotoTemplate">
		<xsl:choose>		
			
				<xsl:when test="substring(./OnTouch,1,9) = 'GOTO NEXT'">
					<xsl:element name="a">
						<xsl:attribute name="href">
							<xsl:value-of select="concat('/',substring-after(./OnTouch, 'GOTO '),'?SID=',$SID)">
							</xsl:value-of>
						</xsl:attribute>
						
						<xsl:value-of select = "./ToDisplay">
						</xsl:value-of>
						
					</xsl:element>
				</xsl:when>			
			
				<xsl:when test="substring(./OnTouch,1,13) = 'GOTO PREVIOUS'">
					<xsl:element name="a">
						<xsl:attribute name="href">
							<xsl:value-of select="concat('/',substring-after(./OnTouch, 'GOTO '),'?SID=',$SID)">
							</xsl:value-of>
						</xsl:attribute>
						
						<xsl:value-of select = "./ToDisplay">
						</xsl:value-of>
			
					</xsl:element>
				</xsl:when>		
				
				<xsl:otherwise> <!-- when test="substring(./OnTouch,1,4) = 'GOTO'" -->
					<xsl:element name="a">
						<xsl:attribute name="href">			
							<xsl:value-of select="concat('/',substring-after(./OnTouch, 'GOTO '),'?SID=',$SID)">
							</xsl:value-of>			
						</xsl:attribute>
						
						<xsl:value-of select = "./ToDisplay">
						</xsl:value-of>
						
					</xsl:element>
				</xsl:otherwise>
			
		</xsl:choose>
	</xsl:template>

	<!--
	//
	// ViewQueryTemplate
	//
	-->

	<xsl:template name = "ViewQueryTemplate">
		<xsl:element name="a">
			<xsl:attribute name="href">			
				<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)">
				</xsl:value-of>			
			</xsl:attribute>
			
			<xsl:value-of select = "./ToDisplay">
			</xsl:value-of>
			
		</xsl:element>
	</xsl:template>

	<!--
	//
	// SendTemplate
	//
	-->

	<xsl:template name = "SendTemplate">
		<xsl:element name="a">
			<xsl:attribute name="href">			
				<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)">
				</xsl:value-of>			
			</xsl:attribute>
			
			<xsl:value-of select = "./ToDisplay">
			</xsl:value-of>
			
		</xsl:element>
	</xsl:template>

	<!--
	//
	// LogoutTemplate
	//
	-->

	<xsl:template name = "LogoutTemplate">
		<xsl:element name="a">
			<xsl:attribute name="href">			
				<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)">
				</xsl:value-of>			
			</xsl:attribute>				
			
			<xsl:value-of select = "./ToDisplay">
			</xsl:value-of>
			
		</xsl:element>
	</xsl:template>

	<!--
	//
	// LoginAsTemplate
	//
	-->

	<xsl:template name = "LoginAsTemplate">
		<xsl:element name="a">
			<xsl:attribute name="href">			
				<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)">
				</xsl:value-of>			
			</xsl:attribute>
			
			<xsl:value-of select = "./ToDisplay">
			</xsl:value-of>
			
		</xsl:element>
	</xsl:template>

	<!--
	//
	// ConfigTemplate
	//
	-->

	<xsl:template name = "ConfigTemplate">
		<xsl:element name="a">
			<xsl:attribute name="href">			
				<xsl:value-of select="concat('/',./OnTouch,'?SID=',$SID)">
				</xsl:value-of>			
			</xsl:attribute>
			
			<xsl:value-of select = "./ToDisplay">
			</xsl:value-of>
			
		</xsl:element>
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
	</msxsl:script>

</xsl:stylesheet>