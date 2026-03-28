import discord
from discord.ext import commands
import os
import asyncio

# --- الإعدادات حقتك يا مشاري ---
SETUP_CHANNEL_ID = 1453714919403819008  
CLAIM_CHANNEL_ID = 1487370985479999519  
TICKET_CATEGORY_ID = 1470811187833864425 
ADMIN_ROLE_ID = 1467863010650362077      

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

# اللون الأسود للفخامة (0x000001 هو أقرب شيء للأسود الخالص في الديسكورد)
BLACK_COLOR = 0x000001

# --- أزرار التحكم داخل التكت ---
class TicketInside(discord.ui.View):
    def __init__(self, owner):
        super().__init__(timeout=None)
        self.owner = owner

    @discord.ui.button(label="ترك التكت 🚪", style=discord.ButtonStyle.secondary, custom_id="leave_ticket")
    async def leave_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        embed = discord.Embed(description=f"⚠️ **الإداري {interaction.user.mention} غادر التكت، متاح للاستلام الآن.**", color=BLACK_COLOR)
        await interaction.response.send_message(embed=embed)
        
        claim_channel = client.get_channel(CLAIM_CHANNEL_ID)
        if claim_channel:
            view = TicketClaimView(self.owner, interaction.channel)
            embed_log = discord.Embed(title="♻️ تكت عاد للمنافسة", description=f"صاحب التكت: {self.owner.mention}\nالروم: {interaction.channel.mention}", color=BLACK_COLOR)
            await claim_channel.send(embed=embed_log, view=view)

    @discord.ui.button(label="حذف التكت 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ الحذف للمدراء فقط!", ephemeral=True)
        await interaction.response.send_message("💀 **جاري تصفية التكت...**")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- زر الاستلام (أبيض فاقع) ---
class TicketClaimView(discord.ui.View):
    def __init__(self, owner, ticket_channel):
        super().__init__(timeout=None)
        self.owner = owner
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="استلام التكت ⚡", style=discord.ButtonStyle.secondary, custom_id="claim_btn")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # السماح للمستلم برؤية التكت
        await self.ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True, attach_files=True)
        
        embed = discord.Embed(
            title="✅ تمت السيطرة", 
            description=f"المستلم: {interaction.user.mention}\nالهدف: {self.owner.mention}", 
            color=BLACK_COLOR
        )
        await interaction.message.edit(embed=embed, view=None)
        
        await interaction.response.send_message(f"انطلق: {self.ticket_channel.mention}", ephemeral=True)
        await self.ticket_channel.send(f"🏴 **{interaction.user.mention} استلم التكت بنجاح. أبشر بسعدك يا {self.owner.mention}!**")

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
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=category)
        
        claim_channel = client.get_channel(CLAIM_CHANNEL_ID)
        if claim_channel:
            claim_view = TicketClaimView(user, channel)
            embed_log = discord.Embed(
                title="🏴 تكت جديد قيد الانتظار", 
                description=f"الشخص: {user.mention}\nالروم: {channel.mention}\nالإدارة: <@&{ADMIN_ROLE_ID}>", 
                color=BLACK_COLOR
            )
            await claim_channel.send(embed=embed_log, view=claim_view)
        
        await interaction.response.send_message(f"✅ **انفتحت الروم: {channel.mention}**", ephemeral=True)
        
        welcome_embed = discord.Embed(
            title="🏴 نظام الدعم الفني", 
            description=f"أهلاً {user.mention}..\n**اكتب طلبك وانتظر الإدارة تستلم التكت.**", 
            color=BLACK_COLOR
        )
        await channel.send(embed=welcome_embed, view=TicketInside(user))

@client.event
async def on_ready():
    client.add_view(TicketView())
    client.add_view(TicketInside(None)) 
    print(f'✅ البوت الزاحف شغال يا مشاري!')

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="🏴 مركز الدعم الفني", 
        description="**لأصحاب الفخامة فقط، اضغط لفتح تكت.**", 
        color=BLACK_COLOR
    )
    await ctx.send(embed=embed, view=TicketView())

token = os.getenv('DISCORD_TOKEN')
client.run(token)
