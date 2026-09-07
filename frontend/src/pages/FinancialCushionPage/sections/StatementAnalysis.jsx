import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "../../../app/providers/AuthProvider.jsx";
import { getCushionState } from "../../../shared/api/cushion.ts";
import {
  getLastAnalysis,
  getFamilySummary,
  recalculateStatement,
  resetLastAnalysis,
  uploadStatement,
} from "../../../shared/api/financialCushion.ts";
import { formatStatementAmount } from "../lib/cushionFormat.js";
import "./StatementAnalysis.css";

function buildDonut(value, target) {
  const circumference = 2 * Math.PI * 45;
  const share = target > 0 ? Math.min(value / target, 1) : 0;
  const length = share * circumference;

  return {
    circumference,
    dasharray: `${length} ${circumference - length}`,
  };
}

function StatementAnalysis() {
  const { user } = useAuth();

  const [analysis, setAnalysis] = useState(null);
  const [result, setResult] = useState(null);
  const [cushionState, setCushionState] = useState(null);
  const [rating, setRating] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [error, setError] = useState("");
  const [isDirty, setIsDirty] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const [expandedGroups, setExpandedGroups] = useState(() => new Set());

  const loadRating = useCallback(async () => {
    const response = await getFamilySummary();
    if (!response.error && response.data) {
      setRating(response.data);
    }
  }, []);

  const computeInitialResult = useCallback(async (loadedAnalysis) => {
    const response = await recalculateStatement({
      months_analyzed: loadedAnalysis.months_analyzed,
      full_months: loadedAnalysis.full_months,
      excluded_months: loadedAnalysis.excluded_months,
      transactions: loadedAnalysis.transactions,
    });
    if (!response.error && response.data) {
      setResult(response.data);
    }
  }, []);

  useEffect(() => {
    async function restore() {
      const [stateResponse, lastResponse] = await Promise.all([
        getCushionState(),
        getLastAnalysis(),
      ]);

      if (!stateResponse.error && stateResponse.data) {
        setCushionState(stateResponse.data);
      }

      if (!lastResponse.error && lastResponse.data) {
        setAnalysis(lastResponse.data);
        await computeInitialResult(lastResponse.data);
      } else if (lastResponse.error) {
        setError(lastResponse.message ?? "Не удалось загрузить анализ.");
      }

      await loadRating();
      setIsLoading(false);
    }

    restore();
  }, [computeInitialResult, loadRating]);

  async function handleFile(file) {
    if (!file) {
      return;
    }
    if (file.type && file.type !== "application/pdf") {
      setError("Нужен файл в формате PDF.");
      return;
    }

    setIsUploading(true);
    setError("");

    const response = await uploadStatement(file);

    if (!response.error && response.data) {
      setAnalysis(response.data);
      setResult(null);
      setIsDirty(false);
      setExpandedGroups(new Set());
      await Promise.all([computeInitialResult(response.data), loadRating()]);
    } else {
      setError(response.message ?? "Не удалось обработать выписку.");
    }

    setIsUploading(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files?.[0]);
  }

  function handleDragOver(event) {
    event.preventDefault();
    setIsDragging(true);
  }

  function patchTransaction(txId, patch) {
    setAnalysis((current) => ({
      ...current,
      transactions: current.transactions.map((tx) =>
        tx.tx_id === txId ? { ...tx, ...patch } : tx,
      ),
    }));
    setIsDirty(true);
  }

  function toggleTransaction(txId, isActive) {
    patchTransaction(txId, { is_active: isActive });
  }

  function toggleGroup(groupName, isActive) {
    setAnalysis((current) => ({
      ...current,
      transactions: current.transactions.map((tx) =>
        !tx.is_transfer && tx.group === groupName
          ? { ...tx, is_active: isActive }
          : tx,
      ),
    }));
    setIsDirty(true);
  }

  function toggleGroupExpanded(groupName) {
    setExpandedGroups((current) => {
      const next = new Set(current);
      if (next.has(groupName)) {
        next.delete(groupName);
      } else {
        next.add(groupName);
      }
      return next;
    });
  }

  function patchTransfers(counterparty, patch) {
    setAnalysis((current) => ({
      ...current,
      transactions: current.transactions.map((tx) =>
        tx.is_transfer && tx.counterparty === counterparty
          ? { ...tx, ...patch }
          : tx,
      ),
    }));
    setIsDirty(true);
  }

  async function handleRecalculate() {
    if (!analysis) {
      return;
    }

    setIsRecalculating(true);
    setError("");

    const response = await recalculateStatement({
      months_analyzed: analysis.months_analyzed,
      full_months: analysis.full_months,
      excluded_months: analysis.excluded_months,
      transactions: analysis.transactions,
    });

    if (!response.error && response.data) {
      setResult(response.data);
      setIsDirty(false);
      await loadRating();
    } else {
      setError(response.message ?? "Не удалось пересчитать подушку.");
    }

    setIsRecalculating(false);
  }

  async function handleReset() {
    const response = await resetLastAnalysis();
    if (!response.error) {
      setAnalysis(null);
      setResult(null);
      setIsDirty(false);
      setExpandedGroups(new Set());
      setError("");
      await loadRating();
    } else {
      setError(response.message ?? "Не удалось сбросить анализ.");
    }
  }

  const groups = result?.groups ?? [];
  const excludedGroups = result?.excluded_groups ?? [];

  const cushionTotal = useMemo(() => {
    if (result) {
      return Number(result.cushion_total);
    }
    if (!analysis) {
      return 0;
    }
    const activeSum = analysis.transactions
      .filter((tx) => tx.is_active)
      .reduce((sum, tx) => sum + tx.amount, 0);
    return activeSum / Math.max(analysis.months_analyzed, 1);
  }, [analysis, result]);

  const monthlyExpenses = cushionState
    ? Number(cushionState.monthly_expenses)
    : 0;
  const coveredMonths =
    monthlyExpenses > 0 ? Math.floor(cushionTotal / monthlyExpenses) : null;

  const goalTarget = cushionState?.goal
    ? Number(cushionState.goal.target_amount)
    : monthlyExpenses * 6;
  const donut = buildDonut(cushionTotal, goalTarget);
  const goalPercent =
    goalTarget > 0 ? Math.min(Math.round((cushionTotal / goalTarget) * 100), 100) : 0;

  if (isLoading) {
    return (
      <article className="card statement-analysis">
        <span className="card__eyebrow">Анализ выписки</span>
        <p className="statement-analysis__hint">Загружаем...</p>
      </article>
    );
  }

  if (!analysis) {
    return (
      <article className="card statement-analysis">
        <span className="card__eyebrow">Анализ выписки</span>
        <h2 className="section-heading__hint">
          Рассчитайте финансовую подушку по своей банковской выписке
        </h2>

        <div
          className={`statement-analysis__dropzone${
            isDragging ? " statement-analysis__dropzone--active" : ""
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={() => setIsDragging(false)}
        >
          {isUploading ? (
            <div className="statement-analysis__loader">
              <span className="statement-analysis__spinner" aria-hidden="true" />
              <span>Анализируем выписку...</span>
            </div>
          ) : (
            <>
              <p className="statement-analysis__dropzone-text">
                Перетащите PDF-выписку сюда или
              </p>
              <label className="statement-analysis__file-button">
                Выбрать файл
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => {
                    handleFile(event.target.files?.[0]);
                    event.target.value = "";
                  }}
                />
              </label>
            </>
          )}
        </div>

        <p className="statement-analysis__hint">
          Загрузите выписку из банка в формате PDF для расчета финансовой
          подушки. Результат будет доступен только вам и отразится в рейтинге
          семьи.
        </p>

        {error && <p className="statement-analysis__error">{error}</p>}
      </article>
    );
  }

  return (
    <div className="statement-analysis-results">
      <article className="card statement-analysis">
        <span className="card__eyebrow">Анализ выписки</span>

        <div className="statement-analysis__body">
          <div className="statement-analysis__figures">
            <div className="statement-analysis__figure">
              <strong className="stat__value">
                {formatStatementAmount(cushionTotal)}
              </strong>
              <span className="stat__caption">
                расчёт по {analysis.months_analyzed} полн. мес. (
                {analysis.full_months.join(", ")})
              </span>
            </div>
            <div className="statement-analysis__figure">
              {coveredMonths !== null ? (
                <span className="statement-analysis__status">
                  Подушка покрывает ~{coveredMonths}{" "}
                  {coveredMonths === 1 ? "месяц" : "мес."} расходов
                </span>
              ) : (
                <span className="statement-analysis__status">
                  Добавьте расходы на главной, чтобы оценить срок покрытия
                </span>
              )}
            </div>
          </div>

          <svg
            className="statement-analysis__donut"
            viewBox="0 0 120 120"
            role="img"
            aria-label={`Прогресс к цели ${goalPercent}%`}
          >
            <circle className="statement-analysis__track" cx="60" cy="60" r="45" />
            <circle
              className="statement-analysis__value-arc"
              cx="60"
              cy="60"
              r="45"
              strokeDasharray={donut.dasharray}
              transform="rotate(-90 60 60)"
            />
            <text x="60" y="56" className="statement-analysis__percent" textAnchor="middle">
              {goalPercent}%
            </text>
            <text x="60" y="72" className="statement-analysis__percent-caption" textAnchor="middle">
              к цели
            </text>
          </svg>
        </div>

        <div className="statement-analysis__actions">
          <button
            type="button"
            className="statement-analysis__submit"
            disabled={isRecalculating || (!isDirty && result !== null)}
            onClick={handleRecalculate}
          >
            {isRecalculating ? "Пересчитываем..." : "Пересчитать"}
          </button>
          <button
            type="button"
            className="statement-analysis__secondary"
            onClick={handleReset}
          >
            Проанализировать другой файл
          </button>
        </div>

        {isDirty && (
          <p className="statement-analysis__dirty">
            Есть несохранённые правки — нажмите «Пересчитать».
          </p>
        )}
        {error && <p className="statement-analysis__error">{error}</p>}
      </article>

      <article className="card statement-analysis">
        <span className="card__eyebrow">Категории расходов</span>

        {groups.length === 0 ? (
          <p className="statement-analysis__hint">
            {result
              ? "Все категории исключены из расчёта."
              : "Считаем категории..."}
          </p>
        ) : (
          <ul className="statement-analysis__groups">
            {groups.map((group) => {
              const isExpanded = expandedGroups.has(group.name);
              const groupTxs = analysis.transactions.filter(
                (tx) => !tx.is_transfer && tx.group === group.name,
              );
              const allActive =
                groupTxs.length > 0 && groupTxs.every((tx) => tx.is_active);

              return (
                <li key={group.name} className="statement-analysis__group">
                  <div className="statement-analysis__group-row">
                    <label className="statement-analysis__checkbox">
                      <input
                        type="checkbox"
                        checked={allActive}
                        onChange={(event) =>
                          toggleGroup(group.name, event.target.checked)
                        }
                      />
                    </label>
                    <button
                      type="button"
                      className="statement-analysis__group-toggle"
                      onClick={() => toggleGroupExpanded(group.name)}
                    >
                      <span className="statement-analysis__group-name">
                        {group.name} — {formatStatementAmount(group.monthly_amount)}{" "}
                        <small>(среднее в месяц)</small>
                      </span>
                      <span
                        className={`statement-analysis__chevron${
                          isExpanded ? " statement-analysis__chevron--open" : ""
                        }`}
                        aria-hidden="true"
                      >
                        ▾
                      </span>
                    </button>
                  </div>

                  <div className="statement-analysis__group-meta">
                    <span>Количество операций: {group.ops_count}</span>
                    <span>Всего потрачено: {formatStatementAmount(group.total_amount)}</span>
                  </div>

                  {isExpanded && (
                    <div className="statement-analysis__operations">
                      <span className="statement-analysis__operations-title">
                        {isDirty ? "Показать операции" : "Операции"}
                      </span>
                      {groupTxs.length === 0 ? (
                        <p className="statement-analysis__hint">Операций нет.</p>
                      ) : (
                        <ul>
                          {groupTxs.map((tx) => (
                            <li
                              key={tx.tx_id}
                              className="statement-analysis__operation"
                            >
                              <label className="statement-analysis__checkbox">
                                <input
                                  type="checkbox"
                                  checked={tx.is_active}
                                  onChange={(event) =>
                                    toggleTransaction(tx.tx_id, event.target.checked)
                                  }
                                />
                              </label>
                              <span className="statement-analysis__operation-name">
                                {tx.counterparty}
                              </span>
                              <span className="statement-analysis__operation-amount">
                                {formatStatementAmount(tx.amount)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </article>

      {analysis.transfer_candidates.length > 0 && (
        <article className="card statement-analysis">
          <span className="card__eyebrow">Скрытые регулярные переводы</span>
          <p className="statement-analysis__hint">
            Обнаружены регулярные переводы, которые могут быть скрытыми
            подписками или услугами. Решите, включать ли их в подушку.
          </p>
          <ul className="statement-analysis__transfers">
            {analysis.transfer_candidates.map((candidate) => {
              const candidateTx = analysis.transactions.find(
                (tx) => tx.is_transfer && tx.counterparty === candidate.counterparty,
              );

              return (
                <li key={candidate.counterparty} className="statement-analysis__transfer">
                  <div className="statement-analysis__transfer-head">
                    <label className="statement-analysis__checkbox">
                      <input
                        type="checkbox"
                        checked={candidateTx ? candidateTx.include_in_cushion : false}
                        onChange={(event) =>
                          patchTransfers(candidate.counterparty, {
                            include_in_cushion: event.target.checked,
                          })
                        }
                      />
                      <span>
                        Перевод контрагенту «{candidate.counterparty}» на ~
                        {formatStatementAmount(candidate.amount)}, повторялся{" "}
                        {candidate.occurrences} раз(а)
                      </span>
                    </label>
                  </div>
                  <input
                    className="statement-analysis__transfer-label"
                    placeholder="Как назвать эту услугу (например, Аренда)"
                    value={candidateTx?.transfer_label ?? ""}
                    onChange={(event) =>
                      patchTransfers(candidate.counterparty, {
                        transfer_label: event.target.value || null,
                      })
                    }
                  />
                </li>
              );
            })}
          </ul>
        </article>
      )}

      {excludedGroups.length > 0 && (
        <article className="card statement-analysis">
          <span className="card__eyebrow">Не включено в подушку</span>
          <ul className="statement-analysis__groups">
            {excludedGroups.map((group) => (
              <li key={group.name} className="statement-analysis__group">
                <div className="statement-analysis__group-row">
                  <span className="statement-analysis__group-name">
                    {group.name} — {formatStatementAmount(group.monthly_amount)}{" "}
                    <small>(среднее в месяц)</small>
                  </span>
                </div>
                <div className="statement-analysis__group-meta">
                  <span>Количество операций: {group.ops_count}</span>
                  <span>Всего потрачено: {formatStatementAmount(group.total_amount)}</span>
                </div>
              </li>
            ))}
          </ul>
        </article>
      )}

      {rating.length > 0 && (
        <article className="card statement-analysis">
          <span className="card__eyebrow">Рейтинг семьи</span>
          <ul className="statement-analysis__rating">
            {rating.map((item) => (
              <li
                key={item.user_id}
                className={`statement-analysis__rating-row${
                  user?.id === item.user_id
                    ? " statement-analysis__rating-row--self"
                    : ""
                }`}
              >
                <span className="statement-analysis__rating-name">
                  {item.user_name}
                </span>
                <span className="statement-analysis__rating-value">
                  {formatStatementAmount(item.cushion_total)}
                </span>
              </li>
            ))}
          </ul>
        </article>
      )}
    </div>
  );
}

export default StatementAnalysis;
