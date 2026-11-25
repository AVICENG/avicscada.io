/*! - v1.0
*/

/*globals Backbone*/
/*globals _*/
/*globals ECALENDAR*/
/*globals $ */

$(function () {
    "use strict";

    ECALENDAR.DialogDisplayView = Backbone.View.extend({
        createDialog: function (msg, options, type) {
            options = options || {};
            var modalOptions = { width: 300,
                resizable: false,
                stacked: true,
                zIndex: 2000,
                modal: true,
                buttons: { "OK": function () {
                    $(this).dialog("close");
                }
                },
                close: function () {
                    $(this).dialog("destroy").remove();
                }
            };

            var dialogContainer = $("<div>" + (msg || "") + "</div>");

            dialogContainer.dialog(_.extend({}, modalOptions, options));

            if (options.removeTitleBar && options.removeTitleBar === true) {
                dialogContainer.dialog('widget').find('.ui-widget-header').remove();
            }
            else {
                dialogContainer.dialog("widget").find('.ui-widget-header').addClass(type);
            }

            return dialogContainer;
        },
        showHourGlass: function () {
            this.hideHourGlass();
            this.hourGlass = this.createDialog('<span class="hour-glass"></span>', { minWidth: 50, minHeight: 50, width: 60, closeOnEscape: false, buttons: {}, removeTitleBar: true });
            this.hourGlass.dialog('widget').addClass('hour-glass-dialog');

        },
        hideHourGlass: function () {
            if (this.hourGlass) {
                this.hourGlass.dialog('close');
                this.hourGlass = null;
            }
        },
        initialize: function () {

            //todo: language resources.
            //todo: generally for bootstrap information colour states. Not every country uses red/green for bad/good

            function handleErrorEvents(msg, opts) {
                this.createDialog(msg, _.extend({ title: ECALENDAR.ApplicationStrings.getResourceFromID("ERROR_OCCURED") }, opts), 'btn-danger');
            }
            function handleSuccessEvents(msg, opts) {
                this.createDialog(msg, _.extend({ title: ECALENDAR.ApplicationStrings.getResourceFromID("COMPLETE") }, opts), 'btn-success');
            }
            function handleInfoEvents(msg, opts) {
                this.createDialog(msg, _.extend({ title: ECALENDAR.ApplicationStrings.getResourceFromID("INFORMATION") }, opts), 'btn-info');

            }
            function handlePrimaryInfoEvents(msg, opts) {
                this.createDialog(msg, _.extend({ title: ECALENDAR.ApplicationStrings.getResourceFromID("INFORMATION") }, opts), 'btn-primary');
            }
            function handleWarningEvents(msg, opts) {
                this.createDialog(msg, _.extend({ title: ECALENDAR.ApplicationStrings.getResourceFromID("WARNING") }, opts), 'btn-warning');
            }

            function handleDownloadEvents(saveData) {
                var msg = _.template('<p><%= description %></p><br><label class="radio"><input type="radio" id="downloadNow" name="downloadOption" value="now" /><%= downloadNow %></label><br /><label class="radio"><input type="radio" id="downloadLater" name="downloadOption" value="later" checked="checked"/><%= downloadLater %></label>', {
                    description: ECALENDAR.ApplicationStrings.getResourceFromID("DOWNLOAD_DESCRIPTION"),
                    downloadNow: ECALENDAR.ApplicationStrings.getResourceFromID("DOWNLOAD_NOW"),
                    downloadLater: ECALENDAR.ApplicationStrings.getResourceFromID("DOWNLOAD_LATER")
                });
                ECALENDAR.AppUtilities.downloadOption = ECALENDAR.ApplicationConstants.downloadOptions.LATER;

                this.createDialog(msg, {
                    title: ECALENDAR.ApplicationStrings.getResourceFromID("DOWNLOAD_OPTIONS_TITLE"),
                    buttons: [
                        {
                            text: ECALENDAR.ApplicationStrings.getResourceFromID('OK'),
                            click: function () {
                                $(this).dialog("close");
                                saveData();
                            }
                        },
                        {
                            text: ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL'),
                            click: function () {
                                $(this).dialog("close");
                                ECALENDAR.AppUtilities.downloadOption = ECALENDAR.ApplicationConstants.downloadOptions.NEVER;
                                saveData();
                            }
                        }
                    ],
                    close: function () {
                        if ($("input[name=downloadOption]:checked").val() === "now") {
                            ECALENDAR.AppUtilities.downloadOption = ECALENDAR.ApplicationConstants.downloadOptions.NOW;
                        }
                        $(this).dialog("destroy").remove();
                    }
                }, 'btn-info');
            }

            this.global_dispatcher.bind('user_messaging', handleErrorEvents, this);
            this.global_dispatcher.bind('sending_data', this.showHourGlass, this);
            this.global_dispatcher.bind('sending_data_complete', this.hideHourGlass, this);

            this.global_dispatcher.bind('error', handleErrorEvents, this);
            this.global_dispatcher.bind('success', handleSuccessEvents, this);
            this.global_dispatcher.bind('info', handleInfoEvents, this);
            this.global_dispatcher.bind('primaryinfo', handlePrimaryInfoEvents, this);
            this.global_dispatcher.bind('warning', handleWarningEvents, this);
            this.global_dispatcher.bind('download', handleDownloadEvents, this);
        }
    });
});