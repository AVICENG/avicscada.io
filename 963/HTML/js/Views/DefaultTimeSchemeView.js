/*globals ECALENDAR, Backbone, _, $, window, setTimeout, document */

$(function () {
    "use strict";

    ECALENDAR.DefaultTimeSchemeView = Backbone.View.extend({
        template: _.template('<select id="DefaultTimeSchemeList" name="" <%= disabled %>><%= options %></select>'),
        events: {
            'change #DefaultTimeSchemeList': 'defaultTimeScheme_changed',
            'focus #DefaultTimeSchemeList': 'deselect',
            'blur #DefaultTimeSchemeList': 'reselect'
        },
        reselect: function (event) {
            if (event.target.selectedIndex === -1) {
                event.target.selectedIndex = this.currentIndex;
            }

        },
        deselect: function (event) {

            if (event.target.selectedIndex !== -1 || this.currentIndex === undefined) {
                this.currentIndex = event.target.selectedIndex;
            }

            event.target.selectedIndex = -1;
        },
        initialize: function () {
            if (!this.collection) {
                this.collection = ECALENDAR.weekSetCollection;
            }
            this.collection.bind('reset', this.render, this);
            this.render();

            ECALENDAR.weeksetTimeChanges.bind('reset', this._showHidePostponedMessage, this);



        },
        _alert: function () {
            return $('<div id="postponedMsg" class="alert alert-info alert-static">' + ECALENDAR.ApplicationStrings.getResourceFromID('CHANGE_PENDING') + '</div>');
        },
        _showHidePostponedMessage: function (model) {
            var alert = this.$('#postponedMsg');
            if (model.length > 0) {
                if (alert.length === 0) {
                    this.$el.append(this._alert());
                }
            }
            else {
                if (alert.length > 0) {
                    alert.remove();
                }
            }

        },
        render: function () {
            var selectedItem = 'selected="selected"';
            var createOptions = function (m) {


                var result = _.template('<option value="<%=value%>" <%=selected%>><%= text %></option>',
                {
                    text: m.get('label'),
                    value: m.get('weekSetID'),
                    selected: ((m.get('isDefault')) ? selectedItem : '')
                });


                return result;
            };

            var options = '', disabled = 'disabled="disabled"';
            if (ECALENDAR.DiaryGroupSelection.get('diaryGroup') !== null) {
                if (ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isFolder') === true && this.collection.getDefaultWeekSet() === null) {
                    options = '<option value=""></option>';

                }
                options += this.collection.map(createOptions).join('');
                if (this.collection.length > 0) {
                    disabled = '';

                }
            }



            this.$el.html(this.template({ options: options, disabled: disabled }));
            this._showHidePostponedMessage(ECALENDAR.weeksetTimeChanges);
            return this;
        },
        defaultTimeScheme_changed: function (event) {
            var self = this,
            postponedDate = null,
            timeschemeSelect = event.target,
            timeschemeSelectValue = event.target.value,
            timeschemeSelectText = event.target.options[event.target.selectedIndex].text,
            cancelChangeTimeScheme = function () {

                timeschemeSelect.selectedIndex = self.currentIndex;
                $(this).dialog('close');
            },
            commitToServer = function (successCallback) {
                var triggerSendingComplete = function () {
                    if (this.global_dispatcher) {
                        this.global_dispatcher.trigger('sending_data_complete');
                    }
                };

                var model = new ECALENDAR.WeekSetTimeChangeModel({
                    date: postponedDate,
                    weekSetId: timeschemeSelectValue,
                    label: timeschemeSelectText,
                    groupId: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID')
                });

                model.global_dispatcher.trigger('sending_data');

                model.save(null, {
                    success: function (model, resp) {
                        triggerSendingComplete.call(model);
                        if (successCallback && typeof successCallback === 'function') {
                            successCallback();
                        }

                        if (ECALENDAR.TimeSchemeSelection.get('timeScheme') instanceof ECALENDAR.WeekSetModel) {
                            ECALENDAR.TimeSchemeSelection.set('timeScheme', null);
                        }
                        model.global_dispatcher.trigger('view_messaging:defaultTimeChangeUpdated');
                    },
                    error: function (model, resp) {
                        triggerSendingComplete.call(model);


                        if (model.global_dispatcher != null) {

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
                                model.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                            } else {
                                model.global_dispatcher.trigger('user_messaging', [errorMsg]);
                            }
                        }
                        timeschemeSelect.selectedIndex = self.currentIndex;
                        model.global_dispatcher.trigger('view_messaging:defaultTimeChangeUpdated');

                    }
                });
            },
            saveChangeToDefaultTimeScheme = function () {
                var successCallback, dialogElement = this;

                if (postponedDate === null) {
                    $(this).dialog('close');
                    //Immediate change asks to configure when to download.
                    self.global_dispatcher.trigger('info', ECALENDAR.ApplicationStrings.getResourceFromID('DEFAULT_SCHEME_SET_TO_WHITE'), {
                        close: function () {
                            $(this).dialog('destroy').remove();
                            // in this situation, server seems to always ask to download now or later, whether associated with zones or not.                    
                            self.global_dispatcher.trigger('download', commitToServer);
                        }
                    });

                } else {
                    successCallback = function () {
                        $(dialogElement).dialog('close');
                    };
                    commitToServer(successCallback);
                }

            },

            closeDialog = function (event, ui) {
                // note: context is the dialog widget

                if (event.which) {
                    //User cancelled by other means (esc or X button)
                    cancelChangeTimeScheme.call(this);
                    return;
                }
                $(this).dialog("destroy").remove();
            },
            showCalendarWhenUserWantsToPostponeChange = function () {
                var element = document.createElement('div');
                var appends = [];
                var _addPostponedChanges = function (inst) {
                    var calendar = this; // the event comes from the calendar view therefore context is the calendar

                    if (ECALENDAR.weeksetTimeChanges) {
                        ECALENDAR.weeksetTimeChanges.each(function (m) {
                            appends.push(function (id, indicator) {
                                return function () {
                                    $(id, inst.dpDiv).find("span:first").append('<span class="datepicker-indicator" data-id="' + indicator + '"><span></span></span>');
                                };
                            } (calendar.getID(m.get('date')), m.cid));

                        });

                        if (appends.length > 0) {
                            setTimeout(function () {
                                inst.dpDiv.css('visibility', 'hidden');
                                _.each(appends, function (f) {
                                    f();
                                });
                                inst.dpDiv.css('visibility', 'visible');
                            }, 0);
                        }
                    }

                };
                var calendarView = new ECALENDAR.CalendarView({ el: element, collection: new Backbone.Collection(), rows: 1, columns: 3 });
                calendarView.bind('calendar_generated', _addPostponedChanges);

                calendarView.$el.dialog({
                    modal: true,
                    height: 350,
                    width: 800,
                    resizable: false,
                    draggable: true,
                    title: ECALENDAR.ApplicationStrings.getResourceFromID('SELECT_DATE'),
                    buttons: [
                        {
                            id: "button-ok",
                            text: ECALENDAR.ApplicationStrings.getResourceFromID('OK'),
                            click: saveChangeToDefaultTimeScheme,
                            disabled: 'disabled'
                        },
                        {
                            id: "button-cancel",
                            text: ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL'),
                            click: cancelChangeTimeScheme
                        }
                    ],
                    close: function (event, ui) {
                        closeDialog.call(this, event, ui);

                        calendarView.unbind('singledate_selected');
                    }
                });

                calendarView.trigger('calendar_generated', { dpDiv: calendarView.$el.dialog('widget') });


                calendarView.bind('singledate_selected', function (view, event) {
                    var okButton = calendarView.$el.dialog('widget').find('button').blur().filter('#button-ok');
                    postponedDate = view.start;

                    if (postponedDate.getTime() < new Date().setHours(48, 0, 0, 0)) {
                        okButton.button('disable');
                        view.global_dispatcher.trigger('user_messaging', ECALENDAR.ApplicationStrings.getResourceFromID('CHOOSE_A_DATE_AFTER_TOMORROW'));
                        return;
                    }

                    if (ECALENDAR.weeksetTimeChanges.length > 0 && postponedDate <= ECALENDAR.weeksetTimeChanges.last().get('date')) {
                        okButton.button('disable');
                        view.global_dispatcher.trigger('user_messaging', ECALENDAR.ApplicationStrings.getResourceFromID('CHOOSE_A_DATE_AFTER_LAST_DATE').replace('%d', ECALENDAR.weeksetTimeChanges.last().get('date').toLocaleDateString()));
                        return;
                    }

                    okButton.button('enable').focus();
                });
                var tooltip = null;
                calendarView.$el.bind('mouseover', function (event) {
                    var srcElement;
                    if (event.target.className === "datepicker-indicator" || event.target.parentNode.className === "datepicker-indicator" && tooltip === null) {
                        srcElement = $(event.target).closest('.datepicker-indicator');
                        srcElement.unbind('mouseleave').bind('mouseleave', function (event) {

                            $(this).unbind('mouseleave');
                            tooltip.hide();
                            tooltip = null;

                        });
                        tooltip = new ECALENDAR.PostponedWeeksetChangeTooltipView({
                            model: ECALENDAR.weeksetTimeChanges.getByCid(srcElement.data('id')),
                            animate: true,
                            el: srcElement
                        });
                    }
                });
                $(this).dialog('close');
            },
            showAreYouSureWhenUserDoesNotWantToPostponeChange = function () {
                var options, buttons = {};

                $(this).dialog('close');

                buttons[ECALENDAR.ApplicationStrings.getResourceFromID('YES')] = saveChangeToDefaultTimeScheme;
                buttons[ECALENDAR.ApplicationStrings.getResourceFromID('NO')] = cancelChangeTimeScheme;

                options = { title: ECALENDAR.ApplicationStrings.getResourceFromID('ARE_YOU_SURE'), buttons: buttons, close: closeDialog };

                self.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('CHANGE_TIMES_CHOICE'), options);

            };

            var options, buttons = {};

            buttons[ECALENDAR.ApplicationStrings.getResourceFromID('YES')] = showCalendarWhenUserWantsToPostponeChange;
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID('NO')] = showAreYouSureWhenUserDoesNotWantToPostponeChange;
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL')] = cancelChangeTimeScheme;

            options = {
                title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM'),
                buttons: buttons,
                close: closeDialog

            };

            // show first dialog - ask the user if they want to postpone the change.
            this.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('POSTPONE_CHOICE'), options);
        }

    });
});