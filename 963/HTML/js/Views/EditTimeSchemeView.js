/*! - v1.0
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */
/*globals Modernizr*/

$(function () {
    "use strict";
    ECALENDAR.EditTimeSchemeView = Backbone.View.extend({

        events: {
            "click #btnEditTimeSchemeViewCancel": "_btnEditTimeSchemeViewCancel_Click",
            "click #btnEditTimeSchemeViewSubmit": "_btnEditTimeSchemeViewSubmit_Click",
            "focus #txtWeekSetName": "_txtWeekSetName_Focus",
            "click #ColourPicker": "_color1_Click",
            "click #colorLabel": "_colorLabel_Click"
        },
        template: '<div class="row-fluid">' +
                    '<div class="span6 form-horizontal label-column">' +
                    '<div class="control-group" id="TextBoxDiv">' +
                    '<label for="txtWeekSetName" class="control-label"><%= weekset_label %>:</label>' +
                    '<div class="controls">' +
                    '<input type="text" id="txtWeekSetName" value="<%= weekset_value %>" tabindex="1" class="span12" />' +
                    '<span class="bubble-anchor" id="txtWeekSetError"></span></div></div>' +
                    '<div class="control-group" id="ColourPicker" >' +
                    '<label  tabindex="1" class="control-label" id="colorLabel" for="color1"><%= color_picker_label %>:</label>' +
                    '<div class="controls">' +
                    '<input id="color1" type="text" name="color1" value="<%= colour %>"/>' +
                    '<span class="bubble-anchor" id="txtWeekSetColourError"></span></div></div>' +
                    '</div>' +
                    '<div class="span6 form-horizontal timing-column">' +
                    '<div class="control-group" id="start-time">' +
                    '<label class="control-label" for="start-time-input"><%= start_time_label %>:</label><div class="controls"><input  tabindex="1" disabled="disabled" type="text" name="start" id="start-time-input" class="time-input" value="<%= start_time_value %>"/></div>' +
                    '</div>' +
                    '<div class="control-group" id="end-time">' +
                    '<label class="control-label" for="end-time-input"><%= end_time_label %>:</label><div class="controls"><input tabindex="1" disabled="disabled" type="text" name="end" id="end-time-input" class="time-input" value="<%= end_time_value %>"/></div>' +
                    '</div>' +
                    '</div>' +
                    '</div>' +
                    '<div class="row-fluid"><div class="span12">' +
                    '<span id="activationTimePlannerWidgetError" class="bubble-anchor point-down"></span>' +
                    '<div id="activationTimePlannerWidgetElement" ></div>' +

                    '</div></div>' +
                    '<div class="row-fluid btn-row"><div class="span12"><button id="btnEditTimeSchemeViewSubmit" class="btn btn-primary"><%= edit_button_text %></button><button id="btnEditTimeSchemeViewCancel" class="btn"><%= cancel_button_text %></button></div></div>',
        initialize: function (options) {
            var plannerEventHandler, self = this, html, ignoreIE8 = false;
            html = $('html');
            if (!html.hasClass('lt-ie9') || html.hasClass('lt-ie8')) {
                ignoreIE8 = true;
            }

            if (!options.el) {
                this.$el = $('#EditTimeSchemeViewElement');
                this.el = this.$el.get(0);
            }
            //Create here the activation time planner widget here.
            //It has been assumed that in already have an embedded HTML element inside view HTML element to hold the activation time planner widget.
            // Add the div for   Activation time planner widget

            this.$el.append(_.template(this.template, { weekset_label: ECALENDAR.ApplicationStrings.getResourceFromID("LABEL_NAME"),
                weekset_value: this.model.get('label'),
                colour: (this.model.isNew()) ? '#333399' : this.model.get('colour'),
                color_picker_label: ECALENDAR.ApplicationStrings.getResourceFromID("CHOOSE_COLOUR"),
                cancel_button_text: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_CANCEL"),
                edit_button_text: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_SUBMIT"),
                start_time_label: ECALENDAR.ApplicationStrings.getResourceFromID("START_TIME"),
                end_time_label: ECALENDAR.ApplicationStrings.getResourceFromID("END_TIME"),
                start_time_value: "",
                end_time_value: ""
            }));

            $('#start-time-input').TimeInput({ timechanged: $.proxy(this._setStartTime, this) }).TimeInput('disableControl');
            $('#end-time-input').TimeInput({ timechanged: $.proxy(this._setEndTime, this) }).TimeInput('disableControl');


            plannerEventHandler = function (start, end, ignoreIE8) {
                return function (e, ui) {

                    function getTimeValue(o) {
                        if (!o || !o.hour) {
                            return "";
                        }
                        return [o.hour, o.minute, '00'].join(':');
                    }
                    function enableTimeBoxes() {

                        start.TimeInput('enableControl');
                        end.TimeInput('enableControl');
                    }
                    function disableTimeBoxes() {
                        start.TimeInput('disableControl');
                        end.TimeInput('disableControl');
                    }

                    if (e.type === 'activationtimeplannertimeperiod_removed' || (ui.start.hour === ui.end.hour && ui.start.minute === ui.end.minute)) {
                        disableTimeBoxes();
                        return;
                    }


                    enableTimeBoxes();

                    if (ignoreIE8 || e.type !== 'activationtimeplannertimeperiod_move') {
                        start.TimeInput("setTime", ui.start.hour, ui.start.minute);
                        end.TimeInput("setTime", ui.end.hour, ui.end.minute);
                    }

                };
            } ($('#start-time-input'), $('#end-time-input'), ignoreIE8);



            //TODO: In the Edit weekset task, please pass the appropriate object of the WeekSetModel.
            this.planner = this.$('#activationTimePlannerWidgetElement').activationTimePlanner({
                maxNumOfActivationPeriods: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('maxPeriods'),
                timeperiod_selected: plannerEventHandler,
                timeperiod_move: plannerEventHandler,
                timeperiod_resize: plannerEventHandler,
                timeperiod_move_end: plannerEventHandler,
                timeperiod_removed: plannerEventHandler,
                weekSetModelObject: this.model,
                eventListeningObject: this.$el
            });



            //Create here colour picker control.
            this.$('#color1').colorPicker();
            var height = 540;
            if (this.model instanceof ECALENDAR.SpecialDayModel) {
                height = 260;
            }
            this.$el.dialog({
                height: height,
                width: 700,
                resizable: false,
                draggable: true,
                modal: true,
                title: ECALENDAR.ApplicationStrings.getResourceFromID('NEW_WEEKSET_TITLE')
            });

            this.$el.bind("dialogclose", function () {
                self.$el.unbind('dialogclose');
                self._destroyTimePlannerWidget(self.options);
            });



            this.txtWeekSetName = this.$("#txtWeekSetName");
            this.TextBoxDiv = this.$("#TextBoxDiv");
            this.txtWeekSetError = this.$("#txtWeekSetError");
            this.txtWeekSetColourError = this.$("#txtWeekSetColourError");
            this.activationTimePlannerWidgetError = this.$("#activationTimePlannerWidgetError");

            this.createContextMenu();

        },
        createContextMenu: function () {
            var self = this, buildMenu = function (trigger) {

                var items = {};
                if (trigger.hasClass('timePeriodStyle')) {
                    items.deletePeriod = { name: ECALENDAR.ApplicationStrings.getResourceFromID('Delete') };
                    items.sep1 = "---";
                }
                items.onAllDay = { name: ECALENDAR.ApplicationStrings.getResourceFromID('ON_ALL_DAY') };
                items.offAllDay = { name: ECALENDAR.ApplicationStrings.getResourceFromID('OFF_ALL_DAY') };
                items.sep2 = "---";
                if (self.model instanceof ECALENDAR.WeekSetModel) {
                    items.onAllWeek = { name: ECALENDAR.ApplicationStrings.getResourceFromID('ON_ALL_WEEK') };
                    items.offAllWeek = { name: ECALENDAR.ApplicationStrings.getResourceFromID('OFF_ALL_WEEK') };
                    items.sep3 = "---";
                }
                items.cutDay = { name: ECALENDAR.ApplicationStrings.getResourceFromID('CUT_DAY'), disabled: !self.planner.activationTimePlanner('canCopyOrCut', trigger) };
                items.copyDay = { name: ECALENDAR.ApplicationStrings.getResourceFromID('COPY_DAY'), disabled: !self.planner.activationTimePlanner('canCopyOrCut', trigger) };
                items.pasteDay = { name: ECALENDAR.ApplicationStrings.getResourceFromID('PASTE_DAY'), disabled: !self.planner.activationTimePlanner('canPaste') };
                items.sep4 = "---";
                if (self.model instanceof ECALENDAR.WeekSetModel) {
                    items.pasteWorkingWeek = { name: ECALENDAR.ApplicationStrings.getResourceFromID('PASTE_WORKING_WEEK'), disabled: !self.planner.activationTimePlanner('canPaste') };
                    items.pasteWeek = { name: ECALENDAR.ApplicationStrings.getResourceFromID('PASTE_WEEK'), disabled: !self.planner.activationTimePlanner('canPaste') };
                }
                return { items: items };
            }, confirmAction = function (options) {
                var opts = { title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM') };
                var buttons = {};
                buttons[ECALENDAR.ApplicationStrings.getResourceFromID('YES')] = function () {
                    $(this).dialog('close');
                    options.yes();
                };
                buttons[ECALENDAR.ApplicationStrings.getResourceFromID('NO')] = function () {
                    $(this).dialog('close');

                };
                opts.buttons = buttons;
                self.global_dispatcher.trigger('warning', options.msg, opts);
            }, callback = function (key, options) {
                var $trigger = options.$trigger;
                switch (key) {
                    case "deletePeriod":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('DELETE_PERIOD'),
                            yes: function () {
                                self.planner.activationTimePlanner('removeTimePeriod', $trigger);
                            }
                        });

                        break;
                    case "onAllDay":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('ON_ALL_DAY_CONFIRM'),
                            yes: function () {
                                self.planner.activationTimePlanner('onAllDay', $trigger);
                            }
                        });
                        break;
                    case "onAllWeek":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('ON_ALL_WEEK_CONFIRM'),
                            yes: function () {
                                self.planner.activationTimePlanner('onAllWeek', $trigger);
                            }
                        });
                        break;
                    case "onWorkingWeek":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('ON_ALL_WEEK_CONFIRM'),
                            yes: function () {
                                self.planner.activationTimePlanner('onWorkingWeek', $trigger);
                            }
                        });
                        break;
                    case "offAllDay":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('OFF_ALL_DAY_CONFIRM'),
                            yes: function () {
                                self.planner.activationTimePlanner('offAllDay', $trigger);
                            }
                        });
                        break;
                    case "offAllWeek":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('OFF_ALL_WEEK_CONFIRM'),
                            yes: function () {
                                self.planner.activationTimePlanner('offAllWeek', $trigger);
                            }
                        });
                        break;
                    case "offWorkingWeek":
                        confirmAction({
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('OFF_ALL_WEEK_CONFIRM'),
                            yes: function () {
                                self.planner.activationTimePlanner('offWorkingWeek', $trigger);
                            }
                        });
                        break;
                    case "cutDay":
                        self.planner.activationTimePlanner('cutDay', $trigger);

                        break;
                    case "copyDay":

                        self.planner.activationTimePlanner('copyDay', $trigger);

                        break;
                    case "pasteDay":
                        if (self.planner.activationTimePlanner('isDayEmpty', $trigger)) {
                            self.planner.activationTimePlanner('pasteDay', $trigger);
                        } else {
                            confirmAction({
                                msg: ECALENDAR.ApplicationStrings.getResourceFromID('PASTE_WEEK_CONFIRM'),
                                yes: function () {
                                    self.planner.activationTimePlanner('pasteDay', $trigger);
                                }
                            });
                        }
                        break;
                    case "pasteWorkingWeek":
                        if (self.planner.activationTimePlanner('isWorkingWeekEmpty', $trigger)) {
                            self.planner.activationTimePlanner('pasteWorkingWeek', $trigger);
                        } else {
                            confirmAction({
                                msg: ECALENDAR.ApplicationStrings.getResourceFromID('PASTE_WEEK_CONFIRM'),
                                yes: function () {
                                    self.planner.activationTimePlanner('pasteWorkingWeek', $trigger);
                                }
                            });
                        }
                        break;
                    case "pasteWeek":
                        if (self.planner.activationTimePlanner('isWeekEmpty', $trigger)) {
                            self.planner.activationTimePlanner('pasteWeek', $trigger);
                        } else {
                            confirmAction({
                                msg: ECALENDAR.ApplicationStrings.getResourceFromID('PASTE_WEEK_CONFIRM'),
                                yes: function () {
                                    self.planner.activationTimePlanner('pasteWeek', $trigger);
                                }
                            });

                        }
                        break;
                }
            };

            $.contextMenu({
                selector: '.ui-dialog .timePeriodStyle, .ui-dialog .dayContainer',
                build: buildMenu,
                callback: callback
            });
        },
        //Handler for Cancel button click
        _btnEditTimeSchemeViewCancel_Click: function () {
            this._destroyTimePlannerWidget(this.options);

        },

        //Handler for Submit button click
        _btnEditTimeSchemeViewSubmit_Click: function () {
            var dataModelFromTimePlanner, groupID, validationPassed, self = this, label;
            function commitToServer() {
                if (self.global_dispatcher != null) {
                    self.global_dispatcher.trigger('sending_data');
                }
                // You have to supply the first 2 args before the options in order for the callbacks to work.                
                dataModelFromTimePlanner.save('groupId', parseInt(groupID, 10),
                    { //Here starts the options
                        success: function (model, resp) {
                            self._destroyTimePlannerWidget(self.options);
                            self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', [model]);
                            self.global_dispatcher.trigger('sending_data_complete');
                        },
                        error: function (model, resp) {
                            if (self.global_dispatcher != null) {

                                //In case if some error appears at server, it is being sent in XML as <Error> error-description </Error>
                                //If there is no error message as response - it means server has succeesully completed the request.
                                var xmlDoc, $xmlDoc, errorMsg = null;
                                if (resp != null) {
                                    if (resp.responseText != null && resp.responseText !== "") {
                                        xmlDoc = $.parseXML(resp.responseText);
                                        $xmlDoc = $(xmlDoc);
                                        errorMsg = $xmlDoc.find("Error").text();
                                    }
                                }
                                if (errorMsg === null || errorMsg.length === 0) {
                                    //It seems a communication error or might be server not available error.
                                    self.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                                } else {
                                    self.global_dispatcher.trigger('user_messaging', [errorMsg]);
                                    self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', [model]);
                                }
                                self.global_dispatcher.trigger('sending_data_complete');
                            }
                        }
                    });

            }

            dataModelFromTimePlanner = this.$('#activationTimePlannerWidgetElement').activationTimePlanner('getWeeksetDataModel');

            label = this.txtWeekSetName.val();

            if (dataModelFromTimePlanner instanceof ECALENDAR.WeekSetModel && ECALENDAR.weekSetCollection.doesLabelExist(label, dataModelFromTimePlanner)) {

                this._processValidationError([{ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('DUPLICATE_LABEL')}]);

                return;
            }
            validationPassed = dataModelFromTimePlanner.set({ label: label, colour: this.$('#color1').val() }, {
                error: function (model, response) {
                    self._processValidationError(response);
                }
            });


            if (validationPassed) {



                groupID = ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID');


                if (self.global_dispatcher && ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("isAssociatedWithTimeZones") && !dataModelFromTimePlanner.isNew()) {
                    self.global_dispatcher.trigger('download', commitToServer);
                } else {
                    commitToServer();
                }


            }
        },
        _clearError: function (control) {
            control.empty().closest('.control-group').removeClass('error');
        },
        //This method removes all the associate validation errors.
        _txtWeekSetName_Focus: function () {
            this._clearError(this.txtWeekSetError);
        },

        //This method will removes all the associated validation errors.
        _color1_Click: function (event) {
            if (event.srcElement) {
                if ((event.srcElement.id !== "colorLabel") && (event.srcElement.id !== "txtWeekSetColourError")) {
                    this._clearError(this.txtWeekSetColourError);
                }
            }
        },
        _colorLabel_Click: function () {
            $('.colorPicker-picker').click();
        },
        _setEndTime: function (e, ui) {
          
            if (!Modernizr.inputtypes.time && e.type === 'time') {
                return;
            }
            var hours = ui.time.getHours(), minutes = ui.time.getMinutes();

            if (ui.time.getHours() === 0 && ui.time.getDate() > new Date(0).getDate()) {
                hours = 24;
            }

            this.planner.activationTimePlanner('updateEndTime', [(hours * 60) + minutes]);

        },
        _setStartTime: function (e, ui) {
            
            if (!Modernizr.inputtypes.time && e.type === 'time') {
                return;
            }
            var hours = ui.time.getHours(), minutes = ui.time.getMinutes();
            if (ui.time.getHours() === 0 && ui.time.getDate() > new Date(0).getDate()) {
                hours = 24;
            }

            this.planner.activationTimePlanner('updateStartTime', [(hours * 60) + minutes]);

        },
        //Process validation error
        _processValidationError: function (response) {
            var i;
            $('.control-group').removeClass('error').find('.bubble-anchor').empty();

            function showError(obj, msg) {
                var html = '<span class="alert alert-error"><button class="close" data-dismiss="alert">x</button>' + msg + '</span>';
                obj.html(html).closest('.control-group').addClass('error');
            }

            //Label attribute validation should be sufficient. Widget controls have their own validation mechanism.
            for (i = 0; i < response.length; i = i + 1) {
                if (response[i].name === "label") {
                    showError(this.txtWeekSetError, response[i].error);
                }
                if (response[i].name === "colour") {
                    showError(this.txtWeekSetColourError, response[i].error);

                }
                if ((response[i].name === "weeksetID") || (response[i].name === "days")) {
                    //This will always update the last error as we know both of they can have validation error message as "Internal error".
                    showError(this.activationTimePlannerWidgetError, response[i].error);

                }
            }
        },

        //Destroy the activation time planner widget
        _destroyTimePlannerWidget: function (options) {


            if (options && options.callback) {
                options.callback();
            }

            $.contextMenu('destroy', '.ui-dialog .timePeriodStyle, .ui-dialog .dayContainer');

            this.planner.activationTimePlanner('destroy');
            $('.colorPicker-palette').remove();

            this.$el.dialog('destroy').empty();

            //Unbind all the events as we are distroying the view now.
            this.undelegateEvents();
        }
    });
});