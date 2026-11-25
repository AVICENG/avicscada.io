/*!
* Utilities class.   
* This class provides various utility functions used within the application.  
*
* Date: Wed April 12, 2012
* Copyright © 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright © 1995-2008 Trend Control Systems Ltd.
*/

/*jslint browser:true*/
/*globals ECALENDAR
 jQuery, $
document
*/

(function ($) {
    "use strict";

    var Utilities;
    Utilities = function () {

        var self = this;
        //This function returns true in case of given two area intersects each other.
        //Please note that these functions are written just to take care about the left and right edges of the rectangle.
        this.intersectLine = function (area1, area2) {

            if (area1 === null || area2 === null ||
					area1.right === null || area1.left === null ||
					area2.right === null || area2.left === null) {
                return false;
            }

            if ((parseFloat(area1.right, 10) > parseFloat(area2.left, 10)) && (parseFloat(area1.left, 10) < parseFloat(area2.right, 10))) {
                return true;
            }

            return false;
        };

        this.setRightToLeft = function () {
            if (ECALENDAR.ApplicationStrings.rtl) {
                $('body').attr('dir', 'rtl');
            }
        };

        this.setPageTitle = function (title) {
            document.title = title;
        };

        //This function's limitation is it initially design for one dimension.
        //Returns true if the child rectangle is completely inside the parent rectangle.
        //Else returns false.
        this.insideLine = function (parentLine, childLine) {

            //By default if any value is null - it would return false.
            if ((parentLine === null) || (parentLine === undefined) ||
						(childLine === null) || (childLine === undefined)) {
                return false;
            }

            if ((parseFloat(parentLine.left, 10) <= parseFloat(childLine.left, 10)) &&
					(parseFloat(parentLine.right, 10) >= parseFloat(childLine.right, 10))) {
                return true;
            }
            return false;
        };

        //Parse the query string and get the value of appropriate key.
        this.getQuerystringFromURL = function (key) {
            var search, params, i, pairs;
            search = decodeURI(location.search);
            if (search === "") {
                return "";
            }

            search = search.substr(1);
            params = search.split("&");
            for (i = 0; i < params.length; i += 1) {
                pairs = params[i].split("=");
                if (pairs[0] === key) {
                    return pairs[1];
                }
            }
            return "";
        };

        //Replace special characters.
        //It returns the modified the string. In case of errorneous input string it will send the same.
        this.replaceSpecialChar = function (input) {
            if ((input !== undefined) && (input !== null) && (input.length !== 0)) {
                input = input.replace(/&/g, "&amp;")
                                   .replace(/>/g, "&gt;")
                                   .replace(/</g, "&lt;")
                                   .replace(/"/g, "&quot;")
                                   .replace(/'/g, "&apos;");
            }
            return input;
        };

        this.SID = self.getQuerystringFromURL('SID');

        this.downloadOption = ECALENDAR.ApplicationConstants.downloadOptions.NEVER;

        this.createSessionApplet = function () {
            $('body').append('<div id="sessionapplet"><OBJECT classid="clsid:8AD9C840-044E-11D1-B3E9-00805F499D93" WIDTH="0" HEIGHT="0"><PARAM NAME="CODE" VALUE="com.novar.util.login.SessionApplet.class"/><PARAM NAME="ARCHIVE" VALUE="sessionapplet.jar"/><PARAM NAME="CODEBASE" VALUE="/html/java"/><PARAM NAME="type" VALUE="application/x-java-applet;version=1.6"/><PARAM NAME="string.encoding" VALUE="UTF8"/><PARAM NAME="session.token" VALUE="' +
                              ECALENDAR.AppUtilities.SID + '"/><PARAM NAME ="session.interval" VALUE="30"/><COMMENT><EMBED TYPE="application/x-java-applet;version=1.6" CODE="com.novar.util.login.SessionApplet.class" JAVA_CODEBASE="/html/java" ARCHIVE="sessionapplet.jar" WIDTH=0 HEIGHT=0 session.token="' +
                              ECALENDAR.AppUtilities.SID + '" session.interval="30" string.encoding ="UTF8" scriptable = false pluginspage = "http://java.sun.com/products/plugin/index.html#download"><NOEMBED></NOEMBED></EMBED></COMMENT></OBJECT></div>');
        };

        this.getContrastColour = function (colour) {
            var colours = [], red, green, blue, brightness;
            colours = colour.match(/^rgba?\(([0-9]{1,3})\s?,\s?([0-9]{1,3})\s?,\s?([0-9]{1,3})(?:\s?,?\s?[0-9.]+)?\)$/);
            function convertHex(hex) {
                return parseInt(hex.length === 1 ? hex.toString() + hex.toString() : hex, 16);
            }
            if (colours && colours.length === 4) {
                red = colours[1];
                green = colours[2];
                blue = colours[3];
            }
            else {
                colours = colour.match(/^#([a-fA-F0-9]{1,2})([a-fA-F0-9]{1,2})([a-fA-F0-9]{1,2})$/);
                //its a hex, convert to decimal
                if (colours && colours.length === 4) {
                    red = convertHex(colours[1]);
                    green = convertHex(colours[2]);
                    blue = convertHex(colours[3]);
                }

            }
            if (colours && colours.length === 4) {
                //4 being the whole string plus 3 pattern matches for r, g, b

                brightness = (0.299 * red) + (0.587 * green) + (0.114 * blue);
                if (brightness >= 125) {
                    return 'rgb(0, 0, 0)';
                }
            }

            return 'rgb(255, 255, 255)';
        };
    };

    ECALENDAR.AppUtilities = new Utilities();

} (jQuery));


