$(function() {
    "use strict";

    ECALENDAR.ChangeDefaultTimeSchemeView = Backbone.View.extend({
        template: _.template('<select id="changeDefaultTimeSchemeList" name=""><%= options %></select>'),
        events: {
            'click #btnDefaultTimeSchemeOK': 'OK_clicked',
            'click #btnDefaultTimeSchemeCancel': 'Cancel_clicked'
        },
        initialize: function() {
            if (!this.collection) {
                this.collection = ECALENDAR.weekSetCollection;
            }
            this.$el = $("#ChangeDefaultTimeScheme");
            this.el = this.$el.get(0);
            if (!this.options.timeSchemeSelection) {
                this.options.timeSchemeSelection = ECALENDAR.TimeSchemeSelection;
            }

            this.collection.bind('reset', this.render, this);
            this.render();

            this.$el.dialog({
                height: 200,
                width: 300,
                resizable: false,
                draggable: true,
                modal: true,
                title: ECALENDAR.ApplicationStrings.getResourceFromID('DELETE_DEFAULT_WEEKSET_TITLE'),
                buttons: [
                    {
                        text:ECALENDAR.ApplicationStrings.getResourceFromID('OK'),
                        click: _.bind(this.OK_clicked, this),
                        id: "btnDefaultTimeSchemeOK",
                        "class": "btn-primary"
                    },
                    {
                        text:ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL'),
                        click:_.bind(this.Cancel_clicked, this),
                        id: "btnDefaultTimeSchemeCancel"
                    }
               ]
            });
        },
        render: function() {
            var firstItem = 'selected="selected"';
            var createOptions = function(m) {
                var result = _.template('<option value="<%=value%>" <%=selected%>><%= text %></option>',
                {
                    text: m.get('label'),
                    value: m.get('weekSetID'),
                    selected: firstItem
                });
                firstItem = '';
                return result;
            };

            var options = '', cnt = 0;
            if (ECALENDAR.DiaryGroupSelection.get('diaryGroup') !== null) {
                for (cnt = 0; cnt < this.collection.length; cnt++) {
                    var model = this.collection.at(cnt);
                    if (model.get('isDefault') !== true) { options += createOptions(model); }
                }
            }
            this.$el.html(this.template({ options: options,
                ok_button_text: ECALENDAR.ApplicationStrings.getResourceFromID('OK'),
                cancel_button_text: ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL')
            }));
            this.changeDefaultTimeSchemeList = $('#changeDefaultTimeSchemeList');
            return this;
        },

        OK_clicked: function() {
            var index = this.changeDefaultTimeSchemeList.attr("value");
            //Update WeekSetTimeChangeModel model here, don't commit the changes to the server as view generator should be making the changes 
            var defaultWeekSetChangeModel = new ECALENDAR.WeekSetTimeChangeModel();
            defaultWeekSetChangeModel.set({ weekSetId: parseInt(index, 10),
                label: this.changeDefaultTimeSchemeList.text,
                groupId: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID')
            });
            //Now the weekset as user has selected new weekset.
            this.destroyWeekset(defaultWeekSetChangeModel);
            this.$el.dialog('destroy').empty();
        },

        destroyWeekset: function(defaultWeekSetChangeModel) {
            var self = this;
            this.global_dispatcher.trigger('sending_data');
            this.options.timeSchemeSelection.get('timeScheme').destroy({
                success: function(model, resp) {
                    model.set('timeScheme', null);
                    self.global_dispatcher.trigger('sending_data_complete', model);
                    self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', model);
                    self.undelegateEvents();
                },
                error: function(model, resp) {
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
                            self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', model);
                        }
                        self.global_dispatcher.trigger('sending_data_complete', model);
                        self.undelegateEvents();
                    }
                },
                newDefaultWeekSetSettings: defaultWeekSetChangeModel
            });
        },

        Cancel_clicked: function() {
            this.$el.dialog('destroy').empty();
            this.undelegateEvents();
        }
    });
});