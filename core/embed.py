import logging
import discord
import datetime

from typing import Union

import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.core.embed"
logger = logging.getLogger(__cogname__)

class ColorModel(Base):
    __tablename__ = "embed_color"

    user_id = Column(BigInteger, primary_key=True)
    color = Column(Integer)

class EmbedColor:
    def __init__(self, bot):
        self.logger = logger

        self.bot = bot
        self.db = bot.db

        ColorModel.metadata.create_all(self.db.engine)
        self.embedColors = {}

    def get_color(self, user: Union[discord.Member, discord.User]):
        color = None
        try:
            session = self.db.Session()
            row = session.query(ColorModel).filter(ColorModel.user_id == user.id).first()
            if(row != None):
                color = row.color
        except Exception as e:
            self.logger.error(f"Error occured getting embed color from database: {e}")
        finally:
            session.close()
        return discord.Colour(color) if color != None else discord.Colour(0)
    
    def set_color(self, user: Union[discord.Member, discord.User], color: discord.Colour):
        try:
            session = self.db.Session()
            row = session.query(ColorModel).filter(ColorModel.user_id == user.id).first()
            if not row:
                model = ColorModel(user_id=user.id, color=color.value)
                session.add(model)
            else:
                row.color = color.value
            session.commit()            
        except Exception as e:
            self.logger.error(f"Error occured in setting color to database: {e}")
        finally:
            session.close()
    
    def create_embed(self, user: Union[discord.Member, discord.User, None]):
        embed = discord.Embed()
        if(user != None):
            embed.color = self.get_color(user)
            embed.set_author(name=user, icon_url=user.avatar.url)
        embed.timestamp = datetime.datetime.now()
        return embed