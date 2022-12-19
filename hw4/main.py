import math
import random
import sqlite3
import asyncio
import time

import aioschedule
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from sqlalchemy import create_engine, and_
from sqlalchemy import MetaData, Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///data.db')


class Users(Base):
    __table__ = Table("Users", Base.metadata, autoload_with=engine)


class Mobs(Base):
    __table__ = Table("Mobs", Base.metadata, autoload_with=engine)


class Locations(Base):
    __table__ = Table("Locations", Base.metadata, autoload_with=engine)


class Items(Base):
    __table__ = Table("Items", Base.metadata, autoload_with=engine)


class UserItems(Base):
    __table__ = Table("user_items", Base.metadata, autoload_with=engine)


metadata = MetaData(bind=engine)
user_items = Table('user_items', metadata, autoload=True)
adjacent_locations = Table('adjacent_locations', metadata, autoload=True)
print(adjacent_locations.columns)

Session = sessionmaker(bind=engine)
session = Session()

with open("secret.txt") as file:
    lines = [line.rstrip() for line in file]
    TOKEN = lines[0]
bot = AsyncTeleBot(TOKEN)


@bot.message_handler(commands=['help'])
async def help(message):
    await bot.send_message(chat_id=message.chat.id,
                           text=f'/start name def_hp def_mana')


@bot.message_handler(commands=['start'])
async def start_game(message):
    args = message.text.split()
    # await bot.reply_to(message, str(args))
    user = session.query(Users).get(message.from_user.id)
    if user:
        session.delete(user)
        session.commit()
    user = Users(UserID=message.from_user.id,
                 Nickname=message.from_user.username)
    if len(args) > 1:
        user.Nickname = args[1]
    if len(args) > 2 and args[2].isdigit():
        user.HP = args[2]
    if len(args) > 3 and args[3].isdigit():
        user.Money = args[2]
    session.add(user)
    session.commit()
    await bot.reply_to(message, f"играет {user.Nickname}")


def distance(fr, to):
    a = session.query(Locations).get(fr)
    b = session.query(Locations).get(to)
    return math.sqrt((a.XCoord - b.XCoord) * (a.XCoord - b.XCoord) + (
            a.YCoord - b.YCoord) * (a.YCoord - b.YCoord))


async def respawn(chat_id, user) -> None:
    await bot.send_message(chat_id, text='вы так и не сходили')

    user.XP = 0
    user.CurHP = user.HP
    user.LocationID = 1
    session.merge(user)
    session.commit()

    aioschedule.clear(chat_id)


@bot.message_handler(commands=['move'])
async def move(message):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await bot.reply_to(message, f"введите номер локации")
        return
    to = int(args[1])
    fro = session.query(Users).filter(
        Users.UserID == message.from_user.id).one().LocationID
    q = session.query(
        adjacent_locations).filter(and_(
        adjacent_locations.c.LocationID == fro,
        adjacent_locations.c.AdjacentLocationID == to)).all()
    if not q:
        options = session.query(
            adjacent_locations.c.AdjacentLocationID).filter(
            adjacent_locations.c.LocationID == fro).all()
        await bot.reply_to(message,
                           f"вам доступны только {[x[0] for x in options]}")
        return

    sec = distance(fro, to)
    location = session.query(Locations).get(to)
    await bot.send_message(chat_id=message.chat.id,
                           text=f'идти {sec} сек')
    time.sleep(sec)
    await bot.reply_to(message,
                       f"вы на месте")
    user = session.query(Users).get(message.from_user.id)
    user.LocationID = to
    session.merge(user)
    session.commit()

    if location.LocationType == 'dungeon':
        mob_options = session.query(Mobs).filter(
            Mobs.ReqLevel <= user.Level).all()
        rand = random.randint(0, len(mob_options) - 1)
        mob = mob_options[rand]
        location.MobID = mob.MobID
        location.CurMobHP = mob.HP
        session.merge(location)
        session.commit()

        await bot.send_message(message.chat.id,
                               text='быстрее используйте /fight, /info у вас 60 секунд!')

        aioschedule.every(60).seconds.do(respawn, chat_id=message.chat.id,
                                         user=user).tag(
            message.chat.id)
    if location.LocationType == 'city':
        pass


@bot.message_handler(commands=['fight'])
async def fight(message):
    user = session.query(Users).get(message.from_user.id)
    location = session.query(Locations).get(user.LocationID)

    if location.LocationType != 'dungeon':
        await bot.send_message(message.chat.id,
                               text='нельзя драться не в подземелье')
        return
    mob = session.query(Mobs).get(location.MobID)
    aioschedule.clear(message.chat.id)
    await bot.send_message(message.chat.id, text='Fight!')

    location.CurMobHP -= user.Attack
    session.commit()
    if location.CurMobHP <= 0:
        aioschedule.clear(message.chat.id)
        user.XP += 10
        user.Level = user.XP // 100 + 1
        await bot.send_message(message.chat.id, text='вы победили')
        return

    user.CurHP -= mob.Attack
    session.commit()
    if user.CurHP <= 0:
        await bot.send_message(message.chat.id, text='вы проиграли')
        user.XP = 0
        user.CurHP = user.HP
        user.LocationID = 1
        session.merge(user)
        session.commit()
        aioschedule.clear(message.chat.id)
        return

    aioschedule.every(60).seconds.do(respawn, chat_id=message.chat.id,
                                     user=user).tag(
        message.chat.id)


@bot.message_handler(commands=['info'])
async def info(message):
    user = session.query(Users).get(message.from_user.id)
    location = session.query(Locations).get(user.LocationID)

    if location.LocationType != 'dungeon':
        await bot.send_message(message.chat.id,
                               text='не вижу противника...')
        return
    mob = session.query(Mobs).get(location.MobID)
    aioschedule.clear(message.chat.id)
    await bot.send_message(message.chat.id,
                           text=f'cur mob HP: {location.CurMobHP}\nmod attack:{mob.Attack}\nyour HP: {user.CurHP}')
    user.CurHP -= mob.Attack
    if user.CurHP <= 0:
        user.XP = 0
        user.CurHP = user.HP
        user.LocationID = 1
        session.merge(user)
        session.commit()
        aioschedule.clear(message.chat.id)
        await bot.send_message(message.chat.id, text='вы проиграли')
        return

    aioschedule.every(60).seconds.do(respawn, chat_id=message.chat.id,
                                     user=user).tag(
        message.chat.id)


async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    await asyncio.gather(bot.infinity_polling(), scheduler())


if __name__ == '__main__':
    asyncio.run(main())
