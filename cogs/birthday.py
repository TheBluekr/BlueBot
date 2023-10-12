import logging
import discord
import dateparser
import datetime
import pytz
import typing
import asyncio

from discord import app_commands
from discord.ext import commands, tasks

import sqlalchemy
from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.birthday"
logger = logging.getLogger(__cogname__)

class BirthdayModel(Base):
    __tablename__ = "birthdayuser"

    user_id = Column(BigInteger, primary_key=True)
    datetime = Column(DateTime)

class BirthdayServerModel(Base):
    __tablename__ = "birthdayserver"

    guild_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger)

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db
        self.embed = self.bot.embed

        BirthdayModel.metadata.create_all(self.db.engine, BirthdayModel.metadata.tables.values(), checkfirst=True)
        BirthdayServerModel.metadata.create_all(self.db.engine, BirthdayServerModel.metadata.tables.values(), checkfirst=True)

        self.setup_birthday_task.start()
    
    @tasks.loop(count=1)
    async def setup_birthday_task(self):
        today = datetime.datetime.now()
        today = datetime.datetime(today.year, today.month, today.day) # Removing HH:MM:SS since we don't need that
        tomorrow = today + datetime.timedelta(days=1)
        await self.check_birthdays(today)
        await asyncio.sleep((tomorrow-datetime.datetime.now()).total_seconds())
        self.poll_birthday.start()
    
    @tasks.loop(hours=24)
    async def poll_birthday(self):
        today = datetime.datetime.now()
        today = datetime.datetime(today.year, today.month, today.day)
        await self.check_birthdays(today)
    
    async def check_birthdays(self, day: datetime.datetime):
        try:
            session = self.db.Session()
            guild_rows: list[BirthdayServerModel] = session.query(BirthdayServerModel).all()
            guilds = dict()
            for guild_row in guild_rows:
                guild: discord.Guild = self.bot.get_guild(guild_row.guild_id)
                guilds[guild.id] = guild.get_channel(guild_row.channel_id)
            
            users = session.query(BirthdayModel).filter(BirthdayModel.datetime.month == day.month, BirthdayModel.datetime.day == day.day).all()
            for user_id in users:
                user: discord.User = self.bot.get_user(user_id)
                for mutual in user.mutual_guilds:
                    channel: discord.TextChannel = guilds.get(mutual.id, None)
                    if(channel):
                        await channel.send(f"Happy birthday {user}")
        except Exception as e:
            self.logger.error(f"Error occured in check_birthdays: {e}")
            session.rollback()
        finally:
            session.close()
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass

    birthday = app_commands.Group(name="birthday", description="Commands for setting up birthday")

    @app_commands.checks.has_permissions(manage_guild=True)
    @birthday.command()
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel=None):
        try:
            session = self.db.Session()
            row: BirthdayServerModel = session.query(BirthdayServerModel).filter(BirthdayServerModel.guild_id == interaction.guild.id).first()
            if(channel):
                embed: discord.Embed = self.embed.create_embed(interaction.user)

                if(row):
                    row.channel_id = channel.id
                else:
                    row = BirthdayServerModel(guild_id = interaction.guild.id, channel_id = channel.id)
                    session.add(row)
                session.commit()

                embed.description = f"Set channel to send birthday messages to {channel.mention}"
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error occured in birthday.channel: {e}")
        finally:
            session.close()

    @birthday.command()
    async def set(self, interaction: discord.Interaction, date: str):
        try:
            session = self.db.Session()
            embed: discord.Embed = self.embed.create_embed(interaction.user)

            parsedDate = dateparser.parse(date)
            if(not parsedDate):
                embed.description = "Invalid date format provided"
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            parsedDate = datetime.datetime(year=parsedDate.year, month=parsedDate.month, day=parsedDate.day)
            utcDate = parsedDate.astimezone(pytz.utc)

            row: BirthdayModel = session.query(BirthdayModel).filter(BirthdayModel.user_id == interaction.user.id).first()
            if(row):
                row.datetime = utcDate
            else:
                row = BirthdayModel(user_id=interaction.user.id, datetime=utcDate)
                session.add(row)
            session.commit()

            timestamp = int((utcDate - pytz.utc.localize(datetime.datetime(1970, 1, 1))).total_seconds())
            embed.description = f"Birthday set on <t:{timestamp}>"
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in birthday.set: {e}")
        finally:
            session.close()
    
    @birthday.command()
    async def list(self, interaction: discord.Interaction):
        try:
            session = self.db.Session()
            pass
        except Exception as e:
            self.logger.error(f"Error occured in birthday.list: {e}")
        finally:
            session.close()
    
async def setup(bot):
    await bot.add_cog(Birthday(bot))