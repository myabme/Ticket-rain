import discord
from discord.ext import commands
import os
import asyncio

# --- الإعدادات حقتك يا مشاري ---
SETUP_CHANNEL_ID = 1453714919403819008  # الروم اللي فيها زر "فتح تكت"
CLAIM_CHANNEL_ID = 1487370985479999519  # الروم اللي يرسل فيها "زر الاستلام" للإدارة
TICKET_CATEGORY_ID = 1470811187833864425 # القسم اللي تفتح فيه التكتات
ADMIN_ROLE_ID = 1467863010650362077      # رتبة الإدارة

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

# --- أزرار التحكم داخل التكت (ترك وحذف) ---
class TicketInside(discord.ui.View):
    def __init__(self, owner):
        super().__init__(timeout=None)
        self.owner = owner

    @discord.ui.button(label="ترك التكت 🚪", style=discord.ButtonStyle.secondary, custom_id="leave_ticket")
    async def leave_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ هذا للإدارة فقط!", ephemeral=True)
        
        # سحب صلاحية الرؤية من الإداري اللي ترك
        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        
        # إشعار داخل التكت
        await interaction.response.send_message(f"⚠️ الإداري {interaction.user.mention} ترك التكت، متاح للاستلام مرة أخرى.")
        
        # إعادة إرسال زر الاستلام في روم الإدارة
        claim_channel = client.get_channel(CLAIM_CHANNEL_ID)
        if claim_channel:
            view = TicketClaimView(self.owner, interaction.channel)
            embed = discord.Embed(title="♻️ تكت عاد للاستلام", description=f"صاحب التكت: {self.owner.mention}\nالروم: {interaction.channel.mention}", color=discord.Color.orange())
            await claim_channel.send(embed=embed, view=view)

    @discord.ui.button(label="حذف التكت 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ الحذف للإدارة فقط!", ephemeral=True)
        await interaction.response.send_message("⚠️ سيتم الحذف خلال 5 ثوانٍ...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- زر الاستلام (Claim) اللي يروح لروم الإدارة ---
class TicketClaimView(discord.ui.View):
    def __init__(self, owner, ticket_channel):
        super().__init__(timeout=None)
        self.owner = owner
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="استلام التكت 📩", style=discord.ButtonStyle.success, custom_id="claim_btn")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ للإدارة فقط!", ephemeral=True)
        
        # السماح للمستلم فقط برؤية التكت (فتح القفل عنه)
        await self.ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True, attach_files=True)
        
        # تحديث رسالة الاستلام في روم الإدارة
        embed = discord.Embed(title="✅ تم الاستلام", description=f"الإداري: {interaction.user.mention}\nصاحب التكت: {self.owner.mention}\nالروم: {self.ticket_channel.mention}", color=discord.Color.green())
        await interaction.message.edit(embed=embed, view=None)
        
        await interaction.response.send_message(f"تم توجيهك للتكت: {self.ticket_channel.mention}", ephemeral=True)
        await self.ticket_channel.send(f"✅ الإداري {interaction.user.mention} استلم التكت لخدمتك يا {self.owner.mention}!")

# --- زر فتح التكت الأساسي ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت 🎫", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        # التكت مخفي عن رتبة الإدارة والجميع (فقط صاحب التكت والبوت)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # إنشاء الروم مخفية
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=category)
        
        # إرسال زر الاستلام في الروم المخصص (1487370985479999519)
        claim_channel = client.get_channel(CLAIM_CHANNEL_ID)
        if claim_channel:
            claim_view = TicketClaimView(user, channel)
            embed_log = discord.Embed(
                title="🎟️ تكت جديد ينتظر الاستلام", 
                description=f"الشخص: {user.mention}\nالروم: {channel.mention}\nالإدارة: <@&{ADMIN_ROLE_ID}>", 
                color=discord.Color.gold()
            )
            await claim_channel.send(embed=embed_log, view=claim_view)
        
        await interaction.response.send_message(f"✅ تم فتح تكتك: {channel.mention}\nانتظر استلام أحد الإداريين لطلبك.", ephemeral=True)
        
        welcome_embed = discord.Embed(title="✨ نظام الدعم الفني", description=f"أهلاً {user.mention}، سيتم خدمتك فور استلام التكت من الإدارة.", color=discord.Color.blue())
        await channel.send(embed=welcome_embed, view=TicketInside(user))

@client.event
async def on_ready():
    client.add_view(TicketView())
    client.add_view(TicketInside(None)) # تسجيل الأزرار عشان ما تعطل
    print(f'✅ البوت شغال يا مشاري: {client.user}')

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="مركز المساعدة 🎫", description="اضغط على الزر بالأسفل لفتح تكت خاص بك", color=discord.Color.blue())
    await ctx.send(embed=embed, view=TicketView())

token = os.getenv('DISCORD_TOKEN')
client.run(token)
