from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, upsert_user, delete_user, get_room
from keyboards import kb_role_choice, kb_no_room, kb_dom_main, kb_sub_main
from texts import (
    WELCOME_NEW, WELCOME_BACK,
    ROLE_CHOSEN_DOM, ROLE_CHOSEN_SUB,
    BTN_DOM, BTN_SUB,
    ERR_UNKNOWN,
)

router = Router()


class StartStates(StatesGroup):
    choosing_role = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    user = get_user(user_id)

    # Совсем новый пользователь
    if not user:
        await state.set_state(StartStates.choosing_role)
        await message.answer(WELCOME_NEW, reply_markup=kb_role_choice())
        return

    # Пользователь уже есть — показываем главное меню по роли
    role = user["role"]
    room_code = user["room_code"]

    if not room_code:
        # Роль есть, но комнаты нет
        if role == "dom":
            await message.answer(ROLE_CHOSEN_DOM, reply_markup=kb_no_room())
        else:
            await message.answer(ROLE_CHOSEN_SUB, reply_markup=kb_no_room())
        return

    # Есть и роль, и комната
    role_word = "Госпожа" if role == "dom" else "псина"
    text = WELCOME_BACK.format(role_word=role_word, room_code=room_code)
    kb = kb_dom_main() if role == "dom" else kb_sub_main()
    await message.answer(text, reply_markup=kb)


@router.message(StartStates.choosing_role, F.text.in_({BTN_DOM, BTN_SUB}))
async def choose_role(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    role = "dom" if message.text == BTN_DOM else "sub"

    upsert_user(user_id, username, role, None)
    await state.clear()

    if role == "dom":
        await message.answer(ROLE_CHOSEN_DOM, reply_markup=kb_no_room())
    else:
        await message.answer(ROLE_CHOSEN_SUB, reply_markup=kb_no_room())


@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """Сброс аккаунта: удаление из комнаты и из users."""
    user_id = message.from_user.id
    user = get_user(user_id)

    if user and user["room_code"]:
        # Если это доминант — комната удаляется (освобождает саба тоже)
        room = get_room(user["room_code"])
        if room and room["dominant_id"] == user_id:
            from database import delete_room
            delete_room(user["room_code"])

    delete_user(user_id)
    await state.clear()
    await message.answer(
        "🔄 Аккаунт сброшен. Нажми /start, чтобы начать заново.",
        reply_markup=None
    )


@router.message(F.text)
async def fallback_text(message: Message):
    """Если пользователь пишет что-то непонятное вне FSM."""
    await message.answer(ERR_UNKNOWN)
