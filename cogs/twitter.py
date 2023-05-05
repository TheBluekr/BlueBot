import logging
import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Union, Optional
import tweepy
import os
import re
import json

import sqlalchemy
from sqlalchemy import Column, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.twitter"
logger = logging.getLogger(__cogname__)

class TwitterModel(Base):
    __tablename__ = "twitter_poll"

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger)
    discord_id = Column(BigInteger)

    twitter_id = Column(BigInteger)
    tweet_id = Column(BigInteger)

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db
        self.embed = self.bot.embed

        self.auth = tweepy.OAuthHandler(os.getenv("TWITTER_API"), os.getenv("TWITTER_API_SECRET"))
        self.auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_SECRET"))

        self.api = tweepy.API(auth=self.auth, wait_on_rate_limit=True)

        TwitterModel.metadata.create_all(self.db.engine, TwitterModel.metadata.tables.values(), checkfirst=True)

        self.poll_twitter.start()

    @tasks.loop(minutes=1)
    async def poll_twitter(self):
        try:
            session = self.db.Session()
            rows = session.query(TwitterModel).all()
            # Maybe should cache in case same user is multiple channels
            cache = {}
            for row in rows:
                cache_data = cache.get(row.discord_id, None)
                if(cache_data == None):
                    twitter_user = self.api.get_user(user_id=row.twitter_id)
                    timeline = self.api.user_timeline(count=50, user_id=twitter_user.id, trim_user=True, exclude_replies=True, include_rts=False, tweet_mode="extended", since_id=row.tweet_id)
                    # Twitter likes to return from new to old, but we want to post from old to new
                    timeline.reverse()
                    cache[row.discord_id] = [twitter_user, timeline]

                    # No new tweets, don't do anything
                    if(len(timeline) == 0):
                        continue
                    
                    member = self.bot.get_user(row.discord_id)
                    channel = self.bot.get_channel(row.channel_id)

                    for tweet in timeline:
                        embed = self.create_tweet_embed(member, twitter_user, tweet)
                        await channel.send(embed=embed)

                        row.tweet_id = tweet.id
                else:
                    twitter_user = cache_data[0]
                    timeline = cache_data[1]
                    if(len(timeline) == 0):
                        continue

                    member = self.bot.get_user(row.discord_id)
                    channel = self.bot.get_channel(row.channel_id)

                    for tweet in timeline:
                        embed = self.create_tweet_embed(member, twitter_user, tweet)
                        await channel.send(embed=embed)
            session.commit()
        except Exception as e:
            self.logger.error(f"Error occured in poll_twitter: {e}")
            session.rollback()
        finally:
            session.close()
    
    @commands.command()
    @commands.has_permissions(manage_guild=True) 
    async def twitter(self, ctx: commands.Context, screen_name: str, member: Union[discord.Member, discord.User, None]) -> None:
        try:
            twitter_user = self.api.get_user(screen_name=screen_name)
            timeline = self.api.user_timeline(count=50, user_id=twitter_user.id, trim_user=True, exclude_replies=True, include_rts=False, tweet_mode="extended")
            tweet = timeline[0]

            session = self.db.Session()
            rows = session.query(TwitterModel).filter(TwitterModel.twitter_id == twitter_user.id, TwitterModel.channel_id == ctx.channel.id).all()
            session.close()

            session = self.db.Session()
            if(len(rows) == 0):
                if(member != None):
                    poll_transaction = TwitterModel(channel_id=ctx.channel.id, discord_id=member.id, twitter_id=twitter_user.id, tweet_id=tweet.id)
                else:
                    poll_transaction = TwitterModel(channel_id=ctx.channel.id, discord_id=None, twitter_id=twitter_user.id, tweet_id=tweet.id)
                session.add(poll_transaction)
                session.commit()

                embed = self.create_tweet_embed(member, twitter_user, tweet)
                await ctx.send(embed=embed)
            else:
                await ctx.send("Failed to add, account already exists in database")

        except tweepy.errors.NotFound:
            await ctx.send(f"Failed to find user for handle: \@{screen_name}")
        except Exception as e:
            self.logger.error(f"Error occured in twitter: {e}")
            session.rollback()
        finally:
            session.close()
    
    @commands.command()
    @commands.has_permissions(manage_guild=True) 
    async def rtwitter(self, ctx: commands.Context, screen_name: str) -> None:
        try:
            session = self.db.Session()
            twitter_user = self.api.get_user(screen_name=screen_name)
            rows = session.query(TwitterModel).filter(TwitterModel.twitter_id == twitter_user.id, TwitterModel.channel_id == ctx.channel.id)
            count = rows.delete(synchronize_session=False)
            session.commit()
            await ctx.send(f"Deleted {count} entries")
        except tweepy.errors.NotFound:
            await ctx.send(f"Failed to find user for handle: \@{screen_name}")
        except Exception as e:
            self.logger.error(f"Error occured in rtwitter: {e}")
            session.rollback()
        finally:
            session.close()
    
    @commands.command()
    @commands.has_permissions(manage_guild=True) 
    async def ltwitter(self, ctx: commands.Context, member: Union[discord.Member, discord.User, str]) -> None:
        try:
            session = self.db.Session()

            if(type(member) == str):
                screen_name = member
                member = None
                twitter_user = self.api.get_user(screen_name=screen_name)
                rows = session.query(TwitterModel).filter(TwitterModel.twitter_id == twitter_user.id).all()
            else:
                rows = session.query(TwitterModel).filter(TwitterModel.discord_id == member.id).all()

            embed = self.embed.create_embed(member)
            embed.description = "```"

            if(len(rows) > 0):
                for row in rows:
                    user = await self.bot.fetch_user(row.discord_id)
                    channel = await self.bot.fetch_channel(row.channel_id)
                    twitter_user = self.api.get_user(user_id=row.twitter_id)
                    embed.description += f"{user} - {channel} ({channel.guild}) - {twitter_user.screen_name}\n"
            else:
                embed.description += "None"
            embed.description += "```"
            await ctx.send(embed=embed)

        except tweepy.errors.NotFound:
            await ctx.send(f"Failed to find user for handle: \@{screen_name}")
        except Exception as e:
            self.logger.error(f"Error occured in twitter: {e}")
            session.rollback()
        finally:
            session.close()
    
    def create_tweet_embed(self, member: Union[discord.Member, discord.User, None], twitter_user, tweet):
        text = re.sub(' https?:\/\/t.co\/[a-zA-Z0-9]{10}', '', tweet.full_text)
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&le;", "≤")
        text = text.replace("&ge;", "≥")
        
        embed = self.embed.create_embed(member)
        embed.description = text
        embed.set_author(name=f"{twitter_user.name} (@{twitter_user.screen_name})", url=f"https://twitter.com/{twitter_user.screen_name}", icon_url=f"{twitter_user.profile_image_url_https}")
        embed.title = "View tweet"
        embed.url = f"https://twitter.com/{twitter_user.screen_name}/status/{tweet.id}"
        embed.set_footer(text="Twitter", icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png")
        embed.timestamp = tweet.created_at
        media = tweet.entities.get("media", None)
        if(media != None):
            embed.set_image(url=media[0]["media_url_https"])
        return embed

async def setup(bot):
    await bot.add_cog(Twitter(bot))