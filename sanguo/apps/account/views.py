# -*- coding: utf-8 -*-
import logging

from apps.server.models import Server
from apps.character.models import Character
from apps.account.models import Account
from core.exception import SanguoException, BadMessage, InvalidOperate
from core.signals import login_signal, register_signal
from core.world import server_list
from protomsg import RegisterResponse, StartGameResponse
from utils import crypto, pack_msg
from utils.decorate import message_response

# logger = logging.getLogger('sanguo')


def create_new_user(email='', password='', device_token=''):
    """

    @param email: registered user's email
    @type email: str
    @param password: registered user's password
    @type password: str
    @param device_token: anonymous user's device token
    @type device_token: str
    @return: @raise ValueError:
    @rtype: User
    """
    passwd = password

    if not email and not passwd and not device_token:
        raise ValueError("Can not create user with all Empty values")

    user = Account.objects.create(
        email=email,
        passwd=passwd,
        device_token=device_token,
    )
    return user


@message_response("RegisterResponse")
def register(request):
    req = request._proto

    if not req.email or not req.password or not req.device_token:
        raise BadMessage("Register: With Empty Arguments")

    if Account.objects.filter(email=req.email).exists():
        raise SanguoException(100, "Register: With an Existed Email {0}".format(req.email))

    try:
        user = Account.objects.get(device_token=req.device_token)
    except Account.DoesNotExist:
        # logger.debug("Register: Create New User")
        user = create_new_user(
            email=req.email,
            password=req.password,
            device_token=''
        )
    else:
        # 这次注册相当于将device_token和帐号绑定。
        # 删除device_token的记录，等下次再用device_token登录的时候，会新建用户
        # logger.debug("Register: Replace device token with email account")
        user.email = req.email
        user.passwd = req.password
        user.device_token = ''
        user.save()

    # register_signal.send(
    #     sender=None,
    #     account_id=user.id
    # )

    response = RegisterResponse()
    response.ret = 0
    response.email = req.email
    response.password = req.password

    top, all_servers = server_list()
    response.top.MergeFrom(top)
    for server in all_servers:
        s = response.servers.add()
        s.MergeFrom(server)

    return pack_msg(response)


@message_response("StartGameResponse")
def login(request):
    req = request._proto
    if req.server_id not in Server.all():
        raise InvalidOperate("Login: With an NON Existed server {0}".format(req.server_id))

    need_create_new_char = None
    if req.anonymous.device_token:
        try:
            user = Account.objects.get(device_token=req.anonymous.device_token)
        except Account.DoesNotExist:
            # logger.debug("Login: With Anonymous. New User, Create New User")
            user = create_new_user(device_token=req.anonymous.device_token)
            need_create_new_char = True
    else:
        if not req.regular.email or not req.regular.password:
            raise BadMessage("Login. Bad Message. No Email or Password")
        try:
            user = Account.objects.get(email=req.regular.email)
            if user.passwd != req.regular.password:
                raise SanguoException(120, "Login: Wrong Password")
        except Account.DoesNotExist:
            raise SanguoException(121, "Login: None Exist Email {0}".format(req.regular.email.encode('utf-8')))

    user.last_server_id = req.server_id
    user.save()
    if not user.active:
        raise SanguoException(122, "Login: User {0} NOT Active".format(user.id))

    request._account_id = user.id
    request._server_id = req.server_id

    char_id = None
    if need_create_new_char is None:
        try:
            char = Character.objects.get(
                account_id=user.id,
                server_id=req.server_id
            )
            need_create_new_char = False
            char_id = char.id
        except Character.DoesNotExist:
            need_create_new_char = True

    request._char_id = char_id

    login_signal.send(
        sender=None,
        account_id=request._account_id,
        server_id=request._server_id,
        char_id=char_id
    )

    if char_id:
        session_str = '{0}:{1}:{2}'.format(
            request._account_id,
            request._server_id,
            request._char_id
        )
    else:
        session_str = '{0}:{1}'.format(request._account_id, request._server_id)

    session = crypto.encrypt(session_str)

    response = StartGameResponse()
    response.ret = 0
    if req.anonymous.device_token:
        response.anonymous.MergeFrom(req.anonymous)
    else:
        response.regular.MergeFrom(req.regular)
    response.need_create_new_char = need_create_new_char

    return pack_msg(response, session)