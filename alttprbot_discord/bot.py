import asyncio
import importlib
import os
import logging
import io

import discord
from discord.ext import commands
from discord.ext.commands import errors
from discord.ext.commands.core import guild_only
from discord_sentry_reporting import use_sentry
from sentry_sdk import push_scope, capture_exception

from alttprbot_discord.util import config
from config import Config as c

config.init()

intents = discord.Intents.default()
intents.members = True  # pylint: disable=assigning-non-slot

# discord.http.API_VERSION = 9

discordbot = commands.Bot(
    command_prefix=commands.when_mentioned_or("$"),
    allowed_mentions=discord.AllowedMentions(
        everyone=False,
        users=True,
        roles=False
    ),
    intents=intents,
    debug_guild=508335685044928540 if c.DEBUG else None
)

if os.environ.get("SENTRY_URL"):
    use_sentry(discordbot, dsn=os.environ.get("SENTRY_URL"))

async def load_extensions():
    await discordbot.load_extension("alttprbot_discord.cogs.alttprgen")
    await discordbot.load_extension("alttprbot_discord.cogs.bontamw")
    await discordbot.load_extension("alttprbot_discord.cogs.daily")
    # await discordbot.load_extension("alttprbot_discord.cogs.discord_servers")
    await discordbot.load_extension("alttprbot_discord.cogs.misc")
    await discordbot.load_extension("alttprbot_discord.cogs.nickname")
    await discordbot.load_extension("alttprbot_discord.cogs.racetime_tools")
    await discordbot.load_extension("alttprbot_discord.cogs.role")
    await discordbot.load_extension("alttprbot_discord.cogs.sgdailies")
    await discordbot.load_extension("alttprbot_discord.cogs.sgl")
    await discordbot.load_extension("alttprbot_discord.cogs.tournament")
    await discordbot.load_extension("alttprbot_discord.cogs.voicerole")
    await discordbot.load_extension("alttprbot_discord.cogs.multiworld")
    await discordbot.load_extension("alttprbot_discord.cogs.generator")
    await discordbot.load_extension("alttprbot_discord.cogs.inquiry")

    if c.DEBUG:
        await discordbot.load_extension("alttprbot_discord.cogs.test")


    if importlib.util.find_spec('jishaku'):
        await discordbot.load_extension('jishaku')

    if importlib.util.find_spec('sahasrahbot_private'):
        await discordbot.load_extension('sahasrahbot_private.stupid_memes')

loop = asyncio.get_event_loop()
loop.run_until_complete(load_extensions())

@discordbot.event
async def on_command_error(ctx, error):
    riplink = discord.utils.get(ctx.bot.emojis, name='RIPLink')
    await ctx.message.remove_reaction('⌚', ctx.bot.user)
    logging.info(error)
    if isinstance(error, commands.CheckFailure):
        pass
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.message.add_reaction('🚫')
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.UserInputError):
        if riplink is None:
            riplink = '👎'
        await ctx.reply(error)
    else:
        if riplink is None:
            riplink = '👎'
        error_to_display = error.original if hasattr(
            error, 'original') else error

        await ctx.message.add_reaction(riplink)

        errorstr = repr(error_to_display)
        if len(errorstr) < 1990:
            await ctx.reply(f"```{errorstr}```")
        else:
            await ctx.reply(
                content="An error occured, please see attachment for the full message.",
                file=discord.File(io.StringIO(error_to_display), filename="error.txt")
            )
        with push_scope() as scope:
            scope.set_tag("guild", ctx.guild.id if ctx.guild else "")
            scope.set_tag("channel", ctx.channel.id if ctx.channel else "")
            scope.set_tag("user", f"{ctx.author.name}#{ctx.author.discriminator}" if ctx.author else "")
            raise error_to_display


@discordbot.event
async def on_application_command_error(ctx, error):
    logging.info(error)
    if isinstance(error, commands.CheckFailure):
        await ctx.respond("You are not authorized to use this command here.", ephemeral=True)
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.respond("You are not authorized to use this command here.", ephemeral=True)
    elif isinstance(error, commands.UserInputError):
        await ctx.respond(error)
    else:
        error_to_display = error.original if hasattr(error, 'original') else error

        errorstr = repr(error_to_display)
        if len(errorstr) < 1990:
            await ctx.respond(f"```{errorstr}```")
        else:
            await ctx.respond(
                content="An error occured, please see attachment for the full message.",
                file=discord.File(io.StringIO(error_to_display), filename="error.txt")
            )

        with push_scope() as scope:
            scope.set_tag("guild", ctx.guild.id if ctx.guild else "")
            scope.set_tag("channel", ctx.channel.id if ctx.channel else "")
            scope.set_tag("user", f"{ctx.author.name}#{ctx.author.discriminator}" if ctx.author else "")
            raise error_to_display


@discordbot.event
async def on_command(ctx):
    await ctx.message.add_reaction('⌚')


@discordbot.event
async def on_command_completion(ctx):
    await ctx.message.add_reaction('✅')
    await ctx.message.remove_reaction('⌚', ctx.bot.user)
