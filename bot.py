import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from discord import app_commands
import random
import os
import webserver

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# IDs and roles configuration
target_user_id = 1090165956363440148
channel_id = 1279210989388042251  # Channel for buttons
channel_id2 = 1278720207040548874
excluded_channel_id = 1278720873863581778  # Excluded channel
role_ids = [1278818590220353617, 1278818223462285437, 1278805002105782403]  # Roles that can press buttons

# Modal for application forms
class ApplicationModal(Modal):
    def __init__(self, title, fields, target_user_id, author_id):
        super().__init__(title=title)
        self.target_user_id = target_user_id
        self.author_id = author_id
        for label, placeholder, max_length in fields:
            self.add_item(TextInput(label=label, placeholder=placeholder, max_length=max_length))

    async def on_submit(self, interaction: discord.Interaction):
        form_data = f"<@{self.target_user_id}> Новая форма на {self.title} от <@{self.author_id}>\n"
        for item in self.children:
            form_data += f"**{item.label}:** {item.value}\n"
        user = bot.get_user(self.target_user_id)
        if user:
            await user.send(form_data)
        await interaction.response.send_message("Ваша заявка была отправлена!", ephemeral=True)

# Modal for response handling
class ResponseModal(Modal):
    def __init__(self, title, label, placeholder, question, user_id, embed, message, color, response_label):
        super().__init__(title=title)
        self.label = label
        self.question = question
        self.user_id = user_id
        self.embed = embed
        self.message = message
        self.color = color
        self.response_label = response_label
        self.add_item(TextInput(label=label, placeholder=placeholder, max_length=2000))

    async def on_submit(self, interaction: discord.Interaction):
        response_text = self.children[0].value
        self.embed.color = self.color
        self.embed.add_field(name=self.response_label, value=response_text, inline=False)
        await self.message.edit(embed=self.embed)
        await interaction.response.send_message("Ответ был обработан.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready and online.')

    # Sync commands
    try:
        await bot.tree.sync()
        print("Команды синхронизированы.")
    except Exception as e:
        print(f"Ошибка при синхронизации команд: {e}")

# Команда для отправки кнопок
@bot.tree.command(name='набор', description='Выберите действие')
async def button_command(interaction: discord.Interaction):
    view = View()
    button1 = Button(label="《📱》Пиар Менеджер", style=discord.ButtonStyle.primary)
    button2 = Button(label="《🍀》Модератор", style=discord.ButtonStyle.secondary)

    async def button1_callback(interaction):
        fields = [
            ("Имя", "Введите ваше имя", 100),
            ("Возраст", "Введите ваш возраст", 3),
            ("Актив в день", "Введите примерный актив", 100),
            ("Ознакомлены с правилами?", "Да/Нет", 3),
        ]
        modal = ApplicationModal("Заявка на Пиар Менеджера", fields, target_user_id, interaction.user.id)
        await interaction.response.send_modal(modal)

    async def button2_callback(interaction):
        fields = [
            ("Имя", "Введите ваше имя", 100),
            ("Возраст", "Введите ваш возраст", 3),
            ("Актив в день", "Введите примерный актив", 100),
            ("Ознакомлены с правилами?", "Да/Нет", 3),
            ("Готовы пройти обзвон?", "Да/Нет", 3),
        ]
        modal = ApplicationModal("Заявка на Модератора", fields, target_user_id, interaction.user.id)
        await interaction.response.send_modal(modal)

    button1.callback = button1_callback
    button2.callback = button2_callback

    view.add_item(button1)
    view.add_item(button2)

    await interaction.response.send_message("Выберите действие:", view=view)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return  # Игнорируем сообщения, отправленные самим ботом

    if message.channel.id == channel_id:
        await message.delete()

        embed = discord.Embed(title="Вопрос:", description=message.content, color=discord.Color.blurple())
        view = View()

        async def respond_callback(interaction):
            if any(role.id in role_ids for role in interaction.user.roles):
                modal = ResponseModal("Ответ на вопрос", "Ответ", "Введите ваш ответ...",
                                      message.content, message.author.id, embed,
                                      interaction.message, discord.Color.green(), "Ответ от администрации:")
                await interaction.response.send_modal(modal)
                # Отправляем сообщение с упоминанием пользователя
                await interaction.channel.send(f"{message.author.mention} Ваш вопрос был обработан.")
            else:
                await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)

        async def reject_callback(interaction):
            if any(role.id in role_ids for role in interaction.user.roles):
                modal = ResponseModal("Причина отказа", "Причина", "Введите причину отказа...",
                                      message.content, message.author.id, embed,
                                      interaction.message, discord.Color.red(),
                                      "Ответ от администрации: Вопрос отказан по причине:")
                await interaction.response.send_modal(modal)
                # Отправляем сообщение с упоминанием пользователя
                await interaction.channel.send(f"{message.author.mention} Ваш вопрос был отклонен.")
            else:
                await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)

        button1 = Button(label="Ответить", style=discord.ButtonStyle.success)
        button2 = Button(label="Отказать", style=discord.ButtonStyle.danger)

        button1.callback = respond_callback
        button2.callback = reject_callback

        view.add_item(button1)
        view.add_item(button2)

        await message.channel.send(embed=embed, view=view)

    elif message.channel.id == channel_id2:
        await message.delete()

        embed = discord.Embed(title="Идея:", description=message.content, color=discord.Color.blurple())
        view = View()

        async def respond_callback(interaction):
            if any(role.id in role_ids for role in interaction.user.roles):
                modal = ResponseModal("Ответ на идею", "Ответ", "Введите ваш ответ...",
                                      message.content, message.author.id, embed,
                                      interaction.message, discord.Color.green(), "Ответ от администрации:")
                await interaction.response.send_modal(modal)
                # Отправляем сообщение с упоминанием пользователя
                await interaction.channel.send(f"{message.author.mention} Ответ на вашу идею был обработан.")
            else:
                await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)

        button1 = Button(label="Ответить", style=discord.ButtonStyle.success)
        button1.callback = respond_callback
        view.add_item(button1)

        await message.channel.send(embed=embed, view=view)

    await bot.process_commands(message)  # Добавьте это, чтобы бот также обрабатывал команды


# Команда для создания формы жалобы
@bot.tree.command(name='жалобы', description='Создайте форму для подачи жалобы.')
async def complaints_command(interaction: discord.Interaction):
    view = View()
    complaint_button = Button(label="Жалобы", style=discord.ButtonStyle.primary)

    async def complaint_button_callback(interaction):
        fields = [
            ("Тип жалобы", "Жалоба на Сервер или игрока?", 45),
            ("ID", "ID сервера,ID нарушителя или ник нарушителя/овнера сервера", 45),
            ("Описание нарушения", "Опишите нарушение", 1000),
            ("Доказательства", "Ссылка на доказательства через imgur или cdn.discordapp и т.д", 500)
        ]
        modal = ApplicationModal("Жалоба", fields, target_user_id, interaction.user.id)
        await interaction.response.send_modal(modal)

    complaint_button.callback = complaint_button_callback
    view.add_item(complaint_button)

    await interaction.response.send_message("Нажмите на кнопку ниже, чтобы подать жалобу:", view=view)

@bot.tree.command(name='embed', description='Создайте простой embed с цветом, заголовком и описанием.')
async def embed_command(interaction: discord.Interaction, channel: discord.TextChannel, color: str, title: str, *, description: str):
    try:
        color = discord.Color(int(color.strip("#"), 16))
    except ValueError:
        await interaction.response.send_message("Некорректный формат цвета. Используйте шестнадцатеричный код цвета, например, #ff5733.", ephemeral=True)
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    await channel.send(embed=embed)
    await interaction.response.send_message(f"Сообщение отправлено в канал {channel.mention}", ephemeral=True)

@bot.tree.command(name='roll', description='Бросьте кость или выберите случайный вариант из списка.')
@app_commands.describe(input="Максимальное число или список вариантов через запятую")
async def roll_command(interaction: discord.Interaction, *, input: str):
    try:
        max_number = int(input)
        result = random.randint(1, max_number)
        await interaction.response.send_message(f"Выпало: {result} из {max_number}")
    except ValueError:
        options = [item.strip() for item in input.split(",")]
        result = random.choice(options)
        await interaction.response.send_message(f"Выбрано: {result}")




# Команда для очистки сообщений
@bot.tree.command(name='clear', description='Очистите указанное количество сообщений в текущем канале.')
@app_commands.describe(amount="Количество сообщений для удаления")
async def clear_command(interaction: discord.Interaction, amount: int):
    if amount < 1:
        await interaction.response.send_message("Количество должно быть больше 0.", ephemeral=True)
        return

    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Удалено {len(deleted)} сообщений.", ephemeral=True)

# Команда для определения первого пользователя
@bot.tree.command(name='первый', description='Определите первого пользователя из списка.')
@app_commands.describe(users="Список пользователей через запятую")
async def first_command(interaction: discord.Interaction, *, users: str):
    user_list = [user.strip() for user in users.split(",")]
    if user_list:
        await interaction.response.send_message(f"Первый: {user_list[0]}")
    else:
        await interaction.response.send_message("Список пользователей пуст.", ephemeral=True)

webserver.keep_alive()

bot_token = os.getenv('BOT_TOKEN')
bot.run(bot_token)