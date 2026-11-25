/*! - v1.0
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

(function () {
    var dispatcher;
    if (this.isExtended) {
        return;
    }
    dispatcher = _.extend({}, Backbone.Events, {
        cid: "dispatcher"
    });
    return _.each([ Backbone.Collection.prototype, Backbone.Model.prototype, Backbone.View.prototype, Backbone.Router.prototype], function (proto) {
        return _.extend(proto, {
            global_dispatcher: dispatcher
        });
    });
})();