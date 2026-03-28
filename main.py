import discord
from discord.ext import commands
import os

# --- الإعدادات اللي عطيتني إياها ---
TICKET_CHANNEL_ID = 1453714919403819008  # الروم اللي يرسل فيها الزر
TICKET_CATEGORY_ID = 1470811187833864425 # القسم اللي تفتح فيه التكتات

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

# --- كود نظام التكت (الأزرار) ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت 🎫", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # جلب القسم (Category)
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        # الصلاحيات (العضو والآدمن يشوفونها والباقي لا)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # رتبة Admin
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # إنشاء الروم باسم العضو داخل الكاتيجوري
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=category
        )
        
        await interaction.response.send_message(f"✅ تم فتح تكتك هنا: {channel.mention}", ephemeral=True)
        
        # رسالة الترحيب والمنشن
        mention_admin = admin_role.mention if admin_role else "@Admin"
        await channel.send(f"مرحباً {user.mention}، أبشر بسعدك! {mention_admin} بيفيدونك الحين.")

@client.event
async def on_ready():
    client.add_view(TicketView()) # عشان الزر يضل شغال دايم
    print(f'✅ البوت شغال باسم: {client.user}')
    
    # يرسل الزر تلقائياً في الروم المخصص
    channel = client.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.purge(limit=5) # يمسح الزر القديم عشان ما يتكرر
        await channel.send("اضغط على الزر تحت لفتح تكت دعم فني 🎫", view=TicketView())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 1. نظام الـ Come (يرسل للخاص إذا كان داخل تكت)
    if message.content.lower() == "come" and "ticket-" in message.channel.name:
        if message.author.guild_permissions.administrator:
            # استخراج اسم العضو من اسم الروم
            user_name = message.channel.name.replace("ticket-", "")
            member = discord.utils.get(message.guild.members, name=user_name)
            if member:
                try:
                    await member.send(f"يا {member.mention}، الإدارة تنتظرك في التكت الخاص بك: {message.channel.mention}")
                    await message.channel.send(f"✅ تم إرسال رسالة لـ {member.mention} في الخاص.")
                except:
                    await message.channel.send("❌ ما قدرت أرسل له خاص (مقفل الخاص).")

    # 2. نظام حماية السب (المنع)
    bad_words = ['يلعن', 'كافر', 'عبد', 'كس', 'منيوك', 'نيجر', 'قحبه', 'شرموط', 'ابوك', 'انيكك', 'يبن', 'امك', 'ديوث']
    clean_content = "".join(char for char in message.content if char.isalnum()).lower()
    for word in bad_words:
        if word in clean_content or word in message.content.lower():
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention} ممنوع السب يا وحش!")
                return
            except: pass

    await client.process_commands(message)

# تشغيل البوت
token = os.getenv('DISCORD_TOKEN')
if token:
    client.run(token)
else:
    print("❌ خطأ: لم يتم العثور على التوكن في Variables!")
