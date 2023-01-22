import logging
import discord
import json
import os

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

        ColorModel.metadata.create_all(self.db.engine, ColorModel.metadata.tables.values(), checkfirst=True)

        self.embedColors = {}

        self.embed_colors()
    
    def embed_colors(self):
        if not os.path.isfile(f"{os.getcwd()}/settings/music.embed.json"):
            return
        try:
            with open(f"{os.getcwd()}/settings/music.embed.json", "r") as file:
                embedColors = json.load(file)
            for key in embedColors.keys():
                self.embedColors[int(key)] = int(embedColors[key], 0)
                session = self.db.Session()
                rows = session.query(ColorModel).all()
                for row in rows:
                    self.embedColors[row.user_id] = row.color
            self.logger.info(f"Loaded {len(self.embedColors)} embed colors for users")
        except json.decoder.JSONDecodeError:
            pass
    
    def get_color(self, user: Union[discord.Member, discord.User]):
        color = self.embedColors.get(user.id, None)
        if(color == None):
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
        self.embedColors[user.id] = color.value
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
    
    def create_embed(self, user: Union[discord.Member, discord.User]):
        embed = discord.Embed(color=self.get_color(user))
        embed.set_author(name=user, icon_url=user.avatar.url)
        return embed