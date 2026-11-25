/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

$(function () {
    "use strict";
    ECALENDAR.BrowseIQZoneView = Backbone.View.extend({
        template: _.template('<table class="table table-bordered table-condensed"><thead><tr><th><%= site_name %></th><th><%= lan_name %></th><th><%= os_name %></th><th><%= zone_label %></th><th><%= item %></th><th><%= device_type %></th></tr></thead><%=body%></table>'),
        initialize: function () {
            this.model = ECALENDAR.DiaryGroupSelection;
            this.render();
            ECALENDAR.DiaryGroupSelection.bind('change', this.render, this);
        },
        render: function () {
            var rowTemplate = function (m) {
                return _.template("<tr><td><%= siteName %></td><td><%=lanName %></td><td><%= osName %></td><td><%= zoneLabel %></td><td><%= item %></td><td><%= deviceType %></td></tr>", m.toJSON());
            }, timezones = null;
            if (this.model.get('diaryGroup') && !this.model.get('diaryGroup').get('isFolder')) {
                timezones = this.model.get('diaryGroup').get('timeZones');

            }

            this.$el.html(this.template({
                body: ((timezones && timezones instanceof Backbone.Collection) ? timezones.map(rowTemplate).join('') : ""),
                site_name: ECALENDAR.ApplicationStrings.getResourceFromID("IQ_SITE_NAME"),
                lan_name: ECALENDAR.ApplicationStrings.getResourceFromID("IQ_LAN_NAME"),
                os_name: ECALENDAR.ApplicationStrings.getResourceFromID("IQ_OS_NAME"),
                zone_label: ECALENDAR.ApplicationStrings.getResourceFromID("IQ_ZONE_LABEL"),
                item: ECALENDAR.ApplicationStrings.getResourceFromID("IQ_ITEM"),
                device_type: ECALENDAR.ApplicationStrings.getResourceFromID("IQ_DEVICE_TYPE")
            }));

        }
    });

});