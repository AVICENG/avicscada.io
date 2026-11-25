/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */
/*globals Modernizr*/



$(function () {
    "use strict";
    ECALENDAR.WizardView = Backbone.View.extend({

        className: 'wizard',
        template: _.template('<div class="wizard-sub-title"></div><div class="btn-row wizard-buttons"><button class="btn btn-back" disabled="disabled"><%= back_text %></button><button class="btn btn-next"><%= next_text %></button><button class="btn btn-cancel"><%= cancel_text %></button></div>'),
        itemTemplate: _.template('<div class="wizard-page wizard-page-<%= i %>"></div>'),
        selectedPage: {},
        events: {
            'click .btn-row': '_buttonClickHandler'
        },
        initialize: function (options) {
            this.subViews = [];
			this.selectedPage.index = 0;
        },
        render: function () {
            // create the wizard html that will contain the views.
            this.$el.html(this.template({
                back_text: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_BACK"),
                next_text: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_NEXT"),
                cancel_text: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_CANCEL")
            }));

            this._toggleNextFinishButton(1);

            //show wizard as dialog.
            this.$el.dialog({
                height: this.options.height || 540,
                width: this.options.width || 800,
                resizable: false,
                draggable: true,
                modal: true,
                title: this.options.title,
                close: function () {
                    $(this).dialog("destroy").remove();
                }
            }).dialog('widget').find('.ui-dialog-titlebar').addClass('btn-primary');

            // instantiate the first view
            if (this.model && this.model.models.length > 0) {
                this._createPage(0);
            }
            return this;
        },
        _showPage: function (page, index) {
            //deactivates the last viewed page and shows current page, store current page pointer in cache.
            if (this.selectedPage.page) {
                (this.subViews[this.selectedPage.index].unbindEvents || function () { }).call(this.subViews[this.selectedPage.index]);
                this.selectedPage.page.removeClass('active');
            }
            this.selectedPage.page = page.addClass('active');
            this.selectedPage.index = index;
            if (!this.hasAddedView) {
                (this.subViews[this.selectedPage.index].bindEvents || function () { }).call(this.subViews[this.selectedPage.index]);
            } else {
                delete this.hasAddedView;
            }
            this.$('.wizard-sub-title').text(this.model.models[index].get('tabText'));
        },
        _createPage: function (index) {
            // show page if it already exists, create page and add its view.
            var model = this.model.models[index], page = this.$el.find('.wizard-page-' + index);

            if (page.length > 0) {
                this._showPage(page, index);
                return;
            }
            page = $(this.itemTemplate({ i: index }));
            this.$el.find('.btn-row').before(page);
            this.subViews.push(new model.attributes.view(_.extend({ el: page }, model.get('viewparams'))));
            this.hasAddedView = true;
            this._showPage(page, index);
        },
        _enableButton: function (btn) {
            btn.removeAttr('disabled');
        },
        _disableButton: function (btn) {
            btn.attr('disabled', true);
        },
        _toggleNextFinishButton: function (pageIndex) {
            this[(pageIndex < this.model.models.length) ? '_showNextButton' : '_showFinishButton'](this.$el.find('button.btn-next'));
        },
        _showNextButton: function (btn) {
            btn.removeClass('btn-finish btn-primary').text(ECALENDAR.ApplicationStrings.getResourceFromID("BTN_NEXT"));
        },
        _showFinishButton: function (btn) {
            btn.addClass('btn-finish btn-primary').text(ECALENDAR.ApplicationStrings.getResourceFromID("BTN_FINISH"));
        },

        _buttonClickHandler: function (e) {
            var eventToRaise, $e, defaultToTrue, newIndex, currentView;
			eventToRaise = '';
			$e = $(e.target).closest('button');
            defaultToTrue = function () {
                return true;
            };
            if ($e.length === 0) {
                return;
            }
            if ($e.hasClass('btn-cancel')) {
                this.$el.dialog('close');
                return;
            }

            currentView = this.subViews[this.selectedPage.index];

            if ($e.hasClass('btn-next')) {
                if (!(currentView.options.onSubmit || defaultToTrue).call(currentView)) {
                    return;
                }
                newIndex = this.selectedPage.index + 1;
                eventToRaise = 'next_click';

            }
            if ($e.hasClass('btn-back')) {
                newIndex = this.selectedPage.index - 1;
                eventToRaise = 'back_click';

            }
            if ($e.hasClass('btn-finish')) {
                if (!(currentView.options.onSubmit || defaultToTrue).call(currentView)) {
                    return;
                }
                eventToRaise = 'finish_click';
            }

            if (eventToRaise !== 'finish_click') {

                this._createPage(newIndex);
                this[(newIndex === 0) ? '_disableButton' : '_enableButton'](this.$el.find('button.btn-back'));
                this._toggleNextFinishButton(newIndex + 1);
            }

            if (eventToRaise !== '') {
                this.trigger(eventToRaise, currentView);
            }

        },
        _destroy: function () {
            this.$el.dialog('destroy');
        }
    }
		);

});