import discord
from discord import Bot
import yt_dlp
import asyncio
import os
from collections import deque
from openai import OpenAI

# =====================
# GLOBALS
# =====================

bot = Bot()
music_queues = {}  
AUTO_DISCONNECT_DELAY = 120  
disconnect_tasks = {}  
client = OpenAI()
YDL_OPTS = {
    "quiet": True,
    "default_search": "ytsearch1",
    "noplaylist": True,
    "format": "bestaudio/best",
    "cookiesfrombrowser": ("chrome",),
    "js_runtime": "deno",
    "remote_components": ["ejs:github"],
}

ydl = yt_dlp.YoutubeDL(YDL_OPTS)


GUILD_ID = 1126806265012699136

#for opus bug

if not discord.opus.is_loaded():
    for path in (
        "/opt/homebrew/lib/libopus.dylib",   # Apple Silicon
    ):
        if os.path.exists(path):
            discord.opus.load_opus(path)
            break

#events

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.sync_commands(guild_ids=[GUILD_ID])


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    vc = guild.voice_client

    if vc is None:
        return

    guild_id = guild.id

    #case 1: someone joined the bot's voice channel
    if after.channel == vc.channel:
        task = disconnect_tasks.pop(guild_id, None)
        if task:
            task.cancel()

    # case 2:someone left the bot's voice channel 
    if before.channel == vc.channel:
        humans_left = [
            m for m in vc.channel.members
            if not m.bot
        ]

        if not humans_left:
            if guild_id not in disconnect_tasks:
                disconnect_tasks[guild_id] = asyncio.create_task(
                    auto_disconnect(guild)
                )


#helpers

async def play_next(ctx):
    guild_id = ctx.guild.id
    vc = ctx.guild.voice_client

    if vc is None:
        return

    if guild_id not in music_queues or not music_queues[guild_id]:
        return

    url, title = music_queues[guild_id].popleft()

    ffmpeg_opts = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    source = discord.FFmpegPCMAudio(url, **ffmpeg_opts)

    def after_playing(error):
        if error:
            print(f"Playback error: {error}")

        asyncio.run_coroutine_threadsafe(
            play_next(ctx),
            bot.loop
        )

    vc.play(source, after=after_playing)
    await ctx.channel.send(f"▶️ Now playing: **{title}**")

async def auto_disconnect(guild):
    await asyncio.sleep(AUTO_DISCONNECT_DELAY)

    vc = guild.voice_client
    if vc is None:
        return

    # check if anyone is left
    humans = [
        member for member in vc.channel.members
        if not member.bot
    ]

    if humans:
        return  # someone came back

    # No humans, then disconnect
    music_queues.pop(guild.id, None)

    if vc.is_playing() or vc.is_paused():
        vc.stop()

    await vc.disconnect()



# commands


@bot.slash_command(description="Ping test command")
async def ping(ctx):
    await ctx.respond("Pong")


@bot.slash_command(description="Join your voice channel")
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.respond("❌ You are not in a voice channel.")
        return

    channel = ctx.author.voice.channel
    vc = ctx.guild.voice_client

    if vc is None:
        await channel.connect()
    else:
        if vc.channel != channel:
            await vc.move_to(channel)

    await ctx.respond(f"Joined **{channel.name}**")



@bot.slash_command(description="Play a song by name or URL")
async def play(ctx, query: str):
    await ctx.defer()

    if ctx.author.voice is None:
        await ctx.followup.send("You must be in a voice channel.")
        return

    # autojoin
    if ctx.guild.voice_client is None:
        await ctx.author.voice.channel.connect()

    vc = ctx.guild.voice_client
    guild_id = ctx.guild.id

    if guild_id not in music_queues:
        music_queues[guild_id] = deque()

    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch1",
        "noplaylist": True,
        "format": "bestaudio/best",
        "cookiesfrombrowser": ("chrome",),
        "js_runtime": "deno",
        "remote_components": ["ejs:github"],
    }

    info = ydl.extract_info(query, download=False)
    if "entries" in info:
        info = info["entries"][0]

    url = info["url"]
    title = info.get("title", "Unknown title")


    # queue add
    music_queues[guild_id].append((url, title))

    if not vc.is_playing():
        await play_next(ctx)
    else:
        await ctx.followup.send(f"Added to queue: **{title}**")

@bot.slash_command(description="Leave the voice channel and clear the queue")
async def leave(ctx):
    vc = ctx.guild.voice_client

    if vc is None:
        await ctx.respond("I am not in a voice channel.")
        return

    guild_id = ctx.guild.id
    music_queues.pop(guild_id, None)

    if vc.is_playing():
        vc.stop()

    await vc.disconnect()
    await ctx.respond("Left the voice channel and cleared the queue.")

@bot.slash_command(description="Skip the current song")
async def skip(ctx):
    vc = ctx.guild.voice_client

    if vc is None or not vc.is_connected():
        await ctx.respond("I am not in a voice channel.")
        return

    if not vc.is_playing():
        await ctx.respond("Nothing is playing.")
        return

    vc.stop()  
    await ctx.respond("Skipped.")

@bot.slash_command(description="Pause the current song")
async def pause(ctx):
    vc = ctx.guild.voice_client

    if vc is None or not vc.is_connected():
        await ctx.respond("I am not in a voice channel.")
        return

    if not vc.is_playing():
        await ctx.respond("❌ Nothing is playing.")
        return

    vc.pause()
    await ctx.respond("⏸️ Paused.")

@bot.slash_command(description="Resume the paused song")
async def resume(ctx):
    vc = ctx.guild.voice_client

    if vc is None or not vc.is_connected():
        await ctx.respond("❌ I am not in a voice channel.")
        return

    if not vc.is_paused():
        await ctx.respond("❌ Nothing is paused.")
        return

    vc.resume()
    await ctx.respond("Resumed.")

@bot.slash_command(description="Show the current music queue")
async def queue_show(ctx):
    guild_id = ctx.guild.id

    if guild_id not in music_queues or not music_queues[guild_id]:
        await ctx.respond("The queue is empty.")
        return

    message = "🎶 **Queue:**\n"
    for i, (_, title) in enumerate(music_queues[guild_id], start=1):
        message += f"`{i}.` {title}\n"

    await ctx.respond(message)

@bot.slash_command(description="Remove a song from the queue by its number")
async def queue_remove(ctx, index: int):
    guild_id = ctx.guild.id

    if guild_id not in music_queues or not music_queues[guild_id]:
        await ctx.respond("The queue is empty.")
        return

    queue = music_queues[guild_id]

    if index < 1 or index > len(queue):
        await ctx.respond("Invalid queue index.")
        return

    removed = queue[index - 1]
    del queue[index - 1]

    await ctx.respond(f"Removed **{removed[1]}** from the queue.")

@bot.slash_command(description="Clear the music queue")
async def queue_clear(ctx):
    guild_id = ctx.guild.id

    if guild_id not in music_queues or not music_queues[guild_id]:
        await ctx.respond("The queue is already empty.")
        return

    music_queues[guild_id].clear()
    await ctx.respond("🧹 Queue cleared.")

@bot.slash_command(description="Add a song directly to the queue")
async def queue_add(ctx, query: str):
    await ctx.defer()

    guild_id = ctx.guild.id

    if guild_id not in music_queues:
        music_queues[guild_id] = deque()

    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch1",
        "noplaylist": True,
        "format": "bestaudio/best",
        "cookiesfrombrowser": ("chrome",),
        "js_runtime": "deno",
        "remote_components": ["ejs:github"],
    }

    info = ydl.extract_info(query, download=False)
    if "entries" in info:
        info = info["entries"][0]

    url = info["url"]
    title = info.get("title", "Unknown title")


    music_queues[guild_id].append((url, title))
    await ctx.followup.send(f"Added to queue: **{title}**")

@bot.slash_command(description="Ask ChatGPT a question")
async def ask(ctx, prompt: str):
    await ctx.defer()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer in a single short paragraph. "
                    "No headings, no titles, no lists, no emojis. "
                    "Do not offer follow-up help or suggestions. "
                    "Be clear and concise."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=120,
        temperature=0.6
    )

    text = response.choices[0].message.content.strip()
    await ctx.followup.send(text)



# run bot



bot.run("DISCORD_TOKEN")
