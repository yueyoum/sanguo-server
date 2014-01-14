# -*- coding:utf-8 -*-
"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'sanguo.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        self.children.append(modules.AppList(
            '帐号管理',
            column=1,
            collapsible=False,
            models=('django.contrib.*',),
            ))


        self.children.append(modules.AppList(
            '编辑器',
            column=1,
            collapsible=True,
            models=('apps.server.*',
                'apps.mail.*',
                ),
            ))

        self.children.append(modules.AppList(
            '游戏数据',
            column=1,
            collapsible=True,
            models=('apps.account.*',
                'apps.character.*',
                'apps.item.*',
                ),
            ))

        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('Media Management'),
            column=2,
            children=[
                {
                    'title': _('FileBrowser'),
                    'url': '/admin/filebrowser/browse/',
                    'external': False,
                },
            ]
        ))
        
        
        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=2,
        ))


