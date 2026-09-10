from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from texts import (
    BTN_DOM, BTN_SUB,
    BTN_CREATE_ROOM, BTN_JOIN_ROOM, BTN_MY_ROOM,
    BTN_MY_TASKS, BTN_CREATE_TASK, BTN_PENDING_REPORTS,
    BTN_SEND_REPORT,
    BTN_BACK, BTN_CANCEL,
    BTN_TYPE_ONE_TIME, BTN_TYPE_DAILY,
)


# ---------- Reply-клавиатуры (постоянные) ----------

def kb_role_choice() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_DOM), KeyboardButton(text=BTN_SUB)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_no_room() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CREATE_ROOM)],
            [KeyboardButton(text=BTN_JOIN_ROOM)],
        ],
        resize_keyboard=True
    )


def kb_dom_main() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_MY_TASKS), KeyboardButton(text=BTN_CREATE_TASK)],
            [KeyboardButton(text=BTN_PENDING_REPORTS)],
            [KeyboardButton(text=BTN_MY_ROOM), KeyboardButton(text="🚪 Выйти из комнаты")],
        ],
        resize_keyboard=True
    )


def kb_sub_main() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_MY_TASKS)],
            [KeyboardButton(text=BTN_SEND_REPORT)],
            [KeyboardButton(text=BTN_MY_ROOM), KeyboardButton(text="🚪 Выйти из комнаты")],
        ],
        resize_keyboard=True
    )


def kb_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True
    )


# ---------- Inline-клавиатуры ----------

def kb_task_types() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_TYPE_ONE_TIME, callback_data="task_type:one_time")],
        [InlineKeyboardButton(text=BTN_TYPE_DAILY, callback_data="task_type:daily")],
        [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel")],
    ])


def kb_task_list_dom(tasks: list) -> InlineKeyboardMarkup:
    """Список задач для доминанта: удалить."""
    rows = []
    for t in tasks:
        rows.append([
            InlineKeyboardButton(
                text=f"🗑 {t['title']}",
                callback_data=f"task_delete:{t['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_task_delete_confirm(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"task_delete_yes:{task_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="back_to_main"),
        ]
    ])


def kb_task_list_sub(tasks: list) -> InlineKeyboardMarkup:
    """Список задач для саба: выбрать для отчёта."""
    rows = []
    for t in tasks:
        rows.append([
            InlineKeyboardButton(
                text=f"📸 {t['title']}",
                callback_data=f"report_task:{t['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_report_review(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"report_ok:{report_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"report_no:{report_id}"),
        ]
    ])


def kb_back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_main")]
    ])
