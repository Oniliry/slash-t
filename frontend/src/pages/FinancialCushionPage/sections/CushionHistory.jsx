import { useEffect, useState } from "react";

import { getCushionState } from "../../../shared/api/cushion.ts";
import {
  formatCushionAmount,
  formatCushionDate,
} from "../lib/cushionFormat.js";
import "./CushionHistory.css";

const operationLabels = {
  topup: { icon: "↑", title: "Пополнение", sign: "+", modifier: "topup" },
  withdraw: { icon: "↓", title: "Списание", sign: "−", modifier: "withdraw" },
};

function CushionHistory() {
  const [operations, setOperations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      const response = await getCushionState();

      if (cancelled) {
        return;
      }

      if (!response.error && response.data) {
        setOperations(response.data.operations);
        setError("");
      } else {
        setError(response.message ?? "Не удалось загрузить историю операций.");
      }

      setIsLoading(false);
    }

    loadHistory();

    // Синхронизируем историю с операциями, выполненными в карточке подушки.
    window.addEventListener("slash-t:cushion-updated", loadHistory);
    return () => {
      cancelled = true;
      window.removeEventListener("slash-t:cushion-updated", loadHistory);
    };
  }, []);

  return (
    <article className="card cushion-history">
      <div className="section-heading">
        <h2>История операций</h2>
        <span className="section-heading__hint">пополнения и списания</span>
      </div>

      {isLoading && <p className="list__empty">Загружаем операции...</p>}

      {!isLoading && error && <p className="list__empty">{error}</p>}

      {!isLoading && !error && operations.length === 0 && (
        <p className="list__empty">
          Пока нет ни одной операции — пополните подушку карточкой выше.
        </p>
      )}

      {!isLoading && !error && operations.length > 0 && (
        <div className="list">
          {operations.map((operation) => {
            const meta = operationLabels[operation.kind];
            return (
              <div className="list__row" key={operation.id}>
                <span>
                  <b className={`cushion-history__title cushion-history__title--${meta.modifier}`}>
                    <span aria-hidden="true">{meta.icon}</span> {meta.title}
                    {operation.comment ? ` · ${operation.comment}` : ""}
                  </b>
                  <small>
                    {formatCushionDate(operation.created_at)}
                    {operation.user_name ? ` · ${operation.user_name}` : ""}
                  </small>
                </span>
                <strong
                  className={`cushion-history__amount cushion-history__amount--${meta.modifier}`}
                >
                  {meta.sign}
                  {formatCushionAmount(operation.amount)}
                </strong>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

export default CushionHistory;
