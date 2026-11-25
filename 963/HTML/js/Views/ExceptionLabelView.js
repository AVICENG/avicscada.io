/*! - v1.0
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */
/*globals Modernizr*/

$(function () {
    "use strict";
    ECALENDAR.ExceptionLabelView = Backbone.View.extend({
        template: _.template('<div class="form-horizontal"><fieldset id="NameFieldset" class="fieldset"><legend><%= HTML_TITLE_NAME %></legend>' +
        '<p><%= HTML_TEXT_NAME %></p>' +
        '<div class="control-group"><label for="exceptionlabel" class="control-label"><%=HTML_LABEL_NAME %></label>' +
        '<div class="controls"><input type="text" id="exceptionlabel" name="exceptionlabel" value="<%= label %>" /><span class="bubble-anchor"></span></div></div></fieldset>' +
		'<fieldset id="RepetitionFieldset" class="fieldset"><legend><%= HTML_TITLE_REPETITION %></legend>' +
        '<p><%= HTML_TEXT_REPETITION %></p>' +
        '<div class="checkbox inline">' +
        '<input id="yearlyrepeated" type="checkbox" name="yearlyrepeated" value="yearlyrepeated" <%= checked %>><label for="yearlyrepeated"><%= HTML_LABEL_REPETITION %></label></div></fieldset></div>'),
        initialize: function () {
            this.model.bind('error', this._showErrors, this);
            this.render();
        },
        render: function () {
            function getResource(id) {
                return ECALENDAR.ApplicationStrings.getResourceFromID(id);
            }
            this.$el.html(this.template(_.extend(this.model.at(0).toJSON(),
            { 
                HTML_LABEL_NAME: getResource('LABEL_NAME'),
                HTML_TEXT_NAME: getResource('TEXT_ADD_EXCEPTION_NAME'),
                HTML_TITLE_NAME: getResource('LABEL_NAME'),
                HTML_LABEL_REPETITION: getResource('LABEL_EXCEPTION_REPEAT_YEARLY'),
                HTML_TEXT_REPETITION: getResource('TEXT_EXCEPTION_REPEAT_YEARLY'),
                HTML_TITLE_REPETITION: getResource('TITLE_EXCEPTION_REPEAT_YEARLY'),
                checked: ((this.model.at(0).get('sameEveryYear') === true) ? 'checked="checked"' : '')
            }
			))); 
        },
        events: {
            'change #exceptionlabel': '_labelChangeEventHandler',
            'focus #exceptionlabel': '_clearErrors',
            'change #yearlyrepeated': '_repetitionChangeEventHandler'
        },
        _labelChangeEventHandler: function (e) {



            if (this.model.length > 0) {
                this.model.each(function (m) {
                    m.set('label', e.target.value, { silent: true });
                });
            }
            else {
                this.model.add(new ECALENDAR.ExceptionModel({ label: e.target.value }), { silent: true });
            }
        },
        _clearErrors: function (e) {
            var elements = (e) ? $(e.target).closest('.control-group') : this.$el.find('.error');
            elements.removeClass('error').find('.alert-error').remove();
        },
        _showErrors: function (model, errors) {
            this._clearErrors();

            _.each(errors, _.bind(function (error) {
                if (error.name === 'label') {
                    this.$el.find('#exceptionlabel').closest('.control-group').addClass('error').find('.bubble-anchor').append('<label for="exceptionlabel" class="alert alert-error"><button class="close" data-dismiss="alert">x</button>' + error.error + '</label>');
                }
            }, this));
        },
        _repetitionChangeEventHandler: function (e) {
            if (this.model.length > 0) {
                this.model.each(function (m) {
                    m.set('sameEveryYear', $(e.target).is(':checked'), { silent: true });
                });
            }
            else {
                this.model.add(new ECALENDAR.ExceptionModel({ sameEveryYear: $(e.target).is(':checked') }), { silent: true });
            }
            
        }


    });

});