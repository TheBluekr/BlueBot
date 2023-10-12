import logging
import discord
import dateparser
import datetime
import pytz
import typing

from discord import app_commands
from discord.ext import commands, tasks

import sqlalchemy
from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.reminder"
logger = logging.getLogger(__cogname__)

class ReminderModel(Base):
    __tablename__ = "reminder"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    guild_id = Column(BigInteger)
    datetime = Column(DateTime)
    message = Column(String(128))

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db
        self.embed = self.bot.embed

        ReminderModel.metadata.create_all(self.db.engine, ReminderModel.metadata.tables.values(), checkfirst=True)

        self.poll_reminders.start()
    
    @tasks.loop(seconds=1)
    async def poll_reminders(self):
        try:
            session = self.db.Session()
            currentUtc = datetime.datetime.utcnow()
            rows = session.query(ReminderModel).filter(ReminderModel.datetime < currentUtc).all()
            for row in rows:
                member: discord.User = self.bot.get_user(row.user_id)
                channel: discord.TextChannel = self.bot.get_channel(row.channel_id)
                embed: discord.Embed = self.embed.create_embed(member)
                embed.description = f"Reminding message: ```{row.message}```"
                await channel.send(f"{member.mention}", embed=embed)
                session.delete(row)
            session.commit()
        except Exception as e:
            self.logger.error(f"Error occured in poll_reminders: {e}")
            session.rollback()
        finally:
            session.close()
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass

    reminder = app_commands.Group(name="reminder", description="Commands for reminders")

    @reminder.command()
    async def create(self, interaction: discord.Interaction, message: str, date: str):
        try:
            session = self.db.Session()
            embed: discord.Embed = self.embed.create_embed(interaction.user)

            parsedDate = dateparser.parse(date)
            if(not parsedDate):
                embed.description = "Invalid date format provided"
                return await interaction.response.send_message(embed=embed)
            utcDate = parsedDate.astimezone(pytz.utc)
            timestamp = int((utcDate - pytz.utc.localize(datetime.datetime(1970, 1, 1))).total_seconds())
            newReminder = ReminderModel(user_id=interaction.user.id, channel_id=interaction.channel.id, guild_id=interaction.guild.id, datetime=utcDate, message=message)
            session.add(newReminder)
            session.commit()
            embed.description = f"Reminder set on <t:{timestamp}> ```{message}```"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error occured in reminder.create: {e}")
        finally:
            session.close()
    
    @reminder.command()
    async def delete(self, interaction: discord.Interaction, date: str):
        try:
            session = self.db.Session()
            rowId = int(date)
            reminder = ReminderModel(id=rowId)
            session.delete(reminder)
            session.commit()
            embed = self.embed.create_embed(interaction.user)
            embed.description = "Succesfully removed reminder"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error occured in reminder.delete: {e}")
        finally:
            session.close()

    @delete.autocomplete("date")
    async def delete_date_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        choices = list()

        try:
            session = self.db.Session()
            parsedDate = dateparser.parse(current)
            if(not parsedDate):
                parsedDate = datetime.datetime.now()
            utcDate = parsedDate.astimezone(pytz.utc)
            rows = session.query(ReminderModel).filter(ReminderModel.user_id == interaction.user.id, ReminderModel.datetime >= utcDate).all()
            for row in rows:
                timestamp = int((utcDate - pytz.utc.localize(datetime.datetime(1970, 1, 1))).total_seconds())
                choices.append(app_commands.Choice(name=f"<t:{timestamp}>", value=row.id))
        except Exception as e:
            self.logger.error(f"Error occured in reminder.delete.date: {e}")
        finally:
            session.close()

        return choices
    
    @reminder.command()
    async def list(self, interaction: discord.Interaction):
        try:
            session = self.db.Session()
            pass
        except Exception as e:
            self.logger.error(f"Error occured in reminder.list: {e}")
        finally:
            session.close()
    
async def setup(bot):
    await bot.add_cog(Reminder(bot))