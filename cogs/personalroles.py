import logging
import discord
import typing
import json
import requests
from io import BytesIO
import imghdr

from discord.ext import commands

import sqlalchemy
from sqlalchemy import Column, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.personalroles"
logger = logging.getLogger(__cogname__)

class RoleModel(Base):
    __tablename__ = "personal_role"

    role_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    guild_id = Column(BigInteger)

class PersonalRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db

        RoleModel.metadata.create_all(self.db.engine, RoleModel.metadata.tables.values(), checkfirst=True)

        self.cache = {}
        try:
            with open("./settings/personalroles.json", "r") as fp:
                self.cache = json.load(fp)
        except:
            pass
    
    async def write(self):
        with open("./settings/personalroles.json", "w") as fp:
            json.dump(self.cache, fp, sort_keys=True, indent=4)
    
    def is_guild_owner():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return commands.check(predicate)
    
    @commands.group(pass_context=True)
    async def pr(self, ctx):
        pass

    @pr.error
    async def pr_error(self, ctx, error):
        if(isinstance(error, commands.CheckFailure)):
            return
    
    @is_guild_owner()
    @pr.command()
    async def convert(self, ctx):
        try:
            session = self.db.Session()
            for key, value in self.cache.items():
                member = ctx.guild.get_member(int(key))
                role = ctx.guild.get_role(int(value))
                if(self._role_exists(session, member.id, ctx.guild.id)):
                    continue
                else:
                    new_role = RoleModel(role_id=role.id, user_id=member.id, guild_id=ctx.guild.id)
                    session.add(new_role)
                    session.commit()
                    session = self.db.Session()
        except Exception as e:
            self.logger.error(f"Error occured in pr.add: {e}")
            session.rollback()
        finally:
            session.close()

    @is_guild_owner()
    @pr.command()
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        try:
            session = self.db.Session()
            if(self._role_exists(session, member.id, ctx.guild.id)):
                await ctx.send(f"{member} already has assigned role {role}")
            else:
                new_role = RoleModel(role_id=role.id, user_id=member.id, guild_id=ctx.guild.id)
                session.add(new_role)
                session.commit()
                await ctx.send(f"Succesfully added {member} with role {role}")
        except Exception as e:
            self.logger.error(f"Error occured in pr.add: {e}")
            session.rollback()
        finally:
            session.close()
    
    @add.error
    async def add_error(self, ctx, error):
        if(isinstance(error, commands.RoleNotFound)):
            await ctx.send(str(error))
    
    @is_guild_owner()
    @pr.command()
    async def remove(self, ctx, member: discord.Member, role: discord.Role):
        self.cache.pop(member.id, None)
        await self.write()
        await ctx.send(f"Succesfully removed {member} with role {role}")
    
    @is_guild_owner()
    @pr.command()
    async def list(self, ctx):
        try:
            session = self.db.Session()
            rows = session.query(RoleModel).filter(RoleModel.guild_id == ctx.guild.id).all()
            message = "```"
            for value in rows:
                message += f"{ctx.guild.get_member(value.user_id)} - {ctx.guild.get_role(value.role_id)}\n"
            await ctx.send(f"{message}```")
        except Exception as e:
            self.logger.error(f"Error occured in pr.list: {e}")
        finally:
            session.close()

    @pr.command()
    async def name(self, ctx, *, name: str):
        try:
            session = self.db.Session()
            row = session.query(RoleModel).filter(RoleModel.guild_id == ctx.guild.id, RoleModel.user_id == ctx.author.id).one()
            role = ctx.author.get_role(row.role_id)
            if(role == None):
                return await ctx.send("No personal role found")
            await role.edit(name=name)
        except Exception as e:
            self.logger.error(f"Error occured in pr.name: {e}")
        finally:
            session.close()
    
    @pr.command()
    async def color(self, ctx, color: discord.Colour):
        try:
            session = self.db.Session()
            row = session.query(RoleModel).filter(RoleModel.guild_id == ctx.guild.id, RoleModel.user_id == ctx.author.id).one()
            role = ctx.author.get_role(row.role_id)
            if(role == None):
                return await ctx.send("No personal role found")
            await role.edit(color=color)
        except Exception as e:
            self.logger.error(f"Error occured in pr.name: {e}")
        finally:
            session.close()
    
    @color.error
    async def color_error(self, ctx, error):
        if(isinstance(error, commands.BadColorArgument)):
            await ctx.send("Invalid color format given")
    
    @pr.command()
    async def icon(self, ctx, url=None):
        try:
            session = self.db.Session()
            row = session.query(RoleModel).filter(RoleModel.guild_id == ctx.guild.id, RoleModel.user_id == ctx.author.id).one()
            role = ctx.author.get_role(row.role_id)
            if(role == None):
                return await ctx.send("No personal role found")
            if(len(ctx.message.attachments) == 0 and url == None):
                return await role.edit(display_icon=None)
            bytes = None
            if(url != None):
                response = requests.get(url)
                if(response.status_code != 200):
                    return await ctx.send(f"URL return error code {response.status_code}")
                bytes = BytesIO(response.content)
                if(imghdr.what(bytes) == None):
                    return await ctx.send(f"Invalid image format provided in URL")
            else:             
                attachment = ctx.message.attachments[0]
                bytes = BytesIO(await attachment.read())
            if(bytes.getbuffer().nbytes > 1024*256): # 262144
                return await ctx.send("Attachment is over the 256kb file size limit")
            await role.edit(display_icon=bytes.read())
        except Exception as e:
            self.logger.error(f"Error occured in pr.name: {e}")
        finally:
            session.close()
    
    def _role_exists(self, session, member_id, guild_id):
        try:
            if not session.query(sqlalchemy.exists().where(RoleModel.user_id == member_id, RoleModel.guild_id == guild_id)).scalar():
                return False
            else:
                return True
        except Exception as e:
            self.logger.error(f"Error occured in _role_exists: {e}")
            return False

async def setup(bot):
    await bot.add_cog(PersonalRoles(bot))