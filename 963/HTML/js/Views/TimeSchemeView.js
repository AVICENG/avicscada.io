/*globals ECALENDAR, Backbone, _, $, window, setTimeout */

$(function () {
    "use strict";

    ECALENDAR.TimeSchemeView = Backbone.View.extend({

        scrollIntoViewEnabled: false,
        selectDefault: true,
        initialize: function (options) {
            this.$timeSchemeListTable = $('<div class="disabled TimeSchemeListTable"></div>');

            if (options.selectDefault === false) {
                this.selectDefault = false;
            }
            if (options.scrollIntoViewEnabled === true) {
                this.scrollIntoViewEnabled = true;
            }

            if (!options.el) {
                this.$el = $('#TimeSchemeViewElement');
                this.el = this.$el.get(0);
            }
            if (!this.options.timeSchemeSelection) {
                this.options.timeSchemeSelection = ECALENDAR.TimeSchemeSelection;
            }

            if ($(".lblTimeSchemeListServerFeedback", this.$el).length === 0) {
                this.$el.append('<div class="lblTimeSchemeListServerFeedback"></div>');
            }

            //rendering
            this.$el.append('<div class="text timeSchemeLabel">' + (options.title || ECALENDAR.ApplicationStrings.getResourceFromID('CONFIGURED_SCHEMES')) + ": </div>");
            this.$el.append(this.$timeSchemeListTable);
            this.render();
            this.bindEvents();

        },
        bindEvents: function () {

            this.model.bind('reset', this.render, this);
            this.global_dispatcher.bind('sending_data:weekSetCollection:fetch', this.showLoading, this);
            this.global_dispatcher.bind('sending_data_complete:weekSetCollection:fetch', this.hideLoading, this);

        },
        unbindEvents: function () {
            this.model.unbind('reset', this.render, this);
        },
        showLoading: function () {
            $('.timeSchemeLabel', this.$el).addClass('loading');
        },
        hideLoading: function () {
            $('.timeSchemeLabel', this.$el).removeClass('loading');
        },
        render: function () {
            var data = {};
            this.$timeSchemeListTable.empty().addClass('disabled').data('cache', data);

            if (this.model.models.length > 0 && this.model.at(0).id !== -1) {

                var htmlString = this.createHTML(this.model), collection = this.model;

                if (htmlString !== "") {

                    this.$timeSchemeListTable.removeClass('disabled').append(htmlString);

                    if (ECALENDAR.DiaryGroupSelection.get('diaryGroup') && ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isFolder') === true) {
                        this.$timeSchemeListTable.addClass('FolderTimeSchemeListTable');
                    }
                    else {
                        this.$timeSchemeListTable.removeClass('FolderTimeSchemeListTable');
                    }

                    //Resetting the label of the weekset for IE7, label with leading spaces where removed automatically when we create DIV having label with space.
                    //For more detail refer JIRA item: 963-265
                    $(".label-part", this.$timeSchemeListTable).each(function (index) {
                        var label = collection.at(index).get("label");
                        if ((index === 0) && (ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isFolder') === false) && (collection.at(index).get('isDefault') === true) && collection.at(index) instanceof ECALENDAR.WeekSetModel) {
                            label = '* ' + label;
                        }
                        $(this).html(label);
                    });
                    if (this.selectDefault === true) {
                        var timescheme = this.options.timeSchemeSelection.get('timeScheme');
                        if (timescheme !== null) {
                            if (timescheme.id > 0) {
                                this.setSelectedTimeSchemeById(timescheme.id);
                            }
                            else {
                                this.setSelectedTimeScheme(this.$timeSchemeListTable.find('.label-part:contains(' + timescheme.get('label') + ')'));
                            }
                        }
                        else {

                            this.setDefaultSelectedTimeScheme();
                        }
                    }


                    this.$timeSchemeListTable.unbind('click').bind('click', _.bind(
                        function (e) {
                            this.setSelectedTimeScheme($(e.target));
                        }, this));

                } else {
                    this.$timeSchemeListTable.addClass('disabled');
                    //TODO : Error message display
                }
            }
        },
        setDefaultSelectedTimeScheme: function () {
            if (this.model.length === 0) {
                this.options.timeSchemeSelection.set({ timeScheme: null });
                return;
            }

            var data = this.$timeSchemeListTable.data('cache') || this.$timeSchemeListTable.data('cache', {}).data('cache');
            data.selectedItem = this.$timeSchemeListTable.find(".tr:first").addClass("selected");

            this.options.timeSchemeSelection.set({ timeScheme: this.model.at(0) });

            if (data.selectedItem.length > 0) {
                this._scrollIntoView(data.selectedItem);
            }

        },
        _scrollIntoView: function (obj) {
            // 1 is the top border
            this.$timeSchemeListTable.scrollTop(obj.offset().top - this.$timeSchemeListTable.offset().top - 1);

        },
        setSelectedTimeSchemeById: function (id) {
            var data = this.$timeSchemeListTable.data('cache') || this.$timeSchemeListTable.data('cache', {}).data('cache'), $target, weeksetId;
            var self = this;
            if (id && (!data.hasOwnProperty('selectedItem') || parseInt(data.selectedItem.data('id'), 10) !== id)) {
                $target = this.$('.tr[data-id="' + id + '"]');
                if ($target.length > 0) {
                    this.setSelectedTimeScheme($target);
                    setTimeout(
                        function () {
                            self._scrollIntoView($target);
                        }, 0);
                }
                else {
                    this.setDefaultSelectedTimeScheme();
                }
            }

        },
        setSelectedTimeScheme: function ($target) {
            var data = this.$timeSchemeListTable.data('cache') || this.$timeSchemeListTable.data('cache', {}).data('cache'),
            $row = $target.closest('.tr'), id, models;
            if ($row.length === 0) {
                // don't do anything, click wasn't on a row.
                return;
            }

            if (data.selectedItem) {
                data.selectedItem.removeClass('selected');
            }
            data.selectedItem = $row.addClass('selected');
            id = parseInt($row.data('id'), 10);
            if (_.isNumber(id) && !_.isNaN(id)) {
                this.options.timeSchemeSelection.set({ timeScheme: this.model.get(id) });
            }
            else {
                models = this.model.where({ label: $row.find('.label-part').html() });
                if (models.length > 0) {
                    this.options.timeSchemeSelection.set({ timeScheme: models[0] });
                }
                else {
                    //something went wrong.
                    $row.removeClass('selected');
                    data.selectedItem = null;
                    this.options.timeSchemeSelection.set({ timeScheme: null });
                }
            }
        },
        createHTML: function (collection) {
            var i, weekSetModel, models, htmlString = "";
            if (collection !== null && collection !== undefined) {
                models = collection.models;
                for (i = 0; i < models.length; i += 1) {
                    weekSetModel = models[i];
                    htmlString += '<div class="tr iconpart" data-id="' + weekSetModel.id + '">';
                    htmlString += '<div class="colour-cell" style="background-color:' + weekSetModel.get("colour") + '">';

                    if ((i === 0) && (ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isFolder') === false) && weekSetModel instanceof ECALENDAR.WeekSetModel && weekSetModel.get('isDefault') === true) {
                        htmlString += '<div class="label-part pre">* ' + weekSetModel.get("label") + '</div></div></div>';
                    } else {
                        htmlString += '<div class="label-part pre">' + weekSetModel.get("label") + '</div></div></div>';
                    }
                }
            }
            return htmlString;
        }

    });
});