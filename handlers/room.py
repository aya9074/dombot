import random

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH
from database import (
    get_user, upsert_user, get_room,
    create_room, set_sub_to_room, delete_room
)
from keyboards import kb_no_room, kb_dom_main, kb_sub_main, kb_cancel
from texts import (
    ROOM_CREATED, ROOM_JOINED, ROOM_NOT_FOUND,
    ROOM_ALREADY_HAS_SUB, ROOM_DOM_CANNOT_JOIN, ROOM_SUB_CANNOT_CREATE,
    BTN_CREATE_ROOM, BTN_JOIN_ROOM, BTN_CANCEL,
    ERR_ONLY_DOM, ERR_ONLY_SUB, ERR_UNKNOWN, BTN_MY_ROOM,
)

router = Router()


class RoomStates(StatesGroup):
    entering_code = State()


def generate_room_code() -> str:
    while True:
        code = "".join(random.choices(ROOM_CODE_ALPHABET, k=ROOM_CODE_LENGTH))
        if not get_room(code):
            return code


# ---------- СОЗДАНИЕ КОМНАТЫ (только доминант) ----------

@router.message(F.text == BTN_CREATE_ROOM)
async def create_room_handler(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.answer("Сначала нажми /start")
        return

    if user["role"] != "dom":
        await message.answer(ERR_ONLY_DOM)
        return

    if user["room_code"]:
        await message.answer(f"У тебя уже есть комната: <code>{user['room_code']}</code>")
        return

    code = generate_room_code()
    create_room(code, user_id)
    upsert_user(user_id, user["username"], "dom", code)

    await message.answer(
        ROOM_CREATED.format(code=code),
        reply_markup=kb_dom_main()
    )


# ---------- ВХОД ПО КОДУ (только саб) ----------

@router.message(F.text == BTN_JOIN_ROOM)
async def join_room_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.answer("Сначала нажми /start")
        return

    if user["role"] != "sub":
        await message.answer(ERR_ONLY_SUB)
        return

    if user["room_code"]:
        await message.answer(f"Ты уже в комнате: <code>{user['room_code']}</code>")
        return

    await state.set_state(RoomStates.entering_code)
    await message.answer(
        "🔑 Введи код комнаты, который дала Госпожа:",
        reply_markup=kb_cancel()
    )


@router.message(RoomStates.entering_code, F.text == BTN_CANCEL)
async def join_room_cancel(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    await message.answer("Отменено.", reply_markup=kb_no_room() if user else None)


@router.message(RoomStates.entering_code, F.text)
async def join_room_code(message: Message, state: FSMContext):
    user_id = message.from_user.id
    code = message.text.strip().upper()

    room = get_room(code)
    if not room:
        await message.answer(ROOM_NOT_FOUND)
        return

    if room["sub_id"] is not None:
        await message.answer(ROOM_ALREADY_HAS_SUB)
        await state.clear()
        return

    # Привязываем саба
    set_sub_to_room(code, user_id)
    user = get_user(user_id)
    upsert_user(user_id, user["username"], "sub", code)
    await state.clear()

    await message.answer(
        ROOM_JOINED.format(code=code),
        reply_markup=kb_sub_main()
    )

    # Уведомляем доминанта
    try:
        await message.bot.send_message(
            room["dominant_id"],
            f"🔔 Твой саб присоединился к комнате <code>{code}</code>.\n"
            f"Юзернейм: @{message.from_user.username or '—'}"
        )
    except Exception:
        pass


# ---------- МОЯ КОМНАТА ----------

@router.message(F.text == BTN_MY_ROOM)
async def my_room(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user or not user["room_code"]:
        await message.answer("У тебя пока нет комнаты.")
        return

    room = get_room(user["room_code"])
    if not room:
        await message.answer("Комната не найдена. Возможно, она удалена.")
        return

    code = user["room_code"]
    role = user["role"]

    if role == "dom":
        sub_status = "подключён" if room["sub_id"] else "ещё не подключился"
        text = (
            f"🏠 <b>Твоя комната</b>\n\n"
            f"Код: <code>{code}</code>\n"
            f"Сабмиссив: {sub_status}"
        )
    else:
        text = (
            f"🏠 <b>Твоя комната</b>\n\n"
            f"Код: <code>{code}</code>\n"
            f"Доминант: подключён"
        )

    await message.answer(text)


# ---------- ВЫХОД ИЗ КОМНАТЫ ----------

@router.message(F.text == "🚪 Выйти из комнаты")
async def leave_room(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user or not user["room_code"]:
        await message.answer("Ты и так не в комнате.")
        return

    code = user["room_code"]
    room = get_room(code)

    if user["role"] == "dom" and room:
        delete_room(code)
        await message.answer(
            "🚪 Комната удалена. Саб освобождён.",
            reply_markup=kb_no_room()
        )
    else:
        # Саб выходит — отвязываем от комнаты
        if room:
            from database import get_conn
            conn = get_conn()
            conn.execute("UPDATE rooms SET sub_id = NULL WHERE code = ?", (code,))
            conn.commit()
            conn.close()

        upsert_user(user_id, user["username"], user["role"], None)
        await message.answer(
            "🚪 Ты вышел из комнаты.",
            reply_markup=kb_no_room()
        )

        # Уведомляем доминанта
        if room:
            try:
                await message.bot.send_message(
                    room["dominant_id"],
                    f"⚠️ Твой саб покинул комнату <code>{code}</code>."
                )
            except Exception:
                pass
