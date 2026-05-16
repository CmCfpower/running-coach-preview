"""Running Telegram bot skeleton."""

from __future__ import annotations

import os
import re
import tempfile
import logging
from datetime import date
from pathlib import Path
from typing import Any, Awaitable, Callable

from running_coach.config import ProjectConfig
from running_coach.llm import LlmError, build_client_from_env
from running_coach.services.analysis import format_analysis, load_coaching_report
from running_coach.services.coach_review import (
    build_coach_review_context,
    format_coach_review_message,
    request_coach_plan_review,
    save_coach_review,
)
from running_coach.services.feedback import (
    append_training_feedback,
    classify_training_feedback,
    format_feedback_response,
    load_training_feedback,
    plan_feedback_notes,
)
from running_coach.services.plan_adjustments import (
    apply_adjustment_to_plan,
    build_plan_adjustment_draft,
    format_adjustment_for_display,
    format_plan_adjustment_notice,
    load_latest_adjustment_draft,
    mark_adjustment_applied,
    mark_adjustment_rejected,
    save_plan_adjustment_draft,
)
from running_coach.services.profile import format_profile_summary, load_profile
from running_coach.services.qa import answer_running_question, format_qa_response
from running_coach.services.training_plan import (
    find_day_plan,
    format_day_plan,
    format_week_plan,
    load_current_training_plan,
)
from running_coach.services.workout_extraction import ExtractionResult, extract_workout_from_images
from running_coach.services.workouts import (
    format_workout_analysis,
    import_workout_file,
    load_workout_for_date,
)
from running_coach.storage import ProjectStorage


LOGGER = logging.getLogger(__name__)
EXTRACT_JOB_PREFIX = "extract_workout:"


def build_running_bot(config: ProjectConfig, storage: ProjectStorage) -> Any:
    """Build python-telegram-bot Application.

    The import is local so the project can still compile before dependencies are
    installed.
    """

    token = os.environ.get(config.running_bot.env_token)
    if not token:
        raise RuntimeError(f"Missing Telegram token env var: {config.running_bot.env_token}")

    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Running Coach MVP\n\n"
            "Команды:\n"
            "/profile - профиль\n"
            "/today - план на сегодня\n"
            "/week - план до старта\n"
            "/analysis - анализ формы\n"
            "/adjustment - черновик коррекции плана\n"
            "/apply_adjustment - применить коррекцию\n\n"
            "/reject_adjustment - отклонить коррекцию\n\n"
            "Фото тренировки можно прислать прямо сюда."
        )

    async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        status = load_profile(storage)
        await update.message.reply_text(format_profile_summary(status))

    async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        plan = load_current_training_plan(storage)
        target_date = date.today()
        day_plan = find_day_plan(plan, target_date)
        actual_workout = load_workout_for_date(storage, target_date.isoformat())
        feedback_notes = plan_feedback_notes(load_training_feedback(storage), target_date)
        await update.message.reply_text(
            format_day_plan(day_plan, target_date, feedback_notes, actual_workout)
        )

    async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        plan = load_current_training_plan(storage)
        feedback_notes = plan_feedback_notes(load_training_feedback(storage))
        await update.message.reply_text(format_week_plan(plan, feedback_notes))

    async def adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        result = load_latest_adjustment_draft(storage)
        if result is None:
            await update.message.reply_text("Черновиков коррекции пока нет.")
            return
        draft, _ = result
        await update.message.reply_text(format_adjustment_for_display(draft))

    async def apply_adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        result = load_latest_adjustment_draft(storage)
        if result is None:
            await update.message.reply_text("Черновиков коррекции нет.")
            return
        draft, _ = result
        if draft.get("status") == "applied":
            await update.message.reply_text("Этот черновик уже применён.")
            return
        try:
            applied_count, skipped = apply_adjustment_to_plan(storage, draft)
        except Exception:
            LOGGER.exception("Failed to apply plan adjustment")
            await update.message.reply_text("Не удалось применить коррекцию. Ошибка записана в logs/running_bot.log.")
            return
        if applied_count == 0:
            skipped_text = ", ".join(skipped) if skipped else "нет подходящих дат"
            await update.message.reply_text(
                f"Ни одного изменения не применено. Пропущено: {skipped_text}\n"
                "Корректируются только следующие 1-3 дня."
            )
            return
        mark_adjustment_applied(storage, draft.get("target_date", ""))
        lines = [f"Применено изменений: {applied_count}"]
        if skipped:
            lines.append(f"Пропущено (вне диапазона): {', '.join(skipped)}")
        lines.append("Используй /today или /week чтобы проверить обновлённый план.")
        await update.message.reply_text("\n".join(lines))

    async def reject_adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        result = load_latest_adjustment_draft(storage)
        if result is None:
            await update.message.reply_text("Активных черновиков коррекции нет.")
            return
        draft, _ = result
        if not mark_adjustment_rejected(storage, draft.get("target_date", "")):
            await update.message.reply_text("Не удалось отклонить черновик. Возможно, он уже применён.")
            return
        await update.message.reply_text(
            "Черновик коррекции отклонён. Основной план не изменён."
        )

    async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            report = load_coaching_report(storage)
        except FileNotFoundError:
            await update.message.reply_text(
                "Анализ пока не найден. Сначала нужно собрать отчёт командой scripts/build_coaching_report.py."
            )
            return
        await update.message.reply_text(format_analysis(report))

    async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if not message or not message.text:
            return

        feedback = classify_training_feedback(message.text, current_date=date.today())
        if feedback is not None:
            feedback_date = str(feedback["date"])
            plan = load_current_training_plan(storage)
            day_plan = find_day_plan(plan, date.fromisoformat(feedback_date))
            actual_workout = load_workout_for_date(storage, feedback_date)
            feedback["context"] = {
                "planned_type": day_plan.get("type") if day_plan else None,
                "actual_workout_id": actual_workout.get("id") if actual_workout else None,
                "actual_distance_km": actual_workout.get("distance_km") if actual_workout else None,
                "actual_duration_sec": actual_workout.get("duration_sec") if actual_workout else None,
            }
            append_training_feedback(storage, feedback, source="telegram")
            await message.reply_text(format_feedback_response(feedback))
            if _needs_coach_review(feedback):
                await _send_coach_review(message.reply_text, storage, feedback_date, plan, day_plan, actual_workout, feedback)
            return

        await _send_qa_answer(message, storage, message.text)

    async def extract_job(context: ContextTypes.DEFAULT_TYPE) -> None:
        data = context.job.data or {}
        chat_id = data["chat_id"]
        workout_date = data["date"]
        raw_file = data["raw_file"]
        try:
            client = build_client_from_env(vision=True)
            extraction = extract_workout_from_images(
                storage,
                workout_date,
                client,
                prompt_path=storage.resolve("prompts", "workout_extract.md"),
                max_images=8,
                force=True,
                prefer_recent=True,
            )
        except (LlmError, ValueError, FileNotFoundError):
            LOGGER.exception("Failed to extract Telegram workout photo batch")
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "Файлы сохранены, но распознавание не удалось.\n"
                    f"Дата: {workout_date}\n"
                    "Ошибка записана в logs/running_bot.log."
                ),
            )
            return

        plan = load_current_training_plan(storage)
        actual_date = extraction.date
        day_plan = find_day_plan(plan, date.fromisoformat(actual_date))
        actual_workout = load_workout_for_date(storage, actual_date)
        await context.bot.send_message(
            chat_id=chat_id,
            text=_format_photo_import_result(workout_date, raw_file, extraction, actual_workout, day_plan),
        )
        if _detect_plan_deviation(day_plan, actual_workout) and not _coach_review_exists(
            storage, actual_date, actual_workout
        ):
            async def _send(text: str) -> None:
                await context.bot.send_message(chat_id=chat_id, text=text)

            await _send_coach_review(_send, storage, actual_date, plan, day_plan, actual_workout)

    async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if not message or not message.photo:
            return

        try:
            target_date = _date_from_caption(message.caption) or date.today().isoformat()
            largest_photo = message.photo[-1]
            telegram_file = await context.bot.get_file(largest_photo.file_id)
            suffix = Path(telegram_file.file_path or "photo.jpg").suffix or ".jpg"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp_path = Path(temp.name)

            try:
                await telegram_file.download_to_drive(custom_path=temp_path)
                result = import_workout_file(
                    storage,
                    target_date,
                    temp_path,
                    source="telegram",
                    caption=message.caption,
                )
            finally:
                temp_path.unlink(missing_ok=True)
        except Exception:
            LOGGER.exception("Failed to save Telegram workout photo")
            await message.reply_text("Не удалось сохранить фото тренировки. Ошибка записана в logs/running_bot.log.")
            return

        if result.duplicate:
            await message.reply_text("Такой файл уже есть. Повторно не сохраняю.")
            plan = load_current_training_plan(storage)
            day_plan = find_day_plan(plan, date.fromisoformat(result.date))
            actual_workout = load_workout_for_date(storage, result.date)
            if actual_workout:
                await message.reply_text(format_workout_analysis(actual_workout, day_plan))
            if _detect_plan_deviation(day_plan, actual_workout) and not _coach_review_exists(
                storage, result.date, actual_workout
            ):
                await _send_coach_review(
                    message.reply_text,
                    storage,
                    result.date,
                    plan,
                    day_plan,
                    actual_workout,
                )
            return

        _schedule_extraction(context, message.chat_id, result.date, result.raw_file)

    builder = Application.builder().token(token)
    proxy_url = os.environ.get("TELEGRAM_PROXY_URL")
    if proxy_url:
        builder = builder.proxy(proxy_url).get_updates_proxy(proxy_url)

    app = builder.build()
    app.bot_data["extract_job"] = extract_job
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("analysis", analysis))
    app.add_handler(CommandHandler("adjustment", adjustment))
    app.add_handler(CommandHandler("apply_adjustment", apply_adjustment))
    app.add_handler(CommandHandler("reject_adjustment", reject_adjustment))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    return app


async def _send_qa_answer(
    message: Any,
    storage: ProjectStorage,
    question: str,
) -> None:
    try:
        client = build_client_from_env(vision=False, timeout_sec=60)
        result = answer_running_question(
            storage,
            client,
            question,
            prompt_path=storage.resolve("prompts", "running_qa.md"),
        )
    except (LlmError, FileNotFoundError, ValueError):
        LOGGER.exception("QA answer failed")
        await message.reply_text(
            "Сейчас не могу ответить — LLM недоступен. Попробуй позже."
        )
        return
    await message.reply_text(format_qa_response(result))


async def _send_coach_review(
    send: Callable[[str], Awaitable[Any]],
    storage: ProjectStorage,
    feedback_date: str,
    plan: dict[str, Any],
    day_plan: dict[str, Any] | None,
    actual_workout: dict[str, Any] | None,
    feedback: dict[str, Any] | None = None,
) -> None:
    await send("Вижу расхождение/важный фидбэк. Отдаю тренеру на быстрый пересмотр плана...")
    try:
        client = build_client_from_env(vision=False, timeout_sec=90)
        context = build_coach_review_context(
            storage,
            target_date=feedback_date,
            plan=plan,
            day_plan=day_plan,
            actual_workout=actual_workout,
            feedback=feedback,
        )
        review = request_coach_plan_review(
            storage,
            client,
            context=context,
            prompt_path=storage.resolve("prompts", "coach_plan_review.md"),
        )
        saved_path = save_coach_review(storage, feedback_date, review)
        adjustment_path = _save_plan_adjustment_if_needed(
            storage,
            feedback_date,
            review,
            plan,
            day_plan,
            actual_workout,
            feedback,
            saved_path,
        )
    except (LlmError, FileNotFoundError, ValueError):
        LOGGER.exception("Coach plan review failed")
        await send(
            "Тренер сейчас не смог пересмотреть план через LLM. Фидбэк сохранён, вернёмся к корректировке позже."
        )
        return

    await send(format_coach_review_message(review, saved_path))
    notice = format_plan_adjustment_notice(adjustment_path)
    if notice:
        await send(notice)


def _save_plan_adjustment_if_needed(
    storage: ProjectStorage,
    feedback_date: str,
    review: dict[str, Any],
    plan: dict[str, Any],
    day_plan: dict[str, Any] | None,
    actual_workout: dict[str, Any] | None,
    feedback: dict[str, Any] | None,
    review_path: str,
) -> str | None:
    draft = build_plan_adjustment_draft(
        target_date=feedback_date,
        review=review,
        plan=plan,
        day_plan=day_plan,
        actual_workout=actual_workout,
        feedback=feedback,
        review_path=review_path,
    )
    if draft is None:
        return None
    return save_plan_adjustment_draft(storage, feedback_date, draft)


def _needs_coach_review(feedback: dict[str, Any]) -> bool:
    context = feedback.get("context") or {}
    if feedback.get("requires_plan_review"):
        return True
    if context.get("planned_type") == "rest" and context.get("actual_workout_id"):
        return True
    return False


def _detect_plan_deviation(
    day_plan: dict[str, Any] | None,
    actual_workout: dict[str, Any] | None,
) -> bool:
    if not actual_workout:
        return False

    if day_plan is None:
        return True

    planned_type = day_plan.get("type", "unknown")
    actual_distance = _number(actual_workout.get("distance_km"))
    actual_duration = _number(actual_workout.get("duration_sec"))

    if planned_type == "rest":
        return bool((actual_distance and actual_distance >= 1.0) or (actual_duration and actual_duration >= 600))

    planned_distance = _number(day_plan.get("distance_km"))
    planned_duration = _number(day_plan.get("duration_min"))
    planned_duration_range = _duration_range_from_instructions(day_plan.get("instructions"))

    if planned_distance and actual_distance:
        diff_ratio = abs(actual_distance - planned_distance) / planned_distance
        if diff_ratio >= 0.35:
            return True

    if planned_duration and actual_duration:
        actual_minutes = actual_duration / 60
        diff_ratio = abs(actual_minutes - planned_duration) / planned_duration
        if diff_ratio >= 0.35:
            return True

    if planned_duration_range and actual_duration:
        actual_minutes = actual_duration / 60
        low, high = planned_duration_range
        if actual_minutes < low * 0.65 or actual_minutes > high * 1.10:
            return True

    if planned_type in {"tempo", "intervals", "long_run"} and actual_distance and actual_distance < 2:
        return True

    return False


def _coach_review_exists(
    storage: ProjectStorage,
    target_date: str,
    actual_workout: dict[str, Any] | None = None,
) -> bool:
    review_path = storage.resolve("data", "coach_reviews", f"{target_date}.json")
    if review_path.exists():
        try:
            review = storage.read_json("data", "coach_reviews", f"{target_date}.json")
        except (OSError, ValueError):
            return True
        if not review.get("invalidated"):
            return True

    adjustment_path = storage.resolve("data", "plan_adjustments", f"{target_date}.json")
    if not adjustment_path.exists():
        return False

    try:
        draft = storage.read_json("data", "plan_adjustments", f"{target_date}.json")
    except (OSError, ValueError):
        return True

    if draft.get("status") in {"invalidated", "superseded"}:
        return False
    draft_workout_id = (draft.get("context") or {}).get("actual_workout_id")
    current_workout_id = actual_workout.get("id") if actual_workout else None
    return bool(draft_workout_id and current_workout_id and draft_workout_id == current_workout_id)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _duration_range_from_instructions(instructions: Any) -> tuple[float, float] | None:
    if not instructions:
        return None
    text = str(instructions).lower()
    match = re.search(r"(\d{1,3})\s*[-–—]\s*(\d{1,3})", text)
    if match:
        low = float(match.group(1))
        high = float(match.group(2))
        return (min(low, high), max(low, high))

    match = re.search(r"(\d{1,3})\s*(?:мин|минут|min)", text)
    if match:
        value = float(match.group(1))
        return (value, value)
    return None


def _date_from_args(args: list[str]) -> str:
    if not args:
        return date.today().isoformat()
    date.fromisoformat(args[0])
    return args[0]


def _date_from_caption(caption: str | None) -> str | None:
    if not caption:
        return None

    patterns = (
        re.compile(r"(?P<year>20\d{2})-(?P<month>\d{2})-(?P<day>\d{2})"),
        re.compile(r"(?P<day>\d{2})[._](?P<month>\d{2})[._](?P<year>\d{2,4})"),
    )
    for pattern in patterns:
        match = pattern.search(caption)
        if match is None:
            continue

        year = int(match.group("year"))
        if year < 100:
            year += 2000
        month = int(match.group("month"))
        day = int(match.group("day"))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    return None


def _format_photo_import_result(
    workout_date: str,
    raw_file: str,
    extraction: ExtractionResult,
    actual_workout: dict[str, Any] | None = None,
    day_plan: dict[str, Any] | None = None,
) -> str:
    status = "обновлён" if extraction.updated else "уже был распознан"
    lines = [
        "Тренировка распознана",
        f"Получил и прочитал: {extraction.images_read} фото",
        f"Дата: {extraction.date}",
        f"Файл: {raw_file}",
        f"parsed.json: {status}",
        f"Уверенность: {extraction.confidence:.2f}",
    ]
    if extraction.date != workout_date:
        lines.append(f"Дата на скриншоте отличается от даты получения. Перенёс с {workout_date} на {extraction.date}.")
    if actual_workout:
        lines.extend(["", format_workout_analysis(actual_workout, day_plan)])
    return "\n".join(lines)


def _schedule_extraction(context: Any, chat_id: int, workout_date: str, raw_file: str) -> None:
    job_name = f"{EXTRACT_JOB_PREFIX}{chat_id}:{workout_date}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    context.job_queue.run_once(
        context.application.bot_data["extract_job"],
        when=8,
        name=job_name,
        data={"chat_id": chat_id, "date": workout_date, "raw_file": raw_file},
    )
