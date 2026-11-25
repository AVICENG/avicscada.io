/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $, setTimeout, document */

$(function () {
    "use strict";

    ECALENDAR.ExceptionListView = Backbone.View.extend({
        template: _.template('<div class="scrollable wizard-page active"><table class="table"><thead><tr><th><%= name %></th><th><%= start_date %></th><th><%= end_date %></th><th><%= same_every_year %></th><th><input id="selectAll" type="checkbox" class="selectAll" /></th><tr></thead><tbody><%= tbody %></tbody></table></div><div class="btn-row wizard-buttons"><button class="btn" id="deleteExceptions" disabled="disabled"><%=delete_exceptions%></button></div>'),
        itemtemplate: _.template('<tr><td><%=label%></td><td><%=formattedStartDate%></td><td><%=formattedEndDate%></td><td><%=sameEveryYearText%></td><td><input type="checkbox" class="selectSingle" data-id="<%=cid%>" /></td></tr>'),
        mapItems: function (m) {
            return this.itemtemplate(_.extend(m.toJSON(), {
                cid: m.cid,
                formattedStartDate: m.get('startDate').toLocaleDateString(),
                formattedEndDate: m.get('endDate').toLocaleDateString(),
                sameEveryYearText: m.sameEveryYearText()
            }));
        },
        initialize: function () {

            this.createCollection();

        },
        resetCollection: function () {
            this.createCollection();
            this.render();
        },
        createCollection: function () {
            var filter = {};
            filter[(this.model instanceof ECALENDAR.SpecialDayModel) ? 'specialDayID' : 'weeksetID'] = this.model.id;
            this.collection = new ECALENDAR.ExceptionCollection(ECALENDAR.exceptionCollection.where(filter));
        },
        render: function () {
            function getText(id) {
                return ECALENDAR.ApplicationStrings.getResourceFromID(id);
            }
            ECALENDAR.exceptionCollection.unbind('reset', this.resetCollection, this);
            ECALENDAR.exceptionCollection.bind('reset', this.resetCollection, this);

            this.$el.html(this.template({
                name: getText('LABEL_NAME'),
                start_date: getText('START_DATE'),
                end_date: getText('END_DATE'),
                same_every_year: getText('SAME_EVERY_YEAR'),
                delete_exceptions: getText('BTN_DELETE_EXCEPTION'),
                tbody: this.collection.map(this.mapItems, this).join('')
            }));
            if (this.cancelButton) {
                this.$('.wizard-buttons').append(this.cancelButton);
            }
            if (this.collection.length === 0) {
                this.$('#deleteExceptions').remove();
                this.$(':checkbox').remove();
            }

        },
        events: {
            "change input[type=checkbox]": "checkBoxChangeHandler",
            "click #deleteExceptions": "deleteExceptions",
            "click #cancel": "closeDialog"
        },
        checkBoxChangeHandler: function (event) {
            var $this = $(event.target), deleteButton = this.$('#deleteExceptions');

            if ($this.hasClass('selectAll')) {
                if ($this.is(':checked')) {
                    this.$(':checkbox').attr('checked', true);
                }
                else {
                    this.$(':checkbox').removeAttr('checked');
                }

            }
            else {
                if ($this.hasClass('selectSingle')) {
                    if (!$this.is(':checked')) {
                        this.$('.selectAll').removeAttr('checked');
                    }
                }
            }
            if (this.$(':checkbox:checked').length === 0) {
                deleteButton.attr('disabled', true);
            }
            else {
                deleteButton.removeAttr('disabled');
            }

        },
        deleteExceptions: function () {
            var exceptions = new ECALENDAR.ExceptionCollection();
            var addModelToException = function (i, v) {
                exceptions.add(this.collection.getByCid($(v).data('id')));
            };

            this.$('.selectSingle:checked').each(_.bind(addModelToException, this));

            if (exceptions.length > 0) {
                this.confirmDeleteExceptions(exceptions);
            }
        },
        confirmDeleteExceptions: function (exceptionDates) {
            var buttons, self = this;
            function commitToServer() {
                if (self.global_dispatcher != null) {
                    self.global_dispatcher.trigger('sending_data');
                }


                exceptionDates.destroy({
                    success: function () {
                        self.reloadExceptions(ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID'));
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
            buttons = {};
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID("YES")] = function () {
                $(this).dialog("close");
                if (self.global_dispatcher && ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("isAssociatedWithTimeZones")) {
                    self.global_dispatcher.trigger('download', commitToServer);

                } else {
                    commitToServer();
                }
            };
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID("NO")] = function () {
                $(this).dialog("close");
            };

            this.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('CONFIRM_DELETE_EXCEPTIONS'), {
                title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM'),
                buttons: buttons,
                close: function () {
                    $(this).dialog("destroy").remove();
                }
            });
        },
        dialog: function () {
            this.cancelButton = function () {
                return $('<button class="btn" id="cancel">' + ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL') + '</button>');
            };


            this.$el.dialog({
                height: 540,
                width: 700,
                resizable: false,
                draggable: true,
                modal: true,
                title: ECALENDAR.ApplicationStrings.getResourceFromID('WHERE_TIMES_USED')
            });



            this.$el.bind("dialogclose", _.bind(function () {
                this.$el.unbind('dialogclose');
                this._destroyView();
            }, this));
            this.render();

        },
        closeDialog: function () {
            this.$el.dialog('close');
        },
        _destroyView: function () {
            this.$el.dialog('destroy').remove();
            ECALENDAR.exceptionCollection.unbind('reset', this.resetCollection, this);
        },
        reloadExceptions: function (diaryId) {

            ECALENDAR.exceptionCollection.global_dispatcher.trigger('sending_data:exceptionCollection:fetch');
            // Get the up-to-dates exception collection from server
            ECALENDAR.exceptionCollection.fetch({
                success: function (collection, response) { // success callback for fetch
                    if (collection.global_dispatcher) {
                        collection.global_dispatcher.trigger('sending_data_complete:exceptionCollection:fetch');
                    }
                },
                error: function (collection, xhr, fetch) { // error callback for fetch
                    if (collection.global_dispatcher) {
                        collection.global_dispatcher.trigger('sending_data_complete:exceptionCollection:fetch');
                    }
                    if (xhr.statusText === "abort") {
                        return;
                    }
                    if (collection.global_dispatcher) {
                        collection.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("GET_EXCEPTION_ERROR")]);
                    }
                },
                model: "Exceptions",
                diaryId: diaryId
            });
        }


    });
});