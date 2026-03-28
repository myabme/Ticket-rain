import discord
from discord.ext import commands
import os
import asyncio

# --- الإعدادات الخاصة بك ---
TICKET_CHANNEL_ID = 1453714919403819008  
TICKET_CATEGORY_ID = 1470811187833864425 
ADMIN_MENTION = "<@&1467863010650362077>" # رتبة الإدارة

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

# --- أزرار التحكم داخل التكت (استلام وحذف) ---
class TicketControls(discord.ui.View):
    def __init__(self, owner):
        super().__init__(timeout=None)
        self.owner = owner # صاحب التكت

    @discord.ui.button(label="استلام التكت 📩", style=discord.ButtonStyle.success, custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # التأكد إن اللي ضغط أدمن
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ هذا الزر للإدارة فقط يا وحش!", ephemeral=True)
        
        button.disabled = True
        await interaction.message.edit(view=self)
        
        embed = discord.Embed(
            title="✅ تم استلام التكت",
            description=f"الإداري: {interaction.user.mention}\nصاحب التكت: {self.owner.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="حذف التكت 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ الحذف للإدارة فقط!", ephemeral=True)
        
        embed = discord.Embed(
            title="⚠️ سيتم حذف التكت",
            description=f"بواسطة: {interaction.user.mention}\nسيتم الإغلاق بعد 5 ثوانٍ...",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- زر فتح التكت الأساسي ---
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
        
        # إنشاء الروم داخل الكاتيجوري
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=category
        )
        
        await interaction.response.send_message(f"✅ تم فتح تكتك: {channel.mention}", ephemeral=True)
        
        # رسالة ترحيب فخمة (Embed)
        welcome_embed = discord.Embed(
            title="✨ تكت جديد - قسم الدعم الفني",
            description=f"أهلاً بك {user.mention} في سيرفرنا!\n\n**يُرجى كتابة مشكلتك بوضوح وانتظار الرد.**\n\nتنبيه للإدارة: {ADMIN_MENTION}",
            color=discord.Color.blue()
        )
        welcome_embed.set_footer(text="نحن هنا لخدمتك ⚡")
        
        await channel.send(embed=welcome_embed, view=TicketControls(user))

@client.event
async def on_ready():
    client.add_view(TicketView())
    client.add_view(TicketControls(None))
    print(f'✅ البوت شغال: {client.user}')

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.message.delete()
    setup_embed = discord.Embed(
        title="مركز الدعم الفني 🎫",
        description="إذا واجهت مشكلة أو تبي مساعدة، اضغط على الزر تحت وبنخدمك بعيوننا!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=setup_embed, view=TicketView())

@client.event
async def on_message(message):
    if message.author == client.user: return
    
    # نظام الـ Come
    if message.content.lower() == "come" and "ticket-" in message.channel.name:
        if message.author.guild_permissions.administrator:
            user_name = message.channel.name.replace("ticket-", "")
            member = discord.utils.get(message.guild.members, name=user_name)
            if member:
                try: await member.send(f"يا وحش الإدارة تنتظرك في التكت: {message.channel.mention}")
                except: pass

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
