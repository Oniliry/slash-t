import { useCallback, useEffect, useState } from "react";

import {
  getCushionState,
  setCushionGoal,
  topUpCushion,
  withdrawCushion,
} from "../../../shared/api/cushion.ts";
import { formatCushionAmount } from "../lib/cushionFormat.js";
import "./CushionSummary.css";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

function buildDonut(balance, target) {
  const circumference = 2 * Math.PI * 45;
  const share = target > 0 ? Math.min(balance / target, 1) : 0;
  const length = share * circumference;

  return {
    circumference,
    dasharray: `${length} ${circumference - length}`,
  };
}

function CushionSummary() {
  const [state, setState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [amount, setAmount] = useState("");
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState("");

  const [isGoalEditing, setIsGoalEditing] = useState(false);
  const [goalAmount, setGoalAmount] = useState("");
  const [goalMonths, setGoalMonths] = useState(6);

  const loadState = useCallback(async () => {
    const response = await getCushionState();

    if (!response.error && response.data) {
      setState(response.data);
      setError("");
    } else {
      setError(response.message ?? "Не удалось загрузить подушку.");
    }

    setIsLoading(false);
  }, []);

  useEffect(() => {
    loadState();
  }, [loadState]);

  async function handleOperation(kind) {
    const value = Number(amount.replace(",", "."));
    if (!Number.isFinite(value) || value <= 0) {
      setActionError("Введите сумму больше нуля.");
      return;
    }

    setIsSubmitting(true);
    setActionError("");

    const request = kind === "topup" ? topUpCushion : withdrawCushion;
    const response = await request({ amount: value, comment: comment || null });

    if (!response.error && response.data) {
      setState(response.data);
      setAmount("");
      setComment("");
      window.dispatchEvent(new Event("slash-t:cushion-updated"));
    } else {
      setActionError(response.message ?? "Не удалось выполнить операцию.");
    }

    setIsSubmitting(false);
  }

  async function handleGoalSave(event) {
    event.preventDefault();

    const target = Number(goalAmount.replace(",", "."));
    if (!Number.isFinite(target) || target <= 0) {
      setActionError("Введите целевую сумму больше нуля.");
      return;
    }

    setIsSubmitting(true);
    setActionError("");

    const response = await setCushionGoal({
      target_amount: target,
      months: goalMonths,
    });

    if (!response.error && response.data) {
      setState(response.data);
      setIsGoalEditing(false);
      window.dispatchEvent(new Event("slash-t:cushion-updated"));
    } else {
      setActionError(response.message ?? "Не удалось сохранить цель.");
    }

    setIsSubmitting(false);
  }

  if (isLoading) {
    return (
      <article className="card cushion-summary">
        <span className="card__eyebrow">Текущие сбережения</span>
        <p className="cushion-summary__hint">Загружаем...</p>
      </article>
    );
  }

  if (error) {
    return (
      <article className="card cushion-summary">
        <span className="card__eyebrow">Текущие сбережения</span>
        <p className="cushion-summary__hint">{error}</p>
      </article>
    );
  }

  const balance = Number(state.balance);
  const goal = state.goal;
  const progressPercent = goal ? goal.progress_percent : 0;
  const donut = buildDonut(balance, goal ? Number(goal.target_amount) : 0);

  return (
    <article className="card cushion-summary">
      <span className="card__eyebrow">Текущие сбережения</span>

      <div className="cushion-summary__body">
        <div className="cushion-summary__figures">
          <div className="cushion-summary__figure">
            <strong className="stat__value">{formatCushionAmount(balance)}</strong>
            <span className="stat__caption">текущий размер подушки</span>
          </div>

          <div className="cushion-summary__figure">
            <strong className="stat__value">{formatCushionAmount(state.monthly_expenses)}</strong>
            <span className="stat__caption">средние расходы семьи в месяц</span>
          </div>
        </div>

        {goal ? (
          <svg
            className="cushion-summary__donut"
            viewBox="0 0 120 120"
            role="img"
            aria-label={`Накоплено ${progressPercent}% цели`}
          >
            <circle className="cushion-summary__track" cx="60" cy="60" r="45" />
            <circle
              className="cushion-summary__value-arc"
              cx="60"
              cy="60"
              r="45"
              strokeDasharray={donut.dasharray}
              transform="rotate(-90 60 60)"
            />
            <text x="60" y="56" className="cushion-summary__percent" textAnchor="middle">
              {progressPercent}%
            </text>
            <text x="60" y="72" className="cushion-summary__percent-caption" textAnchor="middle">
              накоплено
            </text>
          </svg>
        ) : (
          <button
            type="button"
            className="cushion-summary__goal-button"
            onClick={() => {
              setIsGoalEditing(true);
              setGoalAmount(state.monthly_expenses > 0 ? String(Math.round(Number(state.monthly_expenses) * 6)) : "");
            }}
          >
            Цель: 300 000 ₽ — 6 месяцев расходов
            <span>Установить свою цель</span>
          </button>
        )}
      </div>

      {goal && (
        <div className="cushion-summary__goal-line">
          <span>
            Цель: {currencyFormatter.format(Number(goal.target_amount))} ₽ —{" "}
            {goal.months} мес. расходов
          </span>
          <button
            type="button"
            className="cushion-summary__goal-edit"
            onClick={() => {
              setIsGoalEditing(true);
              setGoalAmount(String(Math.round(Number(goal.target_amount))));
              setGoalMonths(goal.months);
            }}
          >
            Изменить
          </button>
        </div>
      )}

      {isGoalEditing && (
        <form className="cushion-summary__goal-form" onSubmit={handleGoalSave}>
          <label className="cushion-summary__field">
            <span>Целевая сумма, ₽</span>
            <input
              inputMode="decimal"
              placeholder="300000"
              value={goalAmount}
              onChange={(event) => setGoalAmount(event.target.value)}
            />
          </label>
          <label className="cushion-summary__field">
            <span>Месяцев расходов</span>
            <input
              inputMode="numeric"
              min="1"
              max="60"
              value={goalMonths}
              onChange={(event) => setGoalMonths(Number(event.target.value) || 1)}
            />
          </label>
          <div className="cushion-summary__actions">
            <button
              type="submit"
              className="cushion-summary__submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Сохраняем..." : "Сохранить цель"}
            </button>
            <button
              type="button"
              className="cushion-summary__secondary"
              onClick={() => setIsGoalEditing(false)}
            >
              Отмена
            </button>
          </div>
        </form>
      )}

      <form
        className="cushion-summary__operation"
        onSubmit={(event) => event.preventDefault()}
      >
        <input
          className="cushion-summary__amount"
          inputMode="decimal"
          placeholder="Сумма, ₽"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />
        <input
          className="cushion-summary__comment"
          placeholder="Комментарий (необязательно)"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
        />
        <div className="cushion-summary__actions">
          <button
            type="button"
            className="cushion-summary__submit"
            disabled={isSubmitting}
            onClick={() => handleOperation("topup")}
          >
            Пополнить
          </button>
          <button
            type="button"
            className="cushion-summary__secondary"
            disabled={isSubmitting}
            onClick={() => handleOperation("withdraw")}
          >
            Списать
          </button>
        </div>
      </form>

      {actionError && <p className="cushion-summary__error">{actionError}</p>}
    </article>
  );
}

export default CushionSummary;
