import telebot
from telebot import types

TOKEN = '5746057060:AAGefVFRp4PXo2EQ6sRbLyS4RPHRm-K8y80'
banned = dict()
tasks = dict()
bot = telebot.TeleBot(TOKEN)

help_text = """ Функционал бота (бот желательно сделать админом):
/help вывести этот текст
/mytasks посмотерть свои задачи
/todo task добавть задание в todo-list
/done n убрать n-ое задание из todo-listа
/promote + reply на сообщение того, кого хотим сделать администратором чата
/ban + reply на сообщение того, кого баним
/unban @member разбанить человека
/stats статистика по участникам/админам
/leave выгнать бота из чата
"""

@bot.message_handler(content_types=["new_chat_members"])
def foo(message):
    bot.reply_to(message, "А ты что здесь делаешь?")

@bot.message_handler(commands=['help'])
def start(message):
  global help_text
  bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['leave'], )
def leave_message(message):
  bot.send_message(message.chat.id, "💀💀💀")
  bot.leave_chat(message.chat.id)

@bot.message_handler(commands=['stats'])
def stats(message):
  admins_cnt=len(bot.get_chat_administrators(message.chat.id))
  members_cnt=bot.get_chat_member_count(message.chat.id)
  bot.send_message(message.chat.id,'{} members\n{} admins'.format(members_cnt,admins_cnt))

@bot.message_handler(commands=['ban'])
def ban(message):
  if message.reply_to_message:
    if bot.ban_chat_member(message.chat.id,message.reply_to_message.from_user.id):
      bot.send_message(message.chat.id, 'в бан, @'+ message.reply_to_message.from_user.username)
      banned['@'+ message.reply_to_message.from_user.username]= message.reply_to_message.from_user.id
    else:
      bot.send_message(message.chat.id, 'что-то не так. нужна /help?'+ message.reply_to_message.from_user.username)
  else:
    bot.send_message(message.chat.id, 'ответь на сообщение того, кого банишь...')

@bot.message_handler(commands=['promote'])
def promote(message):
  if message.reply_to_message:
    if(bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, True)):
      bot.send_message(message.chat.id, 'ты теперь админ @'+ message.reply_to_message.from_user.username)
    else:
      bot.send_message(message.chat.id, 'что-то не так. нужна /help?'+ message.reply_to_message.from_user.username)
  else:
    bot.send_message(message.chat.id, 'ответь на сообщение того, кого promotишь...')

@bot.message_handler(commands=['unban'])
def unban(message):
  user = telebot.util.extract_arguments(message.text)
  if user and user in banned:
    bot.send_message(message.chat.id, user + ' теперь не в бане')
    bot.unban_chat_member(message.chat.id,banned[user])
  else:
    bot.send_message(message.chat.id, 'кого🤨')

def add_task(user,task):
  if user not in tasks:
    tasks[user] = []
  tasks[user]+=[task]

def done_task(user,task_number):
  del tasks[user][task_number]

def get_tasks(username):
  if username not in tasks or len(tasks[username])==0:
    return False  
  text = 'TODO:\n'
  for i, task in enumerate(tasks[username]):
    text+='{}) {}\n'.format(i+1, task)
  return text

def check_if_exists(user,task_number):
  return user in tasks and len(tasks[user])>=task_number

@bot.message_handler(commands=['todo'])
def todo(message):
  new_task = telebot.util.extract_arguments(message.text).replace('\n',' ')
  if new_task:
    add_task(message.from_user.username, new_task)
    bot.send_message(message.chat.id, 'добавил🤓, кол-во задач: {}'.format(len(tasks[message.from_user.username])))
  else:
    bot.send_message(message.chat.id, 'todo WHAT? пожалуйста уточни')

@bot.message_handler(commands=['mytasks'])
def mytasks(message):
  text = get_tasks(message.from_user.username)
  if text:
    bot.send_message(message.chat.id, text)
  else:
    bot.send_message(message.chat.id, 'у @{} нет дел'.format(message.from_user.username))

@bot.message_handler(commands=['done'])
def done(message):
  try:
    task_number = int(telebot.util.extract_arguments(message.text))
    if check_if_exists(message.from_user.username, task_number):
      done_task(message.from_user.username, task_number-1)
      bot.send_message(message.chat.id, 'молодец!, кол-во задач: {}'.format(len(tasks[message.from_user.username])))
    else:
      bot.send_message(message.chat.id, 'у тебя нет такой задачи')
  except:
    bot.send_message(message.chat.id, 'done WHAT? нужен номер задачи')
    return


bot.polling(none_stop=True, interval=0)
