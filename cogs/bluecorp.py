import logging
import discord
import ast
import re

from discord import app_commands
from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.bluecorp"
logger = logging.getLogger(__cogname__)

class Bluecorp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        self.embed = self.bot.embed
    
    def insert_returns(self, body):
        # insert return stmt if the last expression is a expression statement
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])

        # for if statements, we insert returns into the body and the orelse
        if isinstance(body[-1], ast.If):
            self.insert_returns(body[-1].body)
            self.insert_returns(body[-1].orelse)

        # for with blocks, again we insert returns into the body
        if isinstance(body[-1], ast.With):
            self.insert_returns(body[-1].body)

    def check_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == interaction.client.application.owner.id

    @app_commands.command()
    @app_commands.guilds(discord.Object(138365437791567872))
    @app_commands.check(check_owner)
    async def eval_fn(self, interaction: discord.Interaction, cmd: str):
        """Evaluates input.
        Input is interpreted as newline seperated statements.
        If the last statement is an expression, that is the return value.
        Usable globals:
        - `bot`: the bot instance
        - `discord`: the discord module
        - `commands`: the discord.ext.commands module
        - `ctx`: the invokation context
        - `__import__`: the builtin `__import__` function
        Such that `>eval 1 + 1` gives `2` as the result.
        The following invokation will cause the bot to send the text '9'
        to the channel of invokation and return '3' as the result of evaluating
        >eval ```
        a = 1 + 2
        b = a * 2
        await ctx.send(a + b)
        a
        ```
        """
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")

        # add a layer of indentation
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        self.insert_returns(body)

        env = {
            'client': interaction.client,
            'discord': discord,
            'commands': commands,
            'interaction': interaction,
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        try:
            result = (await eval(f"{fn_name}()", env))
        except Exception as e:
            result = f"{type(e).__name__}: {e}"
        embed = self.embed.create_embed(interaction.user)
        embed.description = f"```{result}```"
        await interaction.response.send_message(embed=embed)
    
    @eval_fn.error
    async def eval_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = self.embed.create_embed(interaction.user)
        if(isinstance(error, app_commands.CheckFailure)):
            embed.description = "No permission to execute this command"
        else:
            embed.description = f"```{error}```"
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction, limit: int=100):
        await interaction.channel.purge(limit=limit)
        await interaction.response.send_message(f"Purged {limit} messages", ephemeral=True)

    @app_commands.command()
    @app_commands.guilds(discord.Object(138365437791567872))
    @app_commands.check(check_owner)
    async def send(self, interaction: discord.Interaction, message: str, replyto: str = None):
        #await interaction.response.defer(ephemeral=False, thinking=False)
        await interaction.response.send_message(f"Sending message:\n```{message}```", ephemeral=True)
        try:
            if(replyto != None):
                reply = await interaction.channel.fetch_message(int(replyto))
                await interaction.channel.send(message, reference=reply)
            else:
                await interaction.channel.send(message)
        except discord.NotFound:
            await interaction.channel.send(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if(message.channel.id != 957048975809183774 and message.channel.id != 1050072272221773856): # nsfw-content
            return
        if(re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content) != [] or message.attachments != []):
            await message.create_thread(name="Comments", auto_archive_duration=10080, reason="Automatic creation of threads")
        else:
            await message.delete()
    
async def setup(bot):
    await bot.add_cog(Bluecorp(bot), guild=bot.get_guild(138365437791567872))