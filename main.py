import discord
from discord.ext import commands
from discord import app_commands
import os

# إعدادات البوت (العيون)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

# --- 1. كود نظام التكت (Tickets) ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت 🎫", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # إنشاء الروم باسم العضو
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # إضافة رتبة Admin للروم (تأكد إن اسم الرتبة Admin أو غيرها تحت)
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        await interaction.response.send_message(f"تم فتح التكت الخاص بك: {channel.mention}", ephemeral=True)
        
        # رسالة الترحيب داخل التكت ومنشن الإدارة
        mention_admin = admin_role.mention if admin_role else "@Admin"
        await channel.send(f"مرحباً {user.mention}، أبشر بسعدك! {mention_admin} بيفيدونك الحين.")

@client.event
async def on_ready():
    client.add_view(TicketView()) # عشان الزر يفضل شغال حتى لو طفى البوت
    print(f'✅ البوت شغال باسم: {client.user}')

# أمر لإرسال زر التكت (أكتب !setup في أي روم)
@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    view = TicketView()
    await ctx.send("اضغط على الزر تحت لفتح تكت دعم فني 👇", view=view)

# --- 2. أمر الـ Come (يرسل للخاص) ---
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # إذا الإدمن كتب come داخل تكت
    if message.content.lower() == "come" and "ticket-" in message.channel.name:
        if message.author.guild_permissions.administrator:
            # نجيب العضو صاحب التكت من اسم الروم
            user_name = message.channel.name.replace("ticket-", "")
            member = discord.utils.get(message.guild.members, name=user_name)
            
            if member:
                try:
                    await member.send(f"يا {member.mention}، الإدارة تنتظرك في التكت حقك: {message.channel.mention}")
                    await message.channel.send(f"✅ تم إرسال رسالة لـ {member.mention} في الخاص.")
                except:
                    await message.channel.send("❌ ما قدرت أرسل له خاص (مقفل الخاص).")

    # --- 3. نظام حماية السب (حقنا القديم) ---
    bad_words = ['يلعن', 'كافر', 'عبد', 'كس', 'منيوك', 'نيجر', 'قحبه', 'شرموط', 'ابوك', 'انيكك', 'يبن', 'امك']
    clean_content = "".join(char for char in message.content if char.isalnum()).lower()
    for word in bad_words:
        if word in clean_content or word in message.content.lower():
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention} تم حذف رسالتك (كلمات ممنوعة)!")
                return
            except: pass

    await client.process_commands(message)

token = os.getenv('DISCORD_TOKEN')
client.run(token)
