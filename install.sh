#!/bin/bash
# By Aaron

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'

[[ $EUID -ne 0 ]] && echo -e "${red}错误：${plain} 必须使用root用户运行此脚本！\n" && exit 1

echo "欢迎使用 HostlocAutoGetPoints 一键安装程序。"
echo "安装即将开始"
echo "如果您想取消安装，"
echo "请在 5 秒钟内按 Ctrl+C 终止此脚本。"
echo ""
sleep 5

# 判断操作系统并安装相关依赖
if [[ -f /etc/redhat-release ]]; then
    release="centos"
elif cat /etc/issue | grep -Eqi "debian"; then
    release="debian"
elif cat /etc/issue | grep -Eqi "ubuntu"; then
    release="ubuntu"
elif cat /etc/issue | grep -Eqi "arch"; then
    release="arch"
elif cat /etc/issue | grep -Eqi "centos|red hat|redhat|rocky|alma|oracle linux"; then
    release="centos"
elif cat /proc/version | grep -Eqi "debian"; then
    release="debian"
elif cat /proc/version | grep -Eqi "ubuntu"; then
    release="ubuntu"
elif cat /proc/version | grep -Eqi "arch"; then
    release="arch"
elif cat /proc/version | grep -Eqi "centos|red hat|redhat|rocky|alma|oracle linux"; then
    release="centos"
else
    echo -e "${red}此一键脚本不适合你的系统哦～${plain}\n" && exit 1
fi

# 安装依赖
if [[ x"${release}" == x"centos" ]]; then
    yum install epel-release -y
    yum install git python3 python3-pip -y
    echo '0 2 * * * /usr/bin/python3 /root/HostlocAutoGetPoints/HostlocAutoGetPoints.py' >> /var/spool/cron/root
elif [[ x"${release}" == x"ubuntu" ]]; then
    apt-get update -y
    apt install git python3 python3-pip -y
    echo '0 2 * * * /usr/bin/python3 /root/HostlocAutoGetPoints/HostlocAutoGetPoints.py' >> /var/spool/cron/crontabs/root
elif [[ x"${release}" == x"debian" ]]; then
    apt-get update -y
    apt install git python3 python3-pip -y
    echo '0 2 * * * /usr/bin/python3 /root/HostlocAutoGetPoints/HostlocAutoGetPoints.py' >> /var/spool/cron/crontabs/root
elif [[ x"${release}" == x"arch" ]]; then
    pacman -Sy
    yes | pacman -S git python3 python-pip cronie
    export EDITOR=/usr/bin/nano
    echo '0 2 * * * /usr/bin/python3 /root/HostlocAutoGetPoints/HostlocAutoGetPoints.py' >> /var/spool/cron/root
fi

# 安装 Python 依赖
python3 -m pip install --upgrade requests pyaes pyyaml

# 克隆 GitHub 仓库
git clone https://github.com/Xramas/HostlocAutoGetPoints

clear

# 进入仓库并修改配置
cd HostlocAutoGetPoints

# 创建配置文件 config.yaml
cat > config.yaml << EOF
usernames: "your_username"  # 输入多个账号以逗号分隔
passwords: "your_password"  # 输入多个密码以逗号分隔
bot_api: "your_bot_api"  # 你的Telegram Bot API
chat_id: "your_chat_id"  # 你的Telegram Chat ID
max_retries: 3  # 最大重试次数
retry_delay: 5  # 登录重试间隔（秒）
EOF

# 获取用户输入
printf "请输入Hostloc账号，如果您有多个账号，请使用英文逗号隔开："
read -r USERNAME
printf "请输入Hostloc密码，如果您有多个账号，请使用英文逗号隔开："
read -r PASSWORD
printf "请输入BOT_API，在@BotFather处申请："
read -r BOT_API
printf "请输入CHAT_ID，在@userinfobot处获取："
read -r CHAT_ID

# 更新配置文件
sed -i "s/your_username/$USERNAME/" config.yaml
sed -i "s/your_password/$PASSWORD/" config.yaml
sed -i "s/your_bot_api/$BOT_API/" config.yaml
sed -i "s/your_chat_id/$CHAT_ID/" config.yaml

clear
echo "安装已完成"
echo "请执行 /usr/bin/python3 /root/HostlocAutoGetPoints/HostlocAutoGetPoints.py 查看配置是否正确"
