/*! - v1.0
*/

/*globals Backbone, _*/
/*globals DiaryModel*/
/*globals DiaryCollection*/
/*globals ECALENDAR*/
/*globals $*/


$(function () {
    "use strict";

    ECALENDAR.DisplayDiaryView = Backbone.View.extend({
        fetchModel: function () {
            var self = this;
            ECALENDAR.diaryCollectionObject = new ECALENDAR.DiaryCollection();
            this.model = ECALENDAR.diaryCollectionObject;
            this.model.bind('reset', function () {
                this.render();
            }, this);
            this.model.fetch({
                error: $.proxy(function (textStatus, response, options) { // unused parameters: jqXHR, err
                    var xmlDoc, $xmlDoc, errorMsg;
                    if (this.global_dispatcher != null) {
                        if (response === null ||
                            response === undefined ||
                            response.responseText === null ||
                            response.responseText === undefined ||
                            response.responseText === "") {
                            this.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("GET_DIARY_DATA_ERROR")]);
                        } else {
                            xmlDoc = $.parseXML(response.responseText);
                            $xmlDoc = $(xmlDoc);
                            errorMsg = $xmlDoc.find("Error").text();
                            this.global_dispatcher.trigger('user_messaging', [errorMsg]);
                        }
                    }


                }, this),
                model: "Diaries"
            });
        },
        render: function () {
            var dispatcher = this.global_dispatcher;
            this.$("#treeView").empty().TreeView({ diaryCollectionInputData: this.model, isRTL: ($('body').attr('dir') === "rtl"), itemSelected: _.bind(this._treeViewItemSelected, this) }).bind("loaded.jstree", function () {
                // If a diary group need to be pre-selected
                var groupID = ECALENDAR.AppUtilities.getQuerystringFromURL("GroupID");
                if (groupID != "") {
                    var diaryNode = $('li[databaseIndex=' + groupID + ']');
                    if (diaryNode.length > 0) {
                        $("#treeView").jstree('select_node', diaryNode);
                    }
                    else { 
                        var usermessage = ECALENDAR.ApplicationStrings.getResourceFromID("GROUP_DOES_NOT_EXIST") +
                                          ECALENDAR.ApplicationStrings.getResourceFromID("COUND_NOT_FIND").replace('%s', groupID);
                        dispatcher.trigger('user_messaging', [usermessage]);
                    }
                }
            });
        },
        _treeViewItemSelected: function (event, ui) {
            if ((this.options.diaryGroupSelection.get('diaryGroup') === null) || (ui.id !== this.options.diaryGroupSelection.get('diaryGroup').get('diaryID'))) {

                //Update the diary group selection index here.
                this.options.diaryGroupSelection.set({ diaryGroup: this.model.getModelFromId(ui.id) });
            }
        },
        initialize: function (options) {

            if (!options.el) {
                this.$el = $('#DisplayDiaryViewElement');
                this.el = this.$el.get(0);
            }

            if (!options.model) {
                this.fetchModel();
            }
            else {
                this.model.bind('reset', function () {
                    this.render();
                }, this);
                this.render();
            }



            if (!options.diaryGroupSelection) {
                this.options.diaryGroupSelection = ECALENDAR.DiaryGroupSelection;
            }

            this.global_dispatcher.bind('sending_data:DiaryGroupSelection:refreshData', $.proxy(function () {
                //todo: disabling buttons in this view should be in a helper function.
                if (this.selectedLeaf) {
                    this.selectedLeaf.removeClass('loading');
                }
                this.selectedLeaf = $('#treeView').TreeView('get_selected').addClass('loading');
            }, this));
            this.global_dispatcher.bind('sending_data_complete:DiaryGroupSelection:refreshData', $.proxy(function () {
                if (this.selectedLeaf) {
                    this.selectedLeaf.removeClass('loading');
                } else {
                    $('#treeView').TreeView('get_selected').removeClass('loading');
                }
            }, this));

        }
    });
});