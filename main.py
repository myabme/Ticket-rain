import discord
from discord.ext import commands
import os
import asyncio

# --- الإعدادات حقتك ---
TICKET_CHANNEL_ID = 1453714919403819008  # الروم اللي يرسل فيها زر الاستلام (والسيت اب)
TICKET_CATEGORY_ID = 1470811187833864425 # القسم اللي تفتح فيه التكتات
ADMIN_ROLE_ID = 1467863010650362077      # رقم رتبة الإدارة (بدون منشن)

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
        # الإداري يترك التكت ويرجع مخفي عنه
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ هذا للإدارة فقط!", ephemeral=True)
        
        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        await interaction.response.send_message(f"⚠️ الإداري {interaction.user.mention} ترك التكت، متاح للاستلام مرة أخرى.", color=discord.Color.orange())
        
        # إعادة إرسال زر الاستلام في الروم المخصص
        channel_log = client.get_channel(TICKET_CHANNEL_ID)
        view = TicketClaimView(self.owner, interaction.channel)
        embed = discord.Embed(title="♻️ تكت متاح للاستلام", description=f"صاحب التكت: {self.owner.mention}\nالروم: {interaction.channel.mention}", color=discord.Color.blue())
        await channel_log.send(embed=embed, view=view)

    @discord.ui.button(label="حذف التكت 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ الحذف للإدارة فقط!", ephemeral=True)
        await interaction.response.send_message("⚠️ سيتم الحذف خلال 5 ثوانٍ...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- زر الاستلام (Claim) اللي يظهر للإدارة ---
class TicketClaimView(discord.ui.View):
    def __init__(self, owner, ticket_channel):
        super().__init__(timeout=None)
        self.owner = owner
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="استلام التكت 📩", style=discord.ButtonStyle.success, custom_id="claim_btn")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ للإدارة فقط!", ephemeral=True)
        
        # السماح للمستلم فقط برؤية التكت
        await self.ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True, attach_files=True)
        
        # تعديل رسالة الاستلام
        embed = discord.Embed(title="✅ تم الاستلام", description=f"المستلم: {interaction.user.mention}\nصاحب التكت: {self.owner.mention}", color=discord.Color.green())
        await interaction.message.edit(embed=embed, view=None)
        
        await interaction.response.send_message(f"تم استلام التكت بنجاح: {self.ticket_channel.mention}", ephemeral=True)
        await self.ticket_channel.send(f"✅ {interaction.user.mention} استلم التكت لخدمتك يا {self.owner.mention}!")

# --- زر فتح التكت الأساسي ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت 🎫", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        # التكت مخفي عن الجميع (حتى الإدارة) بالبداية، فقط صاحب التكت والبوت
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=category)
        
        # إرسال زر الاستلام للإدارة في الروم المخصص
        channel_log = client.get_channel(TICKET_CHANNEL_ID)
        claim_view = TicketClaimView(user, channel)
        embed_log = discord.Embed(title="🎟️ تكت جديد بانتظار الاستلام", description=f"صاحب التكت: {user.mention}\nالروم: {channel.mention}\nرتبة الإدارة: <@&{ADMIN_ROLE_ID}>", color=discord.Color.gold())
        await channel_log.send(embed=embed_log, view=claim_view)
        
        await interaction.response.send_message(f"✅ تم فتح تكتك: {channel.mention} (بانتظار استلام إداري)", ephemeral=True)
        
        welcome_embed = discord.Embed(title="✨ دعم فني", description=f"أهلاً {user.mention}، سيقوم إداري باستلام التكت قريباً.", color=discord.Color.blue())
        await channel.send(embed=welcome_embed, view=TicketInside(user))

@client.event
async def on_ready():
    client.add_view(TicketView())
    print(f'✅ البوت شغال: {client.user}')

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="مركز المساعدة 🎫", description="اضغط لفتح تكت خاص", color=discord.Color.purple())
    await ctx.send(embed=embed, view=TicketView())

token = os.getenv('DISCORD_TOKEN')
client.run(token)
