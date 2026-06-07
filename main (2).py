"""
main.py — Zerith Security — DÜZELTME PAKETİ
=============================================
DEĞİŞTİRİLEN BÖLÜMLER:
  1. guild_settings tablosuna  filter_bypass_role_id  sütunu eklendi
  2. on_message → kurucu, admin ve bypass rolü olan kişiler filtreden MUAF
  3. Küfür filtresi durumu artık DB'de kalıcı (bot restart'ta sıfırlanmıyor)
  4. /setup filtrebypass  komutu eklendi
  5. Reklam filtresi de aynı bypass kontrolünden geçiyor

Kodu mevcut main.py'ye PARÇA PARÇA uygula — bütününü değiştirmek yerine
aşağıdaki 5 yama bloğunu ilgili yerlere yapıştır.
"""

# ============================================================
# YAMA 1 — db_init() içindeki guild_settings CREATE sorgusunu bu ile değiştir
# ============================================================

DB_INIT_PATCH = """
    c.execute(\"\"\"CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id TEXT PRIMARY KEY,
        welcome_channel_id TEXT,
        goodbye_channel_id TEXT,
        log_channel_id TEXT,
        mod_role_id TEXT,
        mute_role_id TEXT,
        autorole_id TEXT,
        prefix TEXT DEFAULT '!',
        welcome_message TEXT DEFAULT 'Sunucuya hoş geldin {user}! 🎉',
        goodbye_message TEXT DEFAULT '{user} sunucudan ayrıldı.',
        level_up_channel_id TEXT,
        suggestion_channel_id TEXT,
        ticket_category_id TEXT,
        ticket_log_channel_id TEXT,
        kufur_filtre INTEGER DEFAULT 1,
        reklam_filtre INTEGER DEFAULT 1,
        filter_bypass_role_id TEXT
    )\"\"\")

    # Eski DB'lere yeni sütunları ekle (migrate)
    for col, definition in [
        ("kufur_filtre",        "INTEGER DEFAULT 1"),
        ("reklam_filtre",       "INTEGER DEFAULT 1"),
        ("filter_bypass_role_id", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE guild_settings ADD COLUMN {col} {definition}")
        except Exception:
            pass  # Zaten varsa hata vermez
"""

# ============================================================
# YAMA 2 — Yardımcı fonksiyonlar: dosyanın üst bölümüne ekle
# ============================================================

HELPER_PATCH = """
# ─── Filtre bypass kontrolü ───────────────────────────────
def is_filter_exempt(member: discord.Member, settings: dict) -> bool:
    \"\"\"
    Şu kişiler filtreden MUAF tutulur:
      • Sunucu kurucusu
      • Administrator yetkisi olan herkes
      • filter_bypass_role_id olarak ayarlanmış rolü taşıyan kişi
    \"\"\"
    # Kurucu
    if member.guild.owner_id == member.id:
        return True
    # Admin
    if member.guild_permissions.administrator:
        return True
    # Bypass rolü
    bypass_role_id = settings.get("filter_bypass_role_id")
    if bypass_role_id:
        bypass_role = member.guild.get_role(int(bypass_role_id))
        if bypass_role and bypass_role in member.roles:
            return True
    return False

# ─── Filtre durumu DB'den oku ────────────────────────────
def get_filter_status(guild_id, key="kufur_filtre") -> bool:
    \"\"\"key: 'kufur_filtre' veya 'reklam_filtre' — True = açık\"\"\"
    settings = get_settings(guild_id)
    val = settings.get(key)
    return bool(val) if val is not None else True

def set_filter_status(guild_id, key, value: bool):
    set_setting(guild_id, key, 1 if value else 0)
"""

# ============================================================
# YAMA 3 — on_message() içindeki filtre bloğunu bu ile değiştir
#          (KUFUR_FILTRE_KAPALI set'ine artık gerek yok)
# ============================================================

ON_MESSAGE_FILTER_PATCH = """
    # ── Filtre muafiyet kontrolü ──────────────────────────
    settings = get_settings(message.guild.id)
    exempt = is_filter_exempt(message.author, settings)

    # ── Küfür filtresi ────────────────────────────────────
    if not exempt and get_filter_status(message.guild.id, "kufur_filtre"):
        if kufur_kontrol(icerik):
            await message.delete()
            count = warn_add(message.author.id, message.guild.id, bot.user.id, "Otomatik: Küfür")
            await message.channel.send(
                f"⚠️ {message.author.mention} küfür yasaktır! Uyarı: **{count}/3**",
                delete_after=6
            )
            embed = discord.Embed(title="🚫 Küfür Engellendi", color=discord.Color.red())
            embed.add_field(name="Kullanıcı", value=f"{message.author} ({message.author.id})")
            embed.add_field(name="Kanal", value=message.channel.mention)
            embed.add_field(name="Toplam Uyarı", value=f"{count}/3")
            embed.timestamp = discord.utils.utcnow()
            await log_send(message.guild, embed)
            if count >= 3:
                try:
                    await message.author.timeout(timedelta(minutes=10), reason="3 uyarı — küfür")
                    await message.channel.send(
                        f"🔇 {message.author.mention} 3 uyarı sonucu 10 dakika susturuldu.",
                        delete_after=8
                    )
                    warn_clear(message.author.id, message.guild.id)
                except Exception:
                    pass
            return

    # ── Reklam filtresi ───────────────────────────────────
    if not exempt and get_filter_status(message.guild.id, "reklam_filtre"):
        for ifade in REKLAM_IFADELERI:
            if ifade in icerik:
                await message.delete()
                count = warn_add(message.author.id, message.guild.id, bot.user.id, "Otomatik: Reklam")
                await message.channel.send(
                    f"📢 {message.author.mention} reklam yasaktır! Uyarı: **{count}/3**",
                    delete_after=6
                )
                embed = discord.Embed(title="📢 Reklam Engellendi", color=discord.Color.orange())
                embed.add_field(name="Kullanıcı", value=f"{message.author} ({message.author.id})")
                embed.add_field(name="Kanal", value=message.channel.mention)
                embed.timestamp = discord.utils.utcnow()
                await log_send(message.guild, embed)
                return
"""

# ============================================================
# YAMA 4 — Küfür/Reklam filtre komutlarını bu ile değiştir
#          (DB kalıcı, restart'ta sıfırlanmaz)
# ============================================================

FILTER_COMMANDS_PATCH = """
@bot.command(name="küfürfiltre", aliases=["kufurfiltre", "swearfilter"])
@commands.has_permissions(administrator=True)
async def kufur_filtre(ctx, durum: str):
    if durum.lower() in ("kapat", "off"):
        set_filter_status(ctx.guild.id, "kufur_filtre", False)
        embed = discord.Embed(
            title="🔓 Küfür Filtresi Kapatıldı",
            description="Artık küfür engellenmeyecek. (Kalıcı — restart'ta sıfırlanmaz)",
            color=discord.Color.red()
        )
    elif durum.lower() in ("aç", "ac", "on"):
        set_filter_status(ctx.guild.id, "kufur_filtre", True)
        embed = discord.Embed(
            title="🔒 Küfür Filtresi Açıldı",
            description="Küfürler tekrar engellenecek. (Kalıcı)",
            color=discord.Color.green()
        )
    else:
        return await ctx.send("❌ Kullanım: `!küfürfiltre aç` veya `!küfürfiltre kapat`")
    await ctx.send(embed=embed)
    await log_send(ctx.guild, embed)


@bot.command(name="reklamfiltre", aliases=["adfilter"])
@commands.has_permissions(administrator=True)
async def reklam_filtre(ctx, durum: str):
    if durum.lower() in ("kapat", "off"):
        set_filter_status(ctx.guild.id, "reklam_filtre", False)
        embed = discord.Embed(title="🔓 Reklam Filtresi Kapatıldı", color=discord.Color.red())
    elif durum.lower() in ("aç", "ac", "on"):
        set_filter_status(ctx.guild.id, "reklam_filtre", True)
        embed = discord.Embed(title="🔒 Reklam Filtresi Açıldı", color=discord.Color.green())
    else:
        return await ctx.send("❌ Kullanım: `!reklamfiltre aç` veya `!reklamfiltre kapat`")
    await ctx.send(embed=embed)
    await log_send(ctx.guild, embed)


@bot.command(name="filtredurum", aliases=["filterdurum", "filtrestatus"])
@commands.has_permissions(manage_messages=True)
async def filtre_durum(ctx):
    kufur_ac = get_filter_status(ctx.guild.id, "kufur_filtre")
    reklam_ac = get_filter_status(ctx.guild.id, "reklam_filtre")
    settings = get_settings(ctx.guild.id)
    bypass_id = settings.get("filter_bypass_role_id")
    bypass_str = f"<@&{bypass_id}>" if bypass_id else "Ayarlanmamış"

    embed = discord.Embed(title="🔍 Filtre Durumu", color=discord.Color.blurple())
    embed.add_field(name="🤬 Küfür Filtresi", value="🔒 Aktif" if kufur_ac else "🔓 Kapalı", inline=True)
    embed.add_field(name="📢 Reklam Filtresi", value="🔒 Aktif" if reklam_ac else "🔓 Kapalı", inline=True)
    embed.add_field(name="🛡️ Bypass Rolü", value=bypass_str, inline=False)
    embed.add_field(
        name="👑 Her Zaman Muaf",
        value="Sunucu kurucusu & Administrator yetkisine sahip herkes",
        inline=False
    )
    await ctx.send(embed=embed)
"""

# ============================================================
# YAMA 5 — /setup grubuna filtrebypass komutunu ekle
#          (setup_group.command satırlarının sonuna ekle)
# ============================================================

SETUP_BYPASS_PATCH = """
@setup_group.command(name="filtrebypass", description="Bu role sahip kişiler küfür/reklam filtresini atlar.")
@app_commands.describe(rol="Bypass rolü (None = kaldır)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_filtrebypass(interaction: discord.Interaction, rol: discord.Role = None):
    set_setting(interaction.guild.id, "filter_bypass_role_id", rol.id if rol else None)
    if rol:
        await interaction.response.send_message(
            f"✅ **{rol.mention}** rolüne sahip kişiler artık filtreyi atlar.\\n"
            f"ℹ️ Kurucu ve adminler zaten her zaman muaftır.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("✅ Bypass rolü kaldırıldı.", ephemeral=True)
"""

print("Yama paketi hazır. Aşağıdaki 5 yamayı main.py'ye uygula:")
print("YAMA 1: db_init() içindeki CREATE TABLE guild_settings")
print("YAMA 2: Yardımcı fonksiyonlar bölümüne ekle")
print("YAMA 3: on_message() filtre bloğunu değiştir")
print("YAMA 4: Filtre komutlarını değiştir")
print("YAMA 5: setup_group'a filtrebypass ekle")
