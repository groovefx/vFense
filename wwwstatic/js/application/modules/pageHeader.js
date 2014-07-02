define(
    ['jquery', 'underscore', 'backbone', 'app', 'crel', 'modules/navBar', 'modules/customerDropdown', 'text!templates/pageHeader.html'],
    function ($, _, Backbone, app, crel, DashNav, customerDropdown, headerTemplate) {
        'use strict';
        var PageHeader = {};
        PageHeader.View = Backbone.View.extend({
            tagName: 'header',
            id: 'pageHeader',
            template: headerTemplate,
            initialize: function () {
                this.listenTo(app.user, 'sync', this.checkAdminPermission);
                app.user.fetch();
                return this;
            },
            render: function () {
                var tmpl = _.template(this.template),
                    user = app.user.toJSON();
                this.$el.html(tmpl(user));
                this.customerDropdown = new customerDropdown.View();
                this.$('#dashboardNav')
                    .find('.nav.pull-right')
                    .append(this.customerDropdown.render().el);

                return this;
            },
            checkAdminPermission: function () {
                if (app.user.isAdmin()) {
                    if (!this.$('a[href="#admin/users"]').length) {
                        this.$('#userMenu')
                            .find('.divider')
                            .before(crel('li', crel('a', {'href': '#admin/users'}, 'Admin Settings')));
                    }
                } else {
                    this.$('a[href="#admin/users"]').remove();
                }
            }
        });
        return PageHeader;
    }
);
