from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^sync/$', 'views.world.views.sync'),
                       url(r'^resume/$', 'views.world.views.resume'),
                       url(r'^chat/send/$', 'views.chat.views.send'),
                       url(r'^test/$', 'views.cmd.cmd'),

                       url(r'^pvp/$', 'views.arena.views.arena_battle'),
                       url(r'^arena/panel/$', 'views.arena.views.arena_panel'),

                       url(r'^formation/set/$', 'views.formation.views.set_formation'),
                       url(r'^socket/set/$', 'views.formation.views.set_socket'),
                       url(r'^hero/get/$', 'views.heropanel.views.open'),
                       url(r'^heropanel/refresh/$', 'views.heropanel.views.refresh'),
                       url(r'^heropanel/start/$', 'views.heropanel.views.start'),


                       url(r'^prize/$', 'views.prize.views.prize_get'),

                       url(r'^plunder/list/$', 'views.plunder.views.plunder_list'),
                       url(r'^plunder/$', 'views.plunder.views.plunder'),

                       url(r'^prison/incr/$', 'views.prison.views.incr_prisoners_amount'),
                       url(r'^prisoner/addprob/$', 'views.prison.views.prisoner_add_prob'),
                       url(r'^prisoner/get/$', 'views.prison.views.prisoner_get'),

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

                       url(r'^teambattle/enter/$', 'views.teambattle.views.enter'),
                       url(r'^teambattle/start/$', 'views.teambattle.views.start'),
                       url(r'^teambattle/incr/$', 'views.teambattle.views.incr_time'),
                       url(r'^teambattle/getreward/$', 'views.teambattle.views.get_reward'),
)
