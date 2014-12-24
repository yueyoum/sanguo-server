# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('',
                       url(r'^sync/$', 'views.world.views.sync'),
                       url(r'^resume/$', 'views.world.views.resume'),
                       url(r'^sell/$', 'views.world.views.sell'),
                       url(r'^chat/send/$', 'views.chat.views.send'),

                       url(r'^player/login/$', 'views.account.views.login'),
                       url(r'^player/bind/$', 'views.account.views.bind'),

                       url(r'^pvp/$', 'views.arena.views.arena_battle'),
                       url(r'^arena/panel/$', 'views.arena.views.arena_panel'),

                       url(r'^formation/set/$', 'views.formation.views.set_formation'),
                       url(r'^socket/set/$', 'views.formation.views.set_socket'),

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

                       url(r'^hang/start/$', 'views.affairs.views.hang_start'),
                       url(r'^hang/sync/$', 'views.affairs.views.hang_sync'),
                       url(r'^hang/getreward/$', 'views.affairs.views.hang_get_reward'),

                       url(r'^elitepve/$', 'views.stage.views.elite_pve'),
                       url(r'^elite/reset/$', 'views.stage.views.elite_reset'),
                       url(r'^elite/reset/total/$', 'views.stage.views.elite_reset_total'),
                       url(r'^activitypve/$', 'views.stage.views.activity_pve'),

                       url(r'^prize/$', 'views.prize.views.prize_get'),

                       url(r'^plunder/refresh/$', 'views.plunder.views.plunder_refresh'),
                       url(r'^plunder/$', 'views.plunder.views.plunder'),
                       url(r'^plunder/leaderboard/$', 'views.plunder.views.get_leaderboard'),

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
                       url(r'^friend/giveplundertimes/', 'views.friend.views.give_plunder_times'),
                       url(r'^friend/getplundertimes/', 'views.friend.views.get_plunder_times'),

                       url(r'^mail/open/$', 'views.mail.views.open'),
                       url(r'^mail/delete/$', 'views.mail.views.delete'),
                       url(r'^mail/getattachment/$', 'views.mail.views.get_attachment'),

                       url(r'^daily/checkin/$', 'views.daily.views.checkin'),


                       url(r'^store/panel/$', 'views.store.views.panel'),
                       url(r'^store/buy/$', 'views.store.views.buy'),

                       url(r'^levy/$', 'views.levy.views.levy'),

                       url(r'^char/create/$', 'views.character.views.create_character'),
                       url(r'^activatecode/use/$', 'views.world.views.activatecode_use'),

                       url(r'^purchase/verify/$', 'views.purchase.views.purchase_ios_verify'),

                       #91
                       url(r'^purchase91/orderid/$', 'views.purchase.views.get_91_order_id'),
                       url(r'^purchase/confirm/$', 'views.purchase.views.purchase_confirm'),


                       url(r'^vip/getreward/$', 'views.vip.views.vip_get_reward'),

                       url(r'^activity/getreward/$', 'views.activity.views.get_reward'),

                       # 坐骑
                       url(r'^horse/strength/$', 'views.horse.views.strength'),
                       url(r'^horse/strength/confirm/$', 'views.horse.views.strength_confirm'),
                       url(r'^horse/evolution/$', 'views.horse.views.evolution'),

                       # 工会
                       url(r'^union/create/$', 'views.union.views.create'),
                       url(r'^union/modify/$', 'views.union.views.modify'),
                       url(r'^union/apply/$', 'views.union.views.apply_join'),
                       url(r'^union/agree/$', 'views.union.views.agree_join'),
                       url(r'^union/refuse/$', 'views.union.views.refuse_join'),
                       url(r'^union/list/$', 'views.union.views.get_list'),
                       url(r'^union/quit/$', 'views.union.views.quit'),
                       url(r'^union/manage/$', 'views.union.views.manage'),
                       url(r'^union/buy/$', 'views.union.views.store_buy'),
                       url(r'^union/checkin/$', 'views.union.views.checkin'),
                       url(r'^union/battle/board/$', 'views.union.views.get_battle_board'),
                       url(r'^union/battle/start/$', 'views.union.views.battle_start'),
                       url(r'^union/battle/record/$', 'views.union.views.get_records'),
                       url(r'^union/boss/$', 'views.union.views.get_union_boss'),
                       url(r'^union/boss/log/$', 'views.union.views.get_union_boss_log'),
                       url(r'^union/boss/start/$', 'views.union.views.union_boss_start'),
                       url(r'^union/boss/battle/$', 'views.union.views.union_boss_battle'),

)

# testmode
if settings.ENABLE_TEST_MODE:
    urlpatterns += patterns('',
                            url(r'^test/$', 'views.cmd.cmd'),
                            )

# API
urlpatterns += patterns('',
                        url(r'^api/character/initialize/$', 'views.api.character.views.character_initialize'),
                        url(r'^api/character/information/$', 'views.api.character.views.character_information'),
                        url(r'^api/mail/send/$', 'views.api.mail.views.send_mail'),
                        url(r'^api/checkin/send/$', 'views.api.checkin.views.recv_checkin_data'),

                        url(r'^api/ping/$', 'views.api.ping.views.ping'),
                        url(r'^api/server/feedback/$', 'views.api.server.views.feedback'),

                        url(r'^api/purchase/91/done/$', 'views.api.purchase.views.purchase91_done'),
                        url(r'^api/purchase/aiyingyong/done/$', 'views.api.purchase.views.purchase_aiyingyong_done'),

                        # update the whole server version!
                        url(r'^api/server/version/$', 'views.api.server.views.version_change'),
)
