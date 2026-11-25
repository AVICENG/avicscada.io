/*!
* Backbone.sync
* This is the override function of the backbone.sync
*
* Date: Wed April 17, 2012
* Copyright 2008-2012 Honeywell Technologies Sarl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd.
*/

/*globals Backbone*/
/*globals ECALENDAR*/

Backbone.sync = function (method, model, options) {
    "use strict";

    var xml, url;
    var showNotImplemented = function () {
        model.global_dispatcher.trigger('sending_data_complete');
        model.global_dispatcher.trigger('user_messaging', 'Not implemented');
    };
    switch (method) {
        case "read":
            if (options.model === 'Diaries') {
                url = "DIARYGROUPSASXML" + "?SID=" + ECALENDAR.AppUtilities.SID;
            } else if (options.model === 'Weeksets') {
                url = "WEEKSETSFORGROUPASXML" + "?GroupID=" + options.diaryId + "&SID=" + ECALENDAR.AppUtilities.SID;
            } else if (options.model === 'Exceptions') {
                url = "EXCEPTIONCOLLECTIONASXML" + "?GroupID=" + options.diaryId + "&SID=" + ECALENDAR.AppUtilities.SID;
            }
            else if (options.model === 'SpecialDays') {
                url = "SPECIALDAYSASXML" + "?GroupID=" + options.diaryId + "&SID=" + ECALENDAR.AppUtilities.SID;
            }
            else if (options.model === 'WeeksetTimeChanges') {
                url = "CALENDARMARKERSASXML" + "?GroupID=" + options.diaryId + "&SID=" + ECALENDAR.AppUtilities.SID;
            }
            else {
                showNotImplemented(options.model);
                return;
            }
            return ECALENDAR.Communication.requestGET(url, options.success, options.error);

        case "create":
            if (model instanceof ECALENDAR.WeekSetModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateWeeksetXML(model);
                url = "HandleNewWeekSet" + "?SID=" + ECALENDAR.AppUtilities.SID;
            } else if (model instanceof ECALENDAR.ExceptionCollection) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateExceptionCollectionXML(model);
                url = "HandleNewExceptionCollection" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption;
            }
            else if (model instanceof ECALENDAR.SpecialDayModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateSpecialDayXML(model);
                url = "HandleNewSpecialDay" + "?SID=" + ECALENDAR.AppUtilities.SID;
            }
            else if (model instanceof ECALENDAR.WeekSetTimeChangeModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateWeekSetTimeChangeXML(model);
                url = "HandleChangeDefaultWeekSet" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption + "&GroupID=" + model.get('groupId');
            }
            else if (model instanceof ECALENDAR.ImportTimeSchemeModel) {
            xml = ECALENDAR.WeekSetModelXMLGenerator.generateImportTimeSchemeXML(model);
                url = "HandleImportTimeScheme" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption + "&GroupID=" + options.groupId;
            }
            else {
                showNotImplemented();
            }
            ECALENDAR.Communication.requestPOST(url, xml, options.success, options.error);
            break;

        case "update":
            if (model instanceof ECALENDAR.ExceptionCollection) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateExceptionCollectionXML(model);
                url = "HandleEditExceptionCollection" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption;
            }
            else if (model instanceof ECALENDAR.SpecialDayModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateSpecialDayXML(model);
                url = "HandleEditSpecialDay" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption;
            }
            else if (model instanceof ECALENDAR.WeekSetModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateWeeksetXML(model);
                url = "HandleEditWeekSet" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption;
            }
            else {
                //TODO: Call the appropriate function to do the ajaxing and notifying the server.
                showNotImplemented();
            }
            ECALENDAR.Communication.requestPOST(url, xml, options.success, options.error);
            break;

        case "delete":
            if (model instanceof ECALENDAR.ExceptionCollection) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateDeleteExceptionCollectionXML(model);
                url = "HandleDeleteExceptionCollection" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption;
            }
            else if (model instanceof ECALENDAR.SpecialDayModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateSpecialDayXML(model);
                url = "HandleDeleteSpecialDay" + "?SID=" + ECALENDAR.AppUtilities.SID + "&DOWNLOAD=" + ECALENDAR.AppUtilities.downloadOption;
            }
            else if (model instanceof ECALENDAR.WeekSetModel) {
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateDeleteWeekSetXML(model, options.newDefaultWeekSetSettings);
                url = "HandleDeleteWeekSet" + "?SID=" + ECALENDAR.AppUtilities.SID;
            }
            else if (model instanceof ECALENDAR.WeekSetTimeChangeModel) {
                url = "HandleDeleteMarker" + "?SID=" + ECALENDAR.AppUtilities.SID + "&GroupID=" + model.get('groupId');
                xml = ECALENDAR.WeekSetModelXMLGenerator.generateDeleteDateXML(model.get('date'));
            }
            else {
                showNotImplemented();
            }

            //TODO: Call the appropriate function to do the ajaxing and notifying the server.
            ECALENDAR.Communication.requestPOST(url, xml, options.success, options.error);
            break;
    }

};