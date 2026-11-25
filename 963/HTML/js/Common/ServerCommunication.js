/*! - v1.0
* ServerCommunication.js
*
* This class provides communication functionality with Server. All the ajax call must be made from this class.
*
* Date: Friday June 29, 2012
* Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. 
* Copyright 1995-2008 Trend Control Systems Ltd.
*/

/*globals ECALENDAR*/
/*globals $ */

$(function () {
	"use strict";

    var ServerCommunication = function () {

		this.keepAliveTimeManager = function () {

			var self, keepAliveTimer, keepAliveFunction, anyUX;
			anyUX = false;
			self = this;
			
			keepAliveFunction = function () {
				if (anyUX) {
					self.keepAlive();
					anyUX = false;
				} else {
					clearInterval(keepAliveTimer);
					keepAliveTimer = null;
				}
			};

			//this will work iff event.stopPropagation() is never called in other handlers
			$(document).click(function () {
				anyUX = true;
				if (keepAliveTimer == null) {
					keepAliveTimer = setInterval(keepAliveFunction, 20000);
				}
			});

			keepAliveTimer = setInterval(keepAliveFunction, 20000);
        };

		this.keepAlive = function () {
			var url;
			url = "KEEPALIVE" + "?SID=" + ECALENDAR.AppUtilities.SID;
			this.requestGET(url, null, null);
		};


        //Provides functionality to perform the  of GET HTTP ajax request.
        //Parameters: 
        //url - location where to make the GET request.
        //successCallback - callback function when the ajax communication happens successfully.
        //errorCallback - callback function when the ajax communication has error.
        this.requestGET = function (url, successCallback, errorCallback) {
            return $.ajax({
                type: 'GET',
                url: url,
                dataType: 'xml',
                error: errorCallback,
                success: successCallback
            });
        };


        //This function is abstractation layer of POST HTTP ajax request.
        //Parameters: 
        //url - location where to make the POST request
        //xml - xml request.
        //successCallback - callback function when the ajax communication happens successfully.
        //error - callback function when the ajax communication has error.
        this.requestPOST = function (url, xml, successCallback, errorCallback) {
            $.ajax({
                type: 'POST',
                url: url,
                data: xml,
                dataType: 'text',
                error: errorCallback,
                success: successCallback
            });
        };

        //A method to request the user information from server.
        this.requestUserInformation = function (successCallback, errorCallback) {

            //URL to get the user information
            var url = "CANCONFIGDIARYTIMES" + "?SID=" + ECALENDAR.AppUtilities.SID;
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'xml',
                success: successCallback,
                error: errorCallback
            });
        };

		this.keepAliveTimeManager();

    };

    ECALENDAR.Communication = new ServerCommunication();
});