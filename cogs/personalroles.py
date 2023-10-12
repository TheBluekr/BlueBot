import logging
import discord
import typing
import requests
from io import BytesIO
import imghdr
from typing import Union, Optional

from discord import app_commands
from discord.ext import commands

import sqlalchemy
from sqlalchemy import Column, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.personalroles"
logger = logging.getLogger(__cogname__)

class RoleModel(Base):
    __tablename__ = "personalroles"

    role_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    guild_id = Column(BigInteger)

class PersonalRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db
        self.embed = self.bot.embed

        RoleModel.metadata.create_all(self.db.engine, RoleModel.metadata.tables.values(), checkfirst=True)
    
    def is_guild_owner():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return commands.check(predicate)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass

    personalrole = app_commands.Group(name="personalrole", description="Set properties of your personal role")

    @personalrole.command()
    async def name(self, interaction: discord.Interaction, name: str):
        try:
            session = self.db.Session()
            row = session.query(RoleModel).filter(RoleModel.guild_id == interaction.guild.id, RoleModel.user_id == interaction.user.id).one()
            role = interaction.user.get_role(row.role_id)
            embed = self.embed.create_embed(interaction.user)
            if(role == None):
                embed.description = "No personal role found"
                return await interaction.response.send_message(embed=embed)
            await role.edit(name=name)
            embed.description = f"Set {role} title to: {name}"
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in personalrole.name: {e}")
        finally:
            session.close()
    
    @personalrole.command()
    async def color(self, interaction: discord.Interaction, color: str):
        try:
            session = self.db.Session()
            row = session.query(RoleModel).filter(RoleModel.guild_id == interaction.guild.id, RoleModel.user_id == interaction.user.id).one()
            role = interaction.user.get_role(row.role_id)
            embed = self.embed.create_embed(interaction.user)
            if(role == None):
                embed.description = "No personal role found"
                return await interaction.response.send_message(embed=embed)
            try:
                colorcls = discord.Color.from_str(color)
                await role.edit(color=colorcls)
                embed.description = f"Set {role} color to: #{colorcls.value:0>6X}"
            except:
                embed.description = f"Invalid color format provided"
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in pr.name: {e}")
        finally:
            session.close()
    
    @personalrole.command()
    async def icon(self, interaction: discord.Interaction, url: str = None, attachment: discord.Attachment = None):
        try:
            session = self.db.Session()
            row = session.query(RoleModel).filter(RoleModel.guild_id == interaction.guild.id, RoleModel.user_id == interaction.user.id).one()
            role = interaction.user.get_role(row.role_id)
            embed = self.embed.create_embed(interaction.user)
            if(role == None):
                embed.description = "No personal role found"
                return await interaction.response.send_message(embed=embed)
            if(url == None and attachment == None):
                return await role.edit(display_icon=None)
            image_bytes = None
            if(url != None):
                response = requests.get(url)
                if(response.status_code != 200):
                    embed.description = f"URL return error code {response.status_code}"
                    return await interaction.response.send_message(embed=embed)
                image_bytes = BytesIO(response.content)
                if(imghdr.what(image_bytes) == None):
                    embed.description = f"Invalid image format provided in URL"
                    return await interaction.response.send_message(embed=embed)
            else:             
                image_bytes = BytesIO(await attachment.read())
            if(image_bytes.getbuffer().nbytes > 1024*256): # 262144
                embed.description = "Attachment is over the 256kb file size limit"
                return await interaction.response.send_message(embed=embed)
            await role.edit(display_icon=image_bytes.read())
            embed.description = f"Set {role} icon"
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in pr.name: {e}")
        finally:
            session.close()

    @commands.group(pass_context=True)
    async def pr(self, ctx):
        pass

    @pr.error
    async def pr_error(self, ctx, error):
        if(isinstance(error, commands.CheckFailure)):
            return
    
    @is_guild_owner()
    @pr.command()
    async def create(self, ctx, member: discord.Member, name: str):
        try:
            session = self.db.Session()
            if(self._role_exists(session, member.id, ctx.guild.id)):
                await ctx.send(f"{member} already has assigned role {role}")
            else:
                role = await ctx.guild.create_role(name=name)
                await member.add_roles(role)
                roles = self._get_guild_roles(session, ctx.guild.id)
                lowest = ctx.guild.get_role(list(roles.values())[0])
                for curr in list(roles.values()):
                    temprole = ctx.guild.get_role(curr)
                    if(temprole < lowest):
                        lowest = temprole
                await role.edit(position=lowest.position)

                new_role = RoleModel(role_id=role.id, user_id=member.id, guild_id=ctx.guild.id)
                session.add(new_role)
                session.commit()
                embed = self.embed.create_embed(ctx.author)
                embed.description = f"Succesfully added {member} with role {role}"
                await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in pr.add: {e}")
            session.rollback()
        finally:
            session.close()
    
    @is_guild_owner()
    @pr.command()
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        try:
            await member.add_roles(role)
            session = self.db.Session()
            if(self._role_exists(session, member.id, ctx.guild.id)):
                await ctx.send(f"{member} already has assigned role {role}")
            else:
                new_role = RoleModel(role_id=role.id, user_id=member.id, guild_id=ctx.guild.id)
                session.add(new_role)
                session.commit()
                embed = self.embed.create_embed(ctx.author)
                embed.description = f"Succesfully added {member} with role {role}"
                await ctx.send(embed=embed)
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
    async def remove(self, ctx, member: Union[discord.Member, discord.User], role: discord.Role):
        try:
            session = self.db.Session()
            if(not self._role_exists(session, member.id, ctx.guild.id)):
                await ctx.send(f"{member} doesn't have an assigned role {role}")
            else:
                row = session.query(RoleModel).filter(RoleModel.guild_id == ctx.guild.id, RoleModel.user_id == member.id, RoleModel.role_id == role.id).scalar()
                session.delete(row)
                session.commit()
                embed = self.embed.create_embed(ctx.author)
                embed.description = f"Succesfully removed {member} with role {role}"
                await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in pr.remove: {e}")
            session.rollback()
        finally:
            session.close()
    
    @is_guild_owner()
    @pr.command()
    async def list(self, ctx):
        try:
            session = self.db.Session()
            embed = self.embed.create_embed(ctx.author)
            embed.description = "List of personal roles:\n```"
            rows = session.query(RoleModel).all()
            for row in rows:
                member = ctx.guild.get_member(row.user_id)
                if(member != None):
                    embed.description += f"{member} - {ctx.guild.get_role(row.role_id)}\n"
                else:
                    member = await self.bot.fetch_user(row.user_id)
                    embed.description += f"{member} - {ctx.guild.get_role(row.role_id)} - Not in guild\n"
            embed.description += "```"
            await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Error occured in pr.list: {e}")
        finally:
            session.close()
    
    def _role_exists(self, session, member_id, guild_id):
        try:
            if not session.query(sqlalchemy.exists(RoleModel).where(RoleModel.user_id == member_id, RoleModel.guild_id == guild_id)).scalar():
                return False
            else:
                return True
        except Exception as e:
            self.logger.error(f"Error occured in _role_exists: {e}")
            return False
    
    def _get_guild_roles(self, session, guild_id):
        try:
            rows = session.query(RoleModel).filter(RoleModel.guild_id == guild_id).all()
            roles = {}
            for row in rows:
                roles[row.user_id] = row.role_id
            return roles
        except Exception as e:
            self.logger.error(f"Error occured in _get_guild_roles: {e}")
            return []

async def setup(bot):
    await bot.add_cog(PersonalRoles(bot))