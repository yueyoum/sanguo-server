from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^sync/$', 'views.world.views.sync'),
                       url(r'^resume/$', 'views.world.views.resume'),
                       url(r'^sell/$', 'views.world.views.sell'),
                       url(r'^chat/send/$', 'views.chat.views.send'),
                       url(r'^test/$', 'views.cmd.cmd'),

                       url(r'^player/login/$', 'views.account.views.login'),
                       url(r'^player/bind/$', 'views.account.views.bind'),

                       url(r'^pvp/$', 'views.arena.views.arena_battle'),
                       url(r'^arena/panel/$', 'views.arena.views.arena_panel'),

                       url(r'^formation/set/$', 'views.formation.views.set_formation'),
                       url(r'^socket/set/hero/$', 'views.formation.views.up_hero'),
                       url(r'^socket/set/equipment/$', 'views.formation.views.up_equipment'),

                       url(r'^hero/stepup/$', 'views.hero.views.step_up'),
                       url(r'^hero/recruit/$', 'views.hero.views.recruit'),

                       url(r'^hero/get/$', 'views.heropanel.views.open'),
                       url(r'^heropanel/refresh/$', 'views.heropanel.views.refresh'),

                       url(r'^equip/strengthen/$', 'views.item.views.strengthen_equip'),
                       url(r'^equip/stepup/$', 'views.item.views.step_up_equip'),
                       url(r'^equip/embed/$', 'views.item.views.embed'),
                       url(r'^equip/unembed/$', 'views.item.views.unembed'),
                       url(r'^gem/merge/$', 'views.item.views.merge'),
                       url(r'^stuff/use/$', 'views.item.views.stuff_use'),

                       url(r'^pve/$', 'views.stage.views.pve'),
                       url(r'^hang/$', 'views.stage.views.hang_start'),
                       url(r'^hang/cancel/$', 'views.stage.views.hang_cancel'),
                       url(r'^elitepve/$', 'views.stage.views.elite_pve'),
                       url(r'^elite/reset/$', 'views.stage.views.elite_reset'),
                       url(r'^elite/reset/total/$', 'views.stage.views.elite_reset_total'),
                       url(r'^activitypve/$', 'views.stage.views.activity_pve'),

                       url(r'^prize/$', 'views.prize.views.prize_get'),

                       url(r'^plunder/list/$', 'views.plunder.views.plunder_list'),
                       url(r'^plunder/$', 'views.plunder.views.plunder'),
                       url(r'^plunder/getreward/$', 'views.plunder.views.get_reward'),

                       url(r'^prisoner/get/$', 'views.prison.views.prisoner_get'),
                       # FIXME
                       url(r'^prionser/release/$', 'views.prison.views.prisoner_release'),
                       url(r'^prionser/kill/$', 'views.prison.views.prisoner_kill'),

                       url(r'^friend/player-list/$', 'views.friend.views.candidate_list'),
                       url(r'^friend/add/$', 'views.friend.views.add'),
                       url(r'^friend/cancel/$', 'views.friend.views.cancel'),
                       url(r'^friend/accept/$', 'views.friend.views.accept'),
                       url(r'^friend/refuse/$', 'views.friend.views.refuse'),
                       url(r'^friend/terminate/$', 'views.friend.views.terminate'),
                       url(r'^friend/refresh/$', 'views.friend.views.refresh'),

                       url(r'^mail/open/$', 'views.mail.views.open'),
                       url(r'^mail/delete/$', 'views.mail.views.delete'),
                       url(r'^mail/getattachment/$', 'views.mail.views.get_attachment'),

                       url(r'daily/checkin/$', 'views.daily.views.checkin'),


                       url(r'^store/panel/$', 'views.store.views.panel'),
                       url(r'^store/buy/$', 'views.store.views.buy'),

                       url(r'^levy/$', 'views.levy.views.levy'),

                       url(r'^char/create/$', 'views.character.views.create_character'),
                       url(r'^activatecode/use/$', 'views.world.views.activatecode_use'),

                       url(r'^purchase/products/$', 'views.purchase.views.products'),
                       url(r'^purchase/verify/$', 'views.purchase.views.verify'),
)


# API
urlpatterns += patterns('',
                        url(r'^api/character/initialize/$', 'views.api.character.views.character_initialize'),
                        url(r'^api/mail/send/$', 'views.api.mail.views.send_mail'),
                        url(r'^api/timer/hang/$', 'views.api.callback.views.timer_notify'),
                        url(r'^api/checkin/send/$', 'views.api.checkin.views.recv_checkin_data'),

                        url(r'^api/ping/$', 'views.api.ping.views.ping'),
                        url(r'^api/server/feedback/$', 'views.api.server.views.feedback'),
)
