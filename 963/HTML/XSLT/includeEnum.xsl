<?xml version="1.0" encoding="utf-8"?>
<!-- XSLT VERSION 1.00 4 JULY 2006-->
<xsl:stylesheet version = "1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

	<!--
	//
	// Dynamic Module Status Enumerations
	//
	-->
	<xsl:variable name="WHENINV" select="0" />
	<xsl:variable name="WHENON" select="1" />
	<xsl:variable name="WHENOFF" select="2" />
	<xsl:variable name="WHENINALARM" select="3" />
	<xsl:variable name="WHENWAITING" select="4" />
	<xsl:variable name="WHENOVERRIDDENON" select="5" />
	<xsl:variable name="WHENOVERRIDDENOFF" select="6" />
	<xsl:variable name="WHENERROR" select="7" />
	<xsl:variable name="WHENNORMAL" select="8" />
	<xsl:variable name="WHENCONFIGIN" select="9" />

</xsl:stylesheet>