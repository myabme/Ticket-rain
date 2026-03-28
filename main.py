import discord
from discord.ext import commands
import os

# --- الإعدادات اللي عطيتني إياها ---
TICKET_CHANNEL_ID = 1453714919403819008  
TICKET_CATEGORY_ID = 1470811187833864425 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت 🎫", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=category
        )
        
        await interaction.response.send_message(f"✅ تم فتح تكتك هنا: {channel.mention}", ephemeral=True)
        mention_admin = admin_role.mention if admin_role else "@Admin"
        await channel.send(f"مرحباً {user.mention}، أبشر بسعدك! {mention_admin} بيفيدونك الحين.")

@client.event
async def on_ready():
    client.add_view(TicketView())
    print(f'✅ البوت شغال: {client.user}')
    
    # محاولة إرسال تلقائي (اختياري)
    channel = client.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("نظام التكت شغال! اضغط بالأسفل 🎫", view=TicketView())

# --- الأمر اليدوي اللي طلبته (يرسل التكت) ---
@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.message.delete() # يمسح أمرك عشان الروم تضل نظيفة
    await ctx.send("**نظام الدعم الفني 🎫**\nاضغط على الزر بالأسفل لفتح تكت والتحدث مع الإدارة.", view=TicketView())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # نظام الـ Come
    if message.content.lower() == "come" and "ticket-" in message.channel.name:
        if message.author.guild_permissions.administrator:
            user_name = message.channel.name.replace("ticket-", "")
            member = discord.utils.get(message.guild.members, name=user_name)
            if member:
                try:
                    await member.send(f"يا {member.mention}، الإدارة تنتظرك في التكت: {message.channel.mention}")
                    await message.channel.send(f"✅ تم إرسال رسالة لـ {member.mention} في الخاص.")
                except:
                    await message.channel.send("❌ مقفل الخاص.")

    # حماية السب
    bad_words = ['يلعن', 'كافر', 'عبد', 'كس', 'منيوك', 'قحبه', 'شرموط', 'ابوك', 'انيكك', 'يبن', 'امك']
    clean_content = "".join(char for char in message.content if char.isalnum()).lower()
    for word in bad_words:
        if word in clean_content or word in message.content.lower():
            try:
                await message.delete()
                return
            except: pass

    await client.process_commands(message)

token = os.getenv('DISCORD_TOKEN')
client.run(token)
