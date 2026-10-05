import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import urllib.parse
from aiohttp import web

print("[DEBUG] BOT STARTING")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
VERIFY_CHANNEL_ID = int(os.getenv("VERIFY_CHANNEL_ID", "0"))
VERIFY_ROLE_ID = int(os.getenv("VERIFY_ROLE_ID", "0"))
WAITING_ROLE_ID = int(os.getenv("WAITING_ROLE_ID", "0"))
LINK_URL = os.getenv("LINK_URL", "https://example.com")
PORT = int(os.getenv("PORT", "8080"))

async def handle_ping(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"[+] HTTP server running on port {PORT}")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⏳ חכה 15 דקות", style=discord.ButtonStyle.secondary, custom_id="wait_15")
    async def wait_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏳ קיבלתי.", ephemeral=True)
        await asyncio.sleep(15 * 60)
        guild = interaction.guild
        member = interaction.user
        verify_role = guild.get_role(VERIFY_ROLE_ID)
        waiting_role = guild.get_role(WAITING_ROLE_ID)
        if verify_role and waiting_role:
            try:
                await member.add_roles(verify_role)
                if waiting_role in member.roles:
                    await member.remove_roles(waiting_role)
                await member.send("✅ קיבלת גישה!")
            except Exception as e:
                print(f"Error: {e}")

    @discord.ui.button(label="🔗 היכנס לקישור", style=discord.ButtonStyle.success, custom_id="go_link")
    async def link_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_name = str(interaction.user)
        encoded_name = urllib.parse.quote(user_name)
        unique_link = f"{LINK_URL}?user={encoded_name}"
        await interaction.response.send_message(f"🔗 {unique_link}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"[+] Logged in as {bot.user}")
    bot.add_view(VerifyView())
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"[+] Synced {len(synced)} commands")
    except Exception as e:
        print(f"[-] Sync error: {e}")

@bot.event
async def on_member_join(member):
    waiting_role = member.guild.get_role(WAITING_ROLE_ID)
    if waiting_role:
        try:
            await member.add_roles(waiting_role)
            print(f"[+] Gave waiting role to {member.name}")
        except Exception as e:
            print(f"[-] Error: {e}")

@bot.tree.command(name="setup", description="שולח את הודעת האימות")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("❌ חדר לא נמצא.", ephemeral=True)
        return
    embed = discord.Embed(
        title="🔒 Verification - אימות משתמש",
        description="**Z.FOX IL ACCOUNT**\n\nבחר:\n**⏳ חכה 15 דקות**\n**🔗 היכנס לקישור**",
        color=0x5865F2
    )
    await channel.send(embed=embed, view=VerifyView())
    await interaction.followup.send("✅ נשלח.", ephemeral=True)

async def main():
    await start_web_server()
    print("[DEBUG] Starting bot...")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
