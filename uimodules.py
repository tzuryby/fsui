#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import tornado.web

class HeaderModule(tornado.web.UIModule):
    def render(self, global_client_params={}):
        return self.render_string("uimodules/header.html", global_client_params=global_client_params)
    
class FooterModule(tornado.web.UIModule):
    def render(self, global_client_params={}):
        return self.render_string("uimodules/footer.html", global_client_params=global_client_params)
     
class TitleModule(tornado.web.UIModule):
    def render(self, global_client_params={}):
        return self.render_string("uimodules/title.html", global_client_params=global_client_params)
