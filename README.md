# server

## 部署

1.  确保系统中已安装Nginx, Mysql, Redis, Mongodb, Erlang, RabbitMQ

2.  安装依赖
    
    ```
    apt-get install python-dev libmysqld-dev
    ```

3.  Python虚拟环境。 在项目根目录中执行：

    ```
    virtualenv env
    source activate_env
    pip install -r requirements.txt
    ```

4.  **如果是直接部署到生产服务器，则略过此步，开发时需要执行这一步**

    ```
    获取最新的proto文件，并编译
    git submodule init
    git submodule update
    ./compile-protobufs.sh
    ```


5.  设置rabbitmq

    ```
    如果有必要，就先设置local_settings.py

    rabbitmqctl add_vhost sanguo
    rabbitmqctl add_vhost sanguo_test
    rabbitmqctl set_permissions -p sanguo guest ".*" ".*" ".*"
    rabbitmqctl set_permissions -p sanguo_test guest ".*" ".*" ".*"
    ```


6.  启动timer服务

    ```
    cd sanguo
    celery worker --app timer -l info
    ```



7.  编辑配置文件，并启动程序

    ```
    cd sanguo
    vim sanguo/local_settings.py
    ./start_*_server.sh

    开发: start_dev_server.sh
    测试: start_test_server.sh
    正式: start_production_server.sh
    ```

8.  测试

    ```
    ./start_test_server 启动测试服务，然后在另一个shell中执行：

    source activate_env
    cd sanguo

    全部测试
    python manage.py test   

    测试某一个app
    python manage.py test apps.player.tests

    测试某一个TestCase
    python manage.py test apps.player.tests:LoginTest

    测试某一个TestCase中的一个测试函数
    python manage.py test apps.player.tests:LoginTest.test_regular_login_with_wrong_password
    ```
    


## Mysql配置

*   [设置utf8编码][1]
*   TODO 增大cache


[1]: http://stackoverflow.com/questions/3513773/change-mysql-default-character-set-to-utf8-in-my-cnf


# 问题

## uWSGI 报错

ubuntu 系统上 uWSGI 在 enable-thread 后可能会报这样的错误

`libgcc_s.so.1 must be installed for pthread_cancel to work`

解决办法:



