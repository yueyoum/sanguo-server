from django.conf.urls import patterns, url

urlpatterns = patterns('',

                       url(r'^test/$', 'views.cmd.cmd'),

                       url(r'^pve/$', 'views.stage.views.pve'),
                       url(r'^pvp/$', 'views.stage.views.pvp'),

                       url(r'^formation/set/$', 'views.formation.views.set_formation'),
                       url(r'^socket/set/$', 'views.formation.views.set_socket'),
                       url(r'^hero/get/$', 'views.hero.views.pick_hero'),
                       url(r'^hero/merge/$', 'views.hero.views.merge_hero'),


                       url(r'^hang/$', 'views.stage.views.hang_start'),
                       url(r'^hang/cancel/$', 'views.stage.views.hang_cancel'),

                       url(r'^prize/$', 'views.prize.views.prize_get'),

                       url(r'^plunder/list/$', 'views.stage.views.plunder_list'),
                       url(r'^plunder/$', 'views.stage.views.plunder'),

                       url(r'^prison/open/$', 'views.prison.views.open_slot'),

                       url(r'^prisoner/train/$', 'views.prison.views.train'),
                       url(r'^prisoner/get/$', 'views.prison.views.get'),

                       url(r'^friend/player-list/$', 'views.friend.views.player_list'),
                       url(r'^friend/add/$', 'views.friend.views.add'),
                       url(r'^friend/cancel/$', 'views.friend.views.cancel'),
                       url(r'^friend/accept/$', 'views.friend.views.accept'),
                       url(r'^friend/refuse/$', 'views.friend.views.refuse'),
                       url(r'^friend/terminate/$', 'views.friend.views.terminate'),

                       url(r'^mail/open/$', 'views.mail.views.open'),
                       url(r'^mail/delete/$', 'views.mail.views.delete'),
                       url(r'^mail/getattachment/$', 'views.mail.views.get_attachment'),

                       url(r'daily/checkin/$', 'views.daily.views.checkin'),
                       url(r'daily/checkin/get-reward/$', 'views.daily.views.get_checkin_reward'),
)
