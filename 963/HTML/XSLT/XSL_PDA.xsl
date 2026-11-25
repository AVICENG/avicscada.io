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
			
			<body bgcolor="#FFFFFF" topmargin="0" leftmargin="0" rightmargin="0" bottommargin="0">
			
				<!--
				//
				// formatting of the top of the page with different 963 bannaers and logos
				// also includes refresh button
				//
				-->
				<A NAME="PageTop"></A>				
				
				
				<!-- hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh -->
				
				<table width="100%" height="72" cellspacing="0" cellpadding="0" border="0">
					<tr>
						<!-- first column of main table-->
						<td bgcolor="#ff6600" width="40px" valign="top">
						<CENTER>
								<img src="/html/images/pda963.gif"></img>
								<BR></BR>
								<a href="javascript:location.reload(true)">
									<img src="/html/images/pdaRefresh.gif" title="Refresh Page" width="22" height="16" border="0"></img>
								</a>
						</CENTER>
						</td>
						
						<!-- second column of main table -->
						<td valign="top">
						
							<TABLE WIDTH="100%">
								<TR>
									<TD VALIGN="TOP">
										<!-- MAIN PAGE CODE HERE -->
										
										<table width="100%" height="20" cellspacing="0" cellpadding="0" border="0">
										
											<tr align = "left">
												<td align="left">							
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
												<td align="left">							
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
										
										
										<!-- EXAMPLE DYNAMIC DATA -->
										
										<!--
										//
										// line break
										//
										-->
										<br></br>
										
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
										// display the column headings for the dynamic data table
										// a template to fill the table with dynamic data is embedded/called from here
										//
										-->
										
										<table cellpadding="5" ID="DynamicData" width="100%">
										
											<!-- <COLGROUP span="3" width="10"></COLGROUP> -->
										
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
													<xsl:value-of select = "$IDS1_ACTION">
													</xsl:value-of>
												</td>
												
											</tr>
																													
											<xsl:apply-templates select = "Schematic/Objects/DynamicObj">					
											</xsl:apply-templates>
										</table>				
										
										<!-- EXAMPLE STATIC DATA-->
										
										<!--
										//
										// display the heading of static data
										//
										-->		
										<br></br>
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
										// display the column headings for the static data table
										// a template to fill the table with static data is embedded/called from here
										//
										-->
										
										<table cellpadding="5" ID="StaticData" width="100%"> <!-- white -->
												
											<!-- <COLGROUP span="2" width="50%"></COLGROUP> -->
											
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
										
										
										<BR></BR>
										
										<div>
											<small>
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
											</small>
										</div>										
										
										<!-- END OF MAIN PAGE CODE -->
									</TD>
								</TR>
							</TABLE>
						</td>
					</tr>
					
					<tr>
						<td>
							<img src="/html/images/pdaSwish.gif"></img>
						</td>
						<td valign="middle">
							<small>
								<div align = "left">												
									<a href = "http://www.trend-controls.com" align = "left">
										<xsl:value-of select = "$IDS1_COPY_RIGHT">
										</xsl:value-of>
									</a>
									<br></br>
									
									<a href = "/html/WebHelp/963_manu.htm" align = "left">
										<xsl:value-of select = "$IDS1_VIEW_HELP">
										</xsl:value-of>
									</a>
									<br></br>																	
									
										
								</div>			
							</small>
						</td>
					</tr>
					
				</table>			
				
				
				<!-- hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh -->
				
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
			<xsl:variable name = "isAlarm" select = "./DynamicModuleStatus/AlarmText">
			</xsl:variable>	
			
			<!-- in case of no alarm-->
			<xsl:if test = "string-length($isAlarm) = 0">
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
			</xsl:if>
			
			<!-- in case of alarm -->
			
			<xsl:if test = "string-length($isAlarm) > 0"> 			
				<xsl:choose>
					<xsl:when test = "substring(@Item,1,1) = 'S'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/sensor.gif" align="absBottom" title="Sensor"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>
														
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'D'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/driver.gif" align="absBottom" title="Driver"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'K'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/knob.gif" align="absBottom" title="Knob"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>		
							
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'I'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/digitalinputs.gif" align="absBottom" title="Digital Input"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'W'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/switch.gif" align="absBottom" title="Switch"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'Z'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/timezone.gif" align="absBottom" title="Time Zone"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'X'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/internalsensor.gif" align="absBottom" title="Internal Sensor"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>		
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:when test = "substring(@Item,1,1) = 'M'">
						<td bgcolor = "#FF0000">
							<img src="/html/images/critcalalarm.gif" align="absBottom" title="Internal Sensor"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>		
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:when>
					
					<xsl:otherwise>				
						<td bgcolor = "#FF0000">
							<img src="/html/images/critcalalarm.gif" align="absBottom" title="Internal Sensor"></img>
							<xsl:value-of select = "' '">
							</xsl:value-of>	
							<font size="2" color="#FFFFFF"> 	
								<xsl:value-of select = "@Label">
								</xsl:value-of>
							</font>
						</td>			
					</xsl:otherwise>
				</xsl:choose>
			</xsl:if>
					
			<td class="data">
				<xsl:value-of select = "./DynamicModuleStatus/FormattedLatestValue">
				</xsl:value-of>
			</td>
			
			<td class="data">
				<!-- action here in the same column along with value -->
				
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
	// DisplayLabelWithAlarmColor
	//
	-->

	<xsl:template name = "DisplayLabelWithAlarmColor">
		
		<xsl:variable name = "isAlarm" select = "./DynamicModuleStatus/AlarmText">
		</xsl:variable>		
		
		<xsl:if test = "string-length($isAlarm) > 0"> 			
			<td>
			
			</td>
		</xsl:if>							
		
		<xsl:if test = "string-length($isAlarm) = 0"> 			
			<td class="data">
			
			</td>
		</xsl:if>
					
	</xsl:template>

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
					<xsl:value-of select = "'WIDTH: 16'">
					</xsl:value-of>
				</xsl:attribute>				
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'Graph'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'image'">
					</xsl:value-of>
				</xsl:attribute>			
							
				<xsl:attribute name = "src">
					<xsl:value-of select = "'/html/images/pdaGraph.gif'">
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
					<xsl:value-of select = "'BACKGROUND-COLOR: #ffffff; WIDTH: 30'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'NewValue'">
					</xsl:value-of>
				</xsl:attribute>
			</xsl:element>
			
			<xsl:element name = "INPUT">			
				<xsl:attribute name = "style">
					<xsl:value-of select = "'WIDTH: 16'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'image'">
					</xsl:value-of>
				</xsl:attribute>		
				
				<xsl:attribute name = "src">
					<xsl:value-of select = "'/html/images/pdaSubmit.gif'">
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
			
			<xsl:element name = "SELECT">
				<xsl:element name = "OPTION">
					<xsl:value-of select = "'On'">
					</xsl:value-of>
				</xsl:element>
				
				<xsl:element name = "OPTION">
					<xsl:value-of select = "'Off'">
					</xsl:value-of>
				</xsl:element>
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
					<xsl:value-of select = "'WIDTH: 16'">
					</xsl:value-of>
				</xsl:attribute>
												
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'image'">
					</xsl:value-of>
				</xsl:attribute>		
				
				<xsl:attribute name = "src">
					<xsl:value-of select = "'/html/images/pdaSubmit.gif'">
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
		
		<br></br>
		
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
					<xsl:value-of select = "'WIDTH: 16'">
					</xsl:value-of>
				</xsl:attribute>
				
				<xsl:attribute name = "NAME">
					<xsl:value-of select = "'Graph'">
					</xsl:value-of>
				</xsl:attribute>			
				
				<xsl:attribute name = "TYPE">
					<xsl:value-of select = "'image'">
					</xsl:value-of>
				</xsl:attribute>			
							
				<xsl:attribute name = "src">
					<xsl:value-of select = "'/html/images/pdaGraph.gif'">
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