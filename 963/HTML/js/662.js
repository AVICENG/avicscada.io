
/*
 * JavaScript functions for the Java applets - DO NOT TRANSLATE
 * 
 */

/*
 * Adds the HTML for the login applet.
 */
function CreateLoginApplet(username, jreDownloadComment)
{

document.write('<OBJECT \
    classid = "clsid:8AD9C840-044E-11D1-B3E9-00805F499D93"\
    codebase = "http://java.sun.com/update/1.6.0/jinstall-6u29-windows-i586.cab#Version=1,6,29,0"\
    WIDTH = 400 HEIGHT = 150 ALIGN = center >\
    <PARAM NAME = CODE VALUE = com.novar.util.login.LoginApplet2.class >\
    <PARAM NAME = CODEBASE VALUE = /html/java >\
    <PARAM NAME = ARCHIVE VALUE = sessionapplet.jar,stringtable.jar >\
    <PARAM NAME = "type" VALUE = "application/x-java-applet;version=1.6">\
    <PARAM NAME = "scriptable" VALUE = "false">\
	<PARAM NAME = "string.encoding" VALUE = "UTF8">\
    <PARAM NAME = "username.default" VALUE="' + username + '">\
	<PARAM NAME = "security.encoding" VALUE="1">\
	\
	<COMMENT>\
	<EMBED \
            type = "application/x-java-applet;version=1.6" \
            CODE = com.novar.util.login.LoginApplet2.class \
            JAVA_CODEBASE = /html/java \
            ARCHIVE = sessionapplet.jar,stringtable.jar \
            WIDTH = 400 \
            HEIGHT = 150 \
            ALIGN = center \
            username.default ="' + username + '" \
			string.encoding ="UTF8" \
			security.encoding = "1" \
	    scriptable = false \
	    pluginspage = "http://java.sun.com/products/plugin/index.html#download">\
	    <NOEMBED></NOEMBED>\
	</EMBED>\
    </COMMENT>\
	' + jreDownloadComment + '\
</OBJECT>');

}

/*
 * Adds the HTML for the alarm viewer applet.
 */
function CreateAlarmApplet(username, sid)
{
	document.write('<APPLET CODE="com.novar.apps.alarms.AlarmViewer.class" CODEBASE="/html/java/" ARCHIVE="AlarmViewer.jar, led.jar, calendar.jar, stringtable.jar, imagetable.jar, imageButton.jar" WIDTH="100%" HEIGHT="80%">');
}

/*
 * Adds the HTML for the schematics applet.
 */
function CreateSchematicsApplet(appletWidth, appletHeight)
{
	if ((appletHeight == -1) || (appletWidth == -1))
	{
		document.write('<APPLET CODE=com.trend.apps.schematics.SchemApp.class CODEBASE="/html/java/" ARCHIVE="xmlschematics.jar, adjustments.jar, dynmod.jar, stringtable.jar, sessionapplet.jar, comms.jar, menus.jar, actions.jar" align="baseline" WIDTH="100%" HEIGHT="100%">');
	}
	else
	{
		document.write('<APPLET CODE=com.trend.apps.schematics.SchemApp.class CODEBASE="/html/java/" ARCHIVE="xmlschematics.jar, adjustments.jar, dynmod.jar, stringtable.jar, sessionapplet.jar, comms.jar, menus.jar, actions.jar" align="baseline" WIDTH="' + appletWidth + '" HEIGHT="' + appletHeight + '">');
	}
}

/*
 * Adds the HTML for the graph applet.
 */
function CreateGraphApplet()
{
	document.write('<APPLET CODE="com.novar.apps.graph.GraphApplet.class" CODEBASE="/html/java/" ARCHIVE="graph2.jar, dynmod.jar, stringtable.jar, calendar.jar" WIDTH="100%" HEIGHT="90%">');
}

/*
 * Adds the HTML for the device view applet.
 */
function CreateDeviceViewApplet()
{
	document.write('<APPLET CODE="com.trend.apps.deviceview.Applet.class" CODEBASE="/html/java/" ARCHIVE="dev.jar,dynmod.jar,adjustments.jar,stringtable.jar,comms.jar, menus.jar, actions.jar" WIDTH="100%" HEIGHT="100%">');
}

/*
 * Adds the HTML for the password changer applet
 */
function CreatePasswordChangerApplet(username, minlength, securemode)
{
	document.write('<APPLET CODE="com.novar.util.login.PasswordChangerApplet.class" CODEBASE="/html/java/" ARCHIVE="sessionapplet.jar,stringtable.jar" WIDTH="100%" HEIGHT="350">\
<PARAM NAME="user.name" VALUE="' + username + '">\r\n\
<PARAM NAME="password.minimumlength" VALUE="' + minlength + '">\r\n\
<PARAM NAME="server.command" VALUE="/ChangePwdOnLogin">\r\n\
<PARAM NAME="string.encoding" VALUE="UTF8">\r\n\
<PARAM NAME="security.encoding" VALUE = "1">\r\n\
<PARAM NAME="secure.mode" VALUE="' + securemode + '">\r\n\
</APPLET>');

}

/*
 * Adds a single <PARAM> element to an applet
 */
function AddAppletParameter(key, value)
{
	document.write('<PARAM NAME="' + key + '" VALUE="' + value + '">');
}

/*
 * Adds the closing </APPLET> tag
 */
function CreateAppletCloseTag()
{
	document.write('</APPLET>');
}
