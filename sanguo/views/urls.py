from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('',
                       url(r'^sync/$', 'views.world.views.sync'),
                       url(r'^resume/$', 'views.world.views.resume'),
                       url(r'^sell/$', 'views.world.views.sell'),
                       url(r'^chat/send/$', 'views.chat.views.send'),
                       url(r'^test/$', 'views.cmd.cmd'),

                       url(r'^player/login/$', 'views.account.views.login'),

                       url(r'^pvp/$', 'views.arena.views.arena_battle'),
                       url(r'^arena/panel/$', 'views.arena.views.arena_panel'),

                       url(r'^formation/set/$', 'views.formation.views.set_formation'),
                       url(r'^socket/set/$', 'views.formation.views.set_socket'),

                       url(r'^hero/stepup/$', 'views.hero.views.step_up'),

                       url(r'^hero/get/$', 'views.heropanel.views.open'),
                       url(r'^heropanel/refresh/$', 'views.heropanel.views.refresh'),
                       url(r'^heropanel/start/$', 'views.heropanel.views.start'),

                       url(r'^equip/strengthen/$', 'views.item.views.strengthen_equip'),
                       url(r'^equip/stepup/$', 'views.item.views.step_up_equip'),
                       url(r'^equip/embed/$', 'views.item.views.embed'),
                       url(r'^equip/unembed/$', 'views.item.views.unembed'),
                       url(r'^equip/specialbuy/$', 'views.item.views.special_buy'),
                       url(r'^gem/merge/$', 'views.item.views.merge'),

                       url(r'^pve/$', 'views.stage.views.pve'),
                       url(r'^hang/$', 'views.stage.views.hang_start'),
                       url(r'^hang/cancel/$', 'views.stage.views.hang_cancel'),
                       url(r'^elitepve/$', 'views.stage.views.elite_pve'),

                       url(r'^prize/$', 'views.prize.views.prize_get'),

                       url(r'^plunder/list/$', 'views.plunder.views.plunder_list'),
                       url(r'^plunder/$', 'views.plunder.views.plunder'),
                       url(r'^plunder/getreward/$', 'views.plunder.views.get_reward'),

                       url(r'^prisoner/get/$', 'views.prison.views.prisoner_get'),
                       # FIXME
                       url(r'^prionser/release/$', 'views.prison.views.prisoner_release'),
                       url(r'^prionser/kill/$', 'views.prison.views.prisoner_kill'),

                       url(r'^friend/player-list/$', 'views.friend.views.player_list'),
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

                       url(r'^teambattle/start/$', 'views.teambattle.views.start'),

                       url(r'^store/panel/$', 'views.store.views.panel'),
                       url(r'^store/buy/$', 'views.store.views.buy'),

                       url(r'^levy/$', 'views.levy.views.levy'),
)


# API
urlpatterns += patterns('',
                        url(r'^api/character/initialize/$', 'views.api.character.views.character_initialize'),
                        url(r'^api/mail/send/$', 'views.api.mail.views.send_mail'),
                        url(r'^api/purchase/done/$', 'views.api.purchase.views.purchase_done'),
)


if settings.IS_GUIDE_SERVER:
    urlpatterns += patterns('',
                            url(r'^char/create/$', 'views.character.views.create_character'),
    )

