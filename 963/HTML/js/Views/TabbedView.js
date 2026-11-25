/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */
/*globals Modernizr*/



$(function() {
    "use strict";
    ECALENDAR.TabbedView = Backbone.View.extend({
        template: _.template('<div class="row-fluid tab-view"><ul id="<%= id %>" class="nav nav-tabs"></ul></div>'),
        tabItemTemplate: _.template('<li data-index="<%=id%>"><a href="#"><%=tab_text%></a></li>'),
        tabItemPanelTemplate: _.template('<div class="tab-page" data-index="<%=id%>"></div>'),
        selectedTab: {},
        subViews: [],
        events: {
            'click .nav-tabs': '_tabClickEventHandler'
        },
        initialize: function() {
            this.render();
        },
        render: function() {
            var tabs, tabItems = [], container;
            // create basic layout
            this.$el.html(this.template({ id: this.id }));
            container = this.$el.find('.tab-view');
            tabs = this.$el.find('.nav-tabs');

            //for each tab in the collection, create tab and add to temporary location, create page & instantiate view on it and add to panel
            _.each(this.model.models, _.bind(function(m) {
                tabItems.push(this.tabItemTemplate({ id: m.cid, tab_text: m.get('tabText') }));
                var viewPage = $(this.tabItemPanelTemplate({ id: m.cid }));
                container.append(viewPage);
                this.subViews.push(new m.attributes.view(_.extend({ el: viewPage }, m.get('viewparams'))));
            }, this));

            // add tabs from temp location to dom.
            tabs.append(tabItems.join(''));
            this._setSelectedTab(tabs.find('li:eq(0)'));

            return this;
        },
        _tabClickEventHandler: function(e) {
            this._setSelectedTab($(e.target).closest('li'));
            return false;
        },
        _setSelectedTab: function(tab) {
            if (tab.length === 0) {
                return;
            }
            if (this.selectedTab.tab) {
                this.selectedTab.tab.removeClass('active');
                this.selectedTab.page.removeClass('active');
            }
            this.selectedTab.tab = tab.addClass('active');
            this.selectedTab.page = $('.tab-page[data-index="' + tab.data('index') + '"]').addClass('active');
        },
        _destroy: function() { }

    });

});